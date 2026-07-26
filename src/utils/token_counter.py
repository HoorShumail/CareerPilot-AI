import logging

logger = logging.getLogger("careerpilot.token_counter")


def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in a string.
    Uses tiktoken if available, otherwise falls back to character count estimation (~4 chars per token).
    """
    if not text:
        return 0

    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback heuristic: 1 token ~ 4 characters
        return max(1, len(text) // 4)
