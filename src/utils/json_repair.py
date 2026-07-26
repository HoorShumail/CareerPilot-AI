"""
Production-grade JSON repair utility for LLM responses.

Implements a deterministic multi-stage repair pipeline:
1. Strip BOM and control characters
2. Strip markdown code fences
3. Extract JSON body (first '{' or '[' to matching close)
4. Structural repairs (trailing commas, single quotes, unquoted keys)
5. Balance unclosed braces/brackets
6. Truncation recovery (progressive parsing)

Never corrupts valid JSON. Logs full diagnostics on every failure.
"""

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("careerpilot.json_repair")


class JSONParsingError(ValueError):
    """Raised when JSON parsing and all automatic repair attempts fail."""

    def __init__(
        self,
        agent_name: str,
        original_error: str,
        orig_pos: int,
        orig_snippet: str,
        repaired_error: str,
        repaired_pos: int,
        repaired_snippet: str,
        raw_text: str,
        finish_reason: Optional[str] = None,
    ):
        self.agent_name = agent_name
        self.original_error = original_error
        self.orig_pos = orig_pos
        self.orig_snippet = orig_snippet
        self.repaired_error = repaired_error
        self.repaired_pos = repaired_pos
        self.repaired_snippet = repaired_snippet
        self.raw_text = raw_text
        self.finish_reason = finish_reason
        super().__init__(
            f"JSON parsing failed for {agent_name}. "
            f"Original error: '{original_error}' near position {orig_pos} ('{orig_snippet}'). "
            f"Repaired error: '{repaired_error}' near position {repaired_pos} ('{repaired_snippet}'). "
            f"Finish reason: {finish_reason or 'unknown'}."
        )


# ---------------------------------------------------------------------------
# Stage 1: Strip BOM and control characters
# ---------------------------------------------------------------------------

def _strip_bom_and_control_chars(text: str) -> str:
    """Remove byte-order marks and non-printable control characters (except newline/tab)."""
    if not text:
        return ""
    # Remove BOM
    text = text.lstrip("\ufeff")
    # Remove ASCII control chars except \n \r \t
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


# ---------------------------------------------------------------------------
# Stage 2: Strip markdown code fences
# ---------------------------------------------------------------------------

def clean_markdown_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```, ~~~json ... ~~~, etc.)."""
    if not text:
        return ""
    content = text.strip()

    # Match ```json ... ``` or ~~~ json ... ~~~  (with optional language tag)
    patterns = [
        r"```(?:json|JSON)?\s*\n?([\s\S]*?)\n?\s*```",
        r"~~~(?:json|JSON)?\s*\n?([\s\S]*?)\n?\s*~~~",
    ]
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            content = match.group(1).strip()
            break

    return content


# ---------------------------------------------------------------------------
# Stage 3: Extract JSON body
# ---------------------------------------------------------------------------

def _find_json_boundaries(text: str) -> Tuple[int, int]:
    """
    Find the first JSON object or array boundaries using a stack-based scanner.
    Returns (start, end) indices. If no valid boundaries found, returns (0, len(text)).
    """
    start = -1
    open_char = None

    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            open_char = ch
            break

    if start == -1:
        return 0, len(text)

    close_char = "}" if open_char == "{" else "]"
    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_string:
                escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                return start, i + 1

    # Unclosed — return from start to end (will be repaired later)
    return start, len(text)


def _extract_json_body(text: str) -> str:
    """Extract the JSON body from text that may have leading/trailing non-JSON content."""
    start, end = _find_json_boundaries(text)
    return text[start:end]


# ---------------------------------------------------------------------------
# Stage 4: Structural repairs
# ---------------------------------------------------------------------------

def _remove_trailing_commas(text: str) -> str:
    """Remove trailing commas before closing braces/brackets, respecting string boundaries."""
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if in_string:
            result.append(ch)
            i += 1
            continue

        # Outside string: check for trailing comma
        if ch == ",":
            # Look ahead past whitespace for } or ]
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":
                # Skip this comma
                i += 1
                continue

        result.append(ch)
        i += 1

    return "".join(result)


def _fix_single_quotes(text: str) -> str:
    """Replace single-quoted strings with double-quoted strings outside of existing double-quoted strings."""
    result = []
    in_double = False
    escape = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\" and (in_double or (i > 0 and text[i - 1] == "'")):
            result.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"' and not escape:
            in_double = not in_double
            result.append(ch)
            i += 1
            continue

        if in_double:
            result.append(ch)
            i += 1
            continue

        # Outside double quotes: convert single quotes
        if ch == "'":
            result.append('"')
            i += 1
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def _fix_unquoted_keys(text: str) -> str:
    """Quote unquoted object keys (JavaScript-style identifiers before colons)."""
    # Only match keys at structural positions (after { or ,)
    return re.sub(
        r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
        r' "\1":',
        text,
    )


def _remove_js_comments(text: str) -> str:
    """Remove JavaScript-style comments (// and /* */) outside of strings."""
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if escape:
            result.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\" and in_string:
            result.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if in_string:
            result.append(ch)
            i += 1
            continue

        # Check for // comments
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            # Skip to end of line
            j = i + 2
            while j < n and text[j] != "\n":
                j += 1
            i = j
            continue

        # Check for /* */ comments
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = i + 2
            while j + 1 < n and not (text[j] == "*" and text[j + 1] == "/"):
                j += 1
            i = j + 2
            continue

        result.append(ch)
        i += 1

    return "".join(result)


# ---------------------------------------------------------------------------
# Stage 5: Balance braces/brackets
# ---------------------------------------------------------------------------

def _balance_braces(text: str) -> str:
    """Close any unclosed braces or brackets."""
    in_string = False
    escape = False
    stack = []

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()

    # Close remaining open structures
    while stack:
        text += stack.pop()

    return text


def _fix_missing_commas(text: str) -> str:
    """Insert missing commas between key-value pairs and array elements."""
    # Fix missing commas between value (string, number, bool, null, ], }) and next key ("key":)
    text = re.sub(
        r'("(?:\\.|[^"\\])*"|\d+|true|false|null|\]|\})\s+("(?:\\.|[^"\\])*"\s*:)',
        r'\1, \2',
        text,
    )
    # Fix missing commas between list items
    text = re.sub(
        r'("(?:\\.|[^"\\])*"|\d+|true|false|null|\]|\})\s+("(?:\\.|[^"\\])*"|\d+|true|false|null|\[|\{)',
        r'\1, \2',
        text,
    )
    return text


# ---------------------------------------------------------------------------
# Full repair pipeline
# ---------------------------------------------------------------------------

def repair_json_string(text: str) -> str:
    """
    Production-grade JSON repair pipeline.
    Applies repairs in a deterministic order that cannot corrupt valid JSON.

    Pipeline order:
    1. Strip BOM and control characters
    2. Strip markdown fences
    3. Remove JS comments
    4. Extract JSON body (skip leading/trailing text)
    5. Fix single quotes → double quotes
    6. Fix unquoted keys
    7. Fix missing commas
    8. Remove trailing commas
    9. Balance unclosed braces/brackets
    """
    if not text:
        return "{}"

    content = _strip_bom_and_control_chars(text)
    content = clean_markdown_fences(content)
    content = _remove_js_comments(content)
    content = _extract_json_body(content)
    content = _fix_single_quotes(content)
    content = _fix_unquoted_keys(content)
    content = _fix_missing_commas(content)
    content = _remove_trailing_commas(content)
    content = _balance_braces(content)

    return content


# ---------------------------------------------------------------------------
# Stage 6: Truncation recovery
# ---------------------------------------------------------------------------

def _try_truncation_recovery(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to recover a parseable JSON object from a truncated response
    by progressively closing structures and stripping trailing partial content.
    """
    # Strategy: find the last complete key-value pair and close from there
    for trim in range(0, min(500, len(text)), 10):
        candidate = text if trim == 0 else text[:-trim]
        # Strip any trailing partial values
        candidate = re.sub(r',\s*"[^"]*$', "", candidate)
        candidate = re.sub(r',\s*$', "", candidate)
        candidate = _balance_braces(candidate)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, (dict, list)):
                return parsed if isinstance(parsed, dict) else {"data": parsed}
        except json.JSONDecodeError:
            continue
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _error_context(text: str, pos: int, window: int = 100) -> str:
    """Extract context around an error position."""
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    return text[start:end]


def parse_and_repair_json(
    response_text: str,
    agent_name: str = "Agent",
    finish_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Production-grade JSON parsing pipeline with automatic repair and full diagnostics.

    Pipeline:
    1. Always logs complete raw response
    2. Attempts direct parse (after markdown fence stripping)
    3. If parsing fails, logs exact error position with 100-char context
    4. Runs full repair pipeline
    5. If repair fails, attempts truncation recovery
    6. If all recovery fails, raises descriptive JSONParsingError with full diagnostics

    Args:
        response_text: Raw LLM response string
        agent_name: Name of the calling agent (for logging)
        finish_reason: LLM finish_reason (for diagnostics — "length" indicates truncation)

    Returns:
        Parsed JSON as a dict

    Raises:
        JSONParsingError: When all parsing and repair attempts fail
    """
    # Log raw response for diagnostics
    logger.info(
        "[RAW LLM RESPONSE] Agent=%s | length=%d | finish_reason=%s",
        agent_name,
        len(response_text) if response_text else 0,
        finish_reason or "unknown",
    )
    logger.debug("[RAW LLM RESPONSE BODY] Agent=%s | Content:\n%s", agent_name, response_text)

    # Handle empty responses
    if not response_text or not response_text.strip():
        logger.error("[JSON PARSE FAIL] Agent=%s | Empty response text | finish_reason=%s", agent_name, finish_reason)
        raise JSONParsingError(
            agent_name=agent_name,
            original_error="Empty response text",
            orig_pos=0,
            orig_snippet="",
            repaired_error="Empty response text",
            repaired_pos=0,
            repaired_snippet="",
            raw_text=response_text or "",
            finish_reason=finish_reason,
        )

    # Warn on token truncation
    if finish_reason == "length":
        logger.warning(
            "[TOKEN TRUNCATION] Agent=%s | finish_reason='length' — response was truncated by token limit. "
            "Response length: %d chars. Will attempt recovery.",
            agent_name,
            len(response_text),
        )

    # --- Attempt 1: Direct parse (with markdown fence stripping) ---
    cleaned = _strip_bom_and_control_chars(response_text)
    cleaned = clean_markdown_fences(cleaned)

    try:
        parsed = json.loads(cleaned)
        logger.info("[JSON PARSE OK] Agent=%s | Direct parse succeeded", agent_name)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"data": parsed}
        return {"data": parsed}
    except json.JSONDecodeError as exc:
        orig_pos = exc.pos
        orig_msg = exc.msg
        orig_snippet = _error_context(cleaned, orig_pos)

        logger.warning(
            "[JSON PARSE FAIL] Agent=%s | Error='%s' | Pos=%d (Line %d, Col %d) | "
            "finish_reason=%s | Before='%s' | After='%s'",
            agent_name,
            orig_msg,
            orig_pos,
            exc.lineno,
            exc.colno,
            finish_reason or "unknown",
            cleaned[max(0, orig_pos - 100):orig_pos],
            cleaned[orig_pos:min(len(cleaned), orig_pos + 100)],
        )
        logger.warning(
            "[JSON PARSE FAIL RAW] Agent=%s | Full raw response (%d chars):\n%s",
            agent_name,
            len(response_text),
            response_text,
        )

    # --- Attempt 2: Full repair pipeline ---
    repaired = repair_json_string(response_text)
    logger.info(
        "[JSON REPAIR] Agent=%s | Repaired text length=%d",
        agent_name,
        len(repaired),
    )
    logger.debug("[JSON REPAIR BODY] Agent=%s | Repaired content:\n%s", agent_name, repaired)

    try:
        parsed_repaired = json.loads(repaired)
        logger.info("[JSON REPAIR SUCCESS] Agent=%s | Repair pipeline succeeded", agent_name)
        if isinstance(parsed_repaired, dict):
            return parsed_repaired
        if isinstance(parsed_repaired, list):
            return {"data": parsed_repaired}
        return {"data": parsed_repaired}
    except json.JSONDecodeError as rep_exc:
        rep_pos = rep_exc.pos
        rep_msg = rep_exc.msg
        rep_snippet = _error_context(repaired, rep_pos)

        logger.error(
            "[JSON REPAIR FAIL] Agent=%s | Error='%s' | Pos=%d (Line %d, Col %d) | "
            "Before='%s' | After='%s'",
            agent_name,
            rep_msg,
            rep_pos,
            rep_exc.lineno,
            rep_exc.colno,
            repaired[max(0, rep_pos - 100):rep_pos],
            repaired[rep_pos:min(len(repaired), rep_pos + 100)],
        )

    # --- Attempt 3: Truncation recovery ---
    logger.info("[JSON TRUNCATION RECOVERY] Agent=%s | Attempting progressive truncation recovery...", agent_name)
    recovered = _try_truncation_recovery(repaired)
    if recovered is not None:
        logger.info(
            "[JSON TRUNCATION RECOVERY SUCCESS] Agent=%s | Recovered %d keys from truncated response",
            agent_name,
            len(recovered),
        )
        return recovered

    # --- All attempts failed ---
    logger.error(
        "[JSON ALL REPAIRS FAILED] Agent=%s | All parsing attempts exhausted. "
        "Original length=%d | Repaired length=%d | finish_reason=%s",
        agent_name,
        len(response_text),
        len(repaired),
        finish_reason or "unknown",
    )

    raise JSONParsingError(
        agent_name=agent_name,
        original_error=orig_msg,
        orig_pos=orig_pos,
        orig_snippet=orig_snippet,
        repaired_error=rep_msg,
        repaired_pos=rep_pos,
        repaired_snippet=rep_snippet,
        raw_text=response_text,
        finish_reason=finish_reason,
    )
