import os
import streamlit as st
import streamlit.components.v1 as components
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Setup / global injection
# ---------------------------------------------------------------------------


def inject_custom_css():
    """Inject the central SaaS design system CSS into Streamlit."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "styles", "custom.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def inject_password_manager_fix():
    """
    CRITICAL FIX: Fix Chrome Google Password Manager autocomplete popups.
    Ensures 'current-password' / 'username' on Login, and 'new-password' on Register.
    Executes via iframe JS targeting the parent document with MutationObserver.
    """
    js_code = """
    <script>
    function applyAutocompleteFix() {
        try {
            const parentDoc = window.parent.document;
            if (!parentDoc) return;

            // Target all form fields in Streamlit
            const forms = parentDoc.querySelectorAll('form[data-testid="stForm"]');
            forms.forEach(form => {
                const textContent = (form.innerText || '').toLowerCase();
                const inputs = form.querySelectorAll('input');

                if (textContent.includes('log in') || textContent.includes('login')) {
                    inputs.forEach(input => {
                        if (input.type === 'password') {
                            input.setAttribute('autocomplete', 'current-password');
                        } else if (input.type === 'text' || input.type === 'email') {
                            input.setAttribute('autocomplete', 'username');
                        }
                    });
                } else if (textContent.includes('register') || textContent.includes('sign up')) {
                    inputs.forEach(input => {
                        if (input.type === 'password') {
                            input.setAttribute('autocomplete', 'new-password');
                        }
                    });
                }
            });

            // Also check all inputs outside explicit forms if any
            const allInputs = parentDoc.querySelectorAll('input');
            allInputs.forEach(input => {
                const ariaLabel = (input.getAttribute('aria-label') || '').toLowerCase();
                if (ariaLabel.includes('password')) {
                    const formText = input.closest('form') ? (input.closest('form').innerText || '').toLowerCase() : '';
                    if (formText.includes('register') || formText.includes('new password')) {
                        input.setAttribute('autocomplete', 'new-password');
                    } else if (formText.includes('log in') || formText.includes('current password')) {
                        input.setAttribute('autocomplete', 'current-password');
                    }
                }
            });
        } catch (e) {
            console.error('Autocomplete fix error:', e);
        }
    }

    // Initial run
    applyAutocompleteFix();

    // Attach MutationObserver for Streamlit re-render cycles
    try {
        const observer = new MutationObserver(applyAutocompleteFix);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
    } catch(e) {}
    </script>
    """
    components.html(js_code, height=0, width=0)


# ---------------------------------------------------------------------------
# Low-level formatting helpers
# ---------------------------------------------------------------------------


def humanize(key: str) -> str:
    """Turn a snake_case / kebab-case API key into a readable label."""
    return str(key).replace("_", " ").replace("-", " ").strip().title()


def _is_percentish(value: Any) -> bool:
    """True for floats that look like a 0-1 proportion (e.g. confidence, match scores)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False
    return 0.0 <= f <= 1.0 and isinstance(value, float)


def format_value(key: str, value: Any) -> str:
    """Format a scalar for key-value display — percentages, currency-ish, plain text."""
    key_lower = str(key).lower()

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if _is_percentish(value) and any(hint in key_lower for hint in (
        "confidence", "score", "match", "probability", "readiness", "progress", "percent", "maturity"
    )):
        return f"{float(value) * 100:.0f}%"

    if isinstance(value, (int, float)) and any(hint in key_lower for hint in ("salary", "price", "cost", "budget")):
        try:
            return f"${float(value):,.0f}"
        except (TypeError, ValueError):
            pass

    return str(value)


def progress_fraction(level: Any) -> Optional[float]:
    """Normalize a 0-1 or 0-100 score into a 0-1 float. None if not numeric."""
    try:
        level = float(level)
    except (TypeError, ValueError):
        return None
    return min(max(level / 100 if level > 1 else level, 0.0), 1.0)


_PRIORITY_TONE = {
    "critical": "cp-badge-missing",
    "high": "cp-badge-missing",
    "urgent": "cp-badge-missing",
    "medium": "cp-badge-warning",
    "moderate": "cp-badge-warning",
    "low": "cp-badge-matched",
    "minor": "cp-badge-matched",
}


def _priority_badge_html(label: str) -> str:
    tone = _PRIORITY_TONE.get(str(label).strip().lower(), "cp-badge-indigo")
    return f'<span class="cp-badge {tone}">{label}</span>'


# ---------------------------------------------------------------------------
# Headers / empty states
# ---------------------------------------------------------------------------


def render_page_header(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
    """Render a clean, modern page header."""
    inject_custom_css()
    header_text = f"{icon} {title}" if icon else title
    st.markdown(f"<h1 style='margin-bottom: 0.2rem;'>{header_text}</h1>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='color: #64748B; font-size: 1rem; margin-bottom: 1.5rem;'>{subtitle}</p>", unsafe_allow_html=True)
    else:
        st.write("")


def render_empty_state(title: str, description: str, icon: str = "📭", cta_label: Optional[str] = None, cta_key: Optional[str] = None) -> bool:
    """Render a clean, modern empty state box with optional CTA button."""
    st.markdown(
        f"""
        <div class="cp-empty-state">
            <div class="cp-empty-icon">{icon}</div>
            <div class="cp-empty-title">{title}</div>
            <div class="cp-empty-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_label and cta_key:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            return st.button(cta_label, key=cta_key, use_container_width=True)
    return False


# ---------------------------------------------------------------------------
# Chips / badges
# ---------------------------------------------------------------------------


def render_skill_chips(skills: List[str], category: str = "default"):
    """Render a list of skills as visual badges/chips instead of raw lists or JSON."""
    if not skills:
        st.write("—")
        return

    badge_class = "cp-badge-indigo"
    if category == "matched" or category == "success":
        badge_class = "cp-badge-matched"
    elif category == "missing" or category == "error":
        badge_class = "cp-badge-missing"
    elif category == "warning" or category == "medium":
        badge_class = "cp-badge-warning"
    elif category == "slate":
        badge_class = "cp-badge-slate"

    html = "".join([f'<span class="cp-badge {badge_class}">{skill}</span>' for skill in skills if skill])
    st.markdown(f'<div style="margin-bottom: 0.5rem;">{html}</div>', unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Returns HTML for a colored status badge."""
    status_lower = status.lower()
    badge_class = "cp-badge-slate"
    if status_lower in ("applied", "in_progress", "active"):
        badge_class = "cp-badge-info"
    elif status_lower in ("interview", "screening", "matched"):
        badge_class = "cp-badge-warning"
    elif status_lower in ("offer", "completed", "accepted"):
        badge_class = "cp-badge-matched"
    elif status_lower in ("rejected", "failed", "declined"):
        badge_class = "cp-badge-missing"

    return f'<span class="cp-badge {badge_class}">{status.title()}</span>'


# ---------------------------------------------------------------------------
# Progress / metrics
# ---------------------------------------------------------------------------


def render_progress_bar(value: Any, label: Optional[str] = None):
    """
    Renders a labeled progress bar for a 0-1 or 0-100 score.
    Instead of `progress: 0.72` shows a bar with a "72%" caption.
    """
    frac = progress_fraction(value)
    if frac is None:
        if label:
            st.markdown(f"**{label}:** {value}")
        else:
            st.write(value)
        return

    if label:
        st.markdown(f"**{label}** — {frac * 100:.0f}%")
    st.progress(frac)


def render_metric_card(label: str, value: Any, delta: Optional[Any] = None, help_text: Optional[str] = None):
    """Thin wrapper around st.metric with consistent formatting for %/currency-like values."""
    display_value = format_value(label, value) if not isinstance(value, str) else value
    st.metric(label, display_value, delta=delta, help=help_text)


def render_metric_row(metrics: List[Dict[str, Any]]):
    """
    Renders a row of metric cards from a list like:
    [{"label": "Confidence", "value": 0.89}, {"label": "Readiness", "value": 0.7}]
    """
    metrics = [m for m in metrics if m.get("value") not in (None, "")]
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            render_metric_card(m.get("label", ""), m.get("value"), delta=m.get("delta"), help_text=m.get("help"))


# ---------------------------------------------------------------------------
# Section / expander helpers
# ---------------------------------------------------------------------------


def render_expandable_section(title: str, render_fn, icon: str = "", expanded: bool = False, key: Optional[str] = None):
    """
    Wraps `with st.expander(...): render_fn()` so pages don't repeat the same
    boilerplate. render_fn is a zero-arg callable that draws the section body.
    """
    label = f"{icon} {title}".strip() if icon else title
    with st.expander(label, expanded=expanded):
        render_fn()


def render_section(data: Any, title: Optional[str] = None):
    """
    Top-level dispatcher for an arbitrary API payload — picks the best
    presentation (metric row, card list, smart card, key-value grid) instead
    of ever falling back to raw JSON.
    """
    if title:
        st.markdown(f"### {title}")

    if data in (None, "", [], {}):
        st.write("—")
        return

    if isinstance(data, str):
        st.write(data)
        return

    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            render_ai_list(data)
        elif data and all(isinstance(x, str) for x in data):
            render_skill_chips(data)
        else:
            for item in data:
                st.markdown(f"• {item}")
        return

    if isinstance(data, dict):
        render_formatted_dict(data)
        return

    st.write(data)


# ---------------------------------------------------------------------------
# Smart card rendering (the core upgrade)
# ---------------------------------------------------------------------------

_TITLE_KEYS = ("title", "name", "topic", "role", "position", "skill", "goal")
_SUBTITLE_KEYS = ("company", "institution", "provider", "issuer", "category")
_REASON_KEYS = ("reason", "description", "summary", "explanation", "note", "notes")
_PRIORITY_KEYS = ("priority", "severity")
_META_KEYS = ("timeframe", "duration", "estimated_time", "duration_weeks", "date_range", "dates", "period")
_OUTCOME_KEYS = ("expected_outcomes", "outcomes", "bullets", "highlights", "responsibilities", "resources", "skills_gained")

_CARD_ICONS = {
    "course": "📘", "certification": "📜", "project": "🔨", "skill": "🛠️",
    "book": "📚", "job": "💼", "milestone": "🏁", "goal": "🎯",
}


def _pick_card_icon(item: Dict[str, Any], default: str = "📘") -> str:
    text_blob = " ".join(str(v).lower() for v in item.values() if isinstance(v, str))
    for hint, icon in _CARD_ICONS.items():
        if hint in text_blob:
            return icon
    return default


def is_card_like(data: Any) -> bool:
    """True if a dict looks like a single structured entity (has a title-ish field)."""
    if not isinstance(data, dict):
        return False
    return any(k in data for k in _TITLE_KEYS)


def render_smart_card(item: Dict[str, Any], icon: Optional[str] = None) -> None:
    """
    Detects the common card shape:
      {title, reason/description, priority/severity, timeframe/duration, expected_outcomes}
    and renders it as a clean bordered card instead of a raw dict dump.
    """
    if not isinstance(item, dict):
        st.write(item)
        return

    with st.container(border=True):
        title = next((item.get(k) for k in _TITLE_KEYS if item.get(k)), None)
        subtitle = next((item.get(k) for k in _SUBTITLE_KEYS if item.get(k)), None)
        card_icon = icon or _pick_card_icon(item)

        if title:
            st.markdown(f"**{card_icon} {title}**")
        if subtitle:
            st.caption(subtitle)

        # Priority / severity + timeframe / duration as a compact badge line
        badge_bits = []
        for k in _PRIORITY_KEYS:
            if item.get(k):
                badge_bits.append(f"{humanize(k)}: " + _priority_badge_html(item[k]))
        meta_bits = []
        for k in _META_KEYS:
            if item.get(k):
                meta_bits.append(f"{humanize(k)}: {item[k]}")

        if badge_bits:
            st.markdown(" &nbsp;&nbsp; ".join(badge_bits), unsafe_allow_html=True)
        if meta_bits:
            st.caption(" · ".join(meta_bits))

        reason = next((item.get(k) for k in _REASON_KEYS if item.get(k)), None)
        if reason:
            st.write(reason)

        outcomes = next((item.get(k) for k in _OUTCOME_KEYS if item.get(k)), None)
        if outcomes:
            st.markdown("**Expected Outcome**" if "outcome" in str(outcomes) or True else "")
            if isinstance(outcomes, list):
                for o in outcomes:
                    st.markdown(f"- {o}")
            else:
                st.write(outcomes)

        # Score-like fields (confidence, score, progress) as a mini progress bar
        for k, v in item.items():
            if any(hint in k.lower() for hint in ("score", "confidence", "progress", "readiness")) and isinstance(v, (int, float)):
                render_progress_bar(v, label=humanize(k))

        handled = set(_TITLE_KEYS) | set(_SUBTITLE_KEYS) | set(_REASON_KEYS) | set(_PRIORITY_KEYS) | set(_META_KEYS) | set(_OUTCOME_KEYS)
        handled |= {k for k, v in item.items() if any(h in k.lower() for h in ("score", "confidence", "progress", "readiness")) and isinstance(v, (int, float))}
        leftovers = {k: v for k, v in item.items() if k not in handled and v not in (None, "", [], {})}
        for k, v in leftovers.items():
            if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                st.markdown(f"**{humanize(k)}**")
                render_skill_chips(v)
            elif isinstance(v, (list, dict)):
                st.markdown(f"**{humanize(k)}**")
                render_formatted_dict(v)
            else:
                st.markdown(f"**{humanize(k)}:** {format_value(k, v)}")


def render_ai_list(items: List[Dict[str, Any]]) -> None:
    """
    Renders a list of AI-returned objects (recommendations, roadmap steps,
    courses, projects, ...) as stacked smart cards. No calling page needs to
    know the shape — it just hands over the raw list.
    """
    if not items:
        st.write("—")
        return
    for item in items:
        if isinstance(item, dict):
            render_smart_card(item)
        else:
            st.markdown(f"• {item}")


def render_info_card(title: str, body: str = "", icon: str = "ℹ️", tone: str = "default") -> None:
    """Simple bordered callout card for a single piece of prose/info."""
    tone_fn = {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}.get(tone)
    with st.container(border=True):
        st.markdown(f"**{icon} {title}**")
        if body:
            if tone_fn:
                tone_fn(body)
            else:
                st.write(body)


def render_recommendation_card(rec: Dict[str, Any]) -> None:
    """
    Specialized card for recommendation-shaped payloads:
      {title/name, reason, priority, estimated_time}
    Falls back to render_smart_card for anything else.
    """
    render_smart_card(rec, icon="💡")


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


def render_timeline_card(entry: Dict[str, Any], index: int = 0) -> None:
    """A single timeline/snapshot entry — label, date, score deltas, additions."""
    if not isinstance(entry, dict):
        st.write(entry)
        return

    label = entry.get("snapshot_label") or entry.get("title") or entry.get("label") or f"Snapshot #{index + 1}"
    created = entry.get("created_at") or entry.get("date")

    with st.container(border=True):
        header = f"**📌 {label}**"
        if created:
            header += f"  ·  {created}"
        st.markdown(header)

        payload = entry.get("snapshot_payload") or entry

        changes = payload.get("changes") or payload.get("score_changes")
        if changes:
            for key, val in changes.items():
                if isinstance(val, (list, tuple)) and len(val) == 2:
                    before, after = val
                    st.write(f"**{humanize(key)}:** {before} → {after}")
                elif isinstance(val, dict) and "before" in val and "after" in val:
                    st.write(f"**{humanize(key)}:** {val['before']} → {val['after']}")
                else:
                    st.write(f"**{humanize(key)}:** {val}")

        added = payload.get("added_skills") or payload.get("added")
        if added:
            st.markdown("**Added**")
            render_skill_chips(added) if all(isinstance(a, str) for a in added) else render_formatted_dict(added)

        if not changes and not added and payload not in (None, {}, entry):
            render_formatted_dict(payload)


def render_timeline(entries: List[Dict[str, Any]]) -> None:
    """Renders a full list of timeline/snapshot entries in order."""
    if not entries:
        st.write("—")
        return
    for i, entry in enumerate(entries):
        render_timeline_card(entry, i)


# ---------------------------------------------------------------------------
# Generic dict/list fallback (now card-aware)
# ---------------------------------------------------------------------------


def render_formatted_dict(data: Any, title: Optional[str] = None):
    """
    Recursively renders JSON/dict structures into clean, modern cards and
    key-value grids INSTEAD of raw st.json() output.

    Upgraded to detect common "card" shapes (title + reason/priority/duration/
    expected_outcomes) and render them as smart cards, and to detect lists of
    such objects and render them as stacked cards via render_ai_list.
    """
    if title:
        st.markdown(f"### {title}")

    if data is None:
        st.write("—")
        return

    if isinstance(data, list):
        if not data:
            st.write("—")
            return
        if all(isinstance(x, dict) for x in data):
            render_ai_list(data)
            return
        if all(isinstance(x, str) for x in data):
            render_skill_chips(data)
            return
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                with st.expander(f"Item #{idx + 1}", expanded=(idx == 0)):
                    render_formatted_dict(item)
            else:
                st.markdown(f"• {item}")
        return

    if isinstance(data, dict):
        if not data:
            st.write("—")
            return

        # Whole dict looks like a single card (title + supporting fields)
        if is_card_like(data):
            render_smart_card(data)
            return

        for k, v in data.items():
            key_label = humanize(k)
            if isinstance(v, list):
                if v and all(isinstance(x, str) for x in v):
                    st.markdown(f"**{key_label}**")
                    render_skill_chips(v, category="default")
                elif v and all(isinstance(x, dict) for x in v):
                    with st.expander(key_label, expanded=True):
                        render_ai_list(v)
                else:
                    with st.expander(key_label, expanded=True):
                        render_formatted_dict(v)
            elif isinstance(v, dict):
                if is_card_like(v):
                    st.markdown(f"**{key_label}**")
                    render_smart_card(v)
                else:
                    with st.expander(key_label, expanded=True):
                        render_formatted_dict(v)
            elif any(hint in k.lower() for hint in ("score", "confidence", "progress", "readiness", "maturity")) and isinstance(v, (int, float)):
                render_progress_bar(v, label=key_label)
            elif k.lower() in ("priority", "severity") and v:
                st.markdown(f"**{key_label}:** " + _priority_badge_html(v), unsafe_allow_html=True)
            elif k.lower() == "status" and v:
                st.markdown(f"**{key_label}:** " + render_status_badge(str(v)), unsafe_allow_html=True)
            else:
                st.markdown(
                    f"""
                    <div class="cp-kv-row">
                        <span class="cp-kv-label">{key_label}</span>
                        <span class="cp-kv-value">{format_value(k, v) if v is not None else '—'}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.write(str(data))