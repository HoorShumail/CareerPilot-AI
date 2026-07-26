"""
web/components/renderers.py

Reusable Streamlit rendering helpers for CareerPilot AI.

Every page (Career Twin, Career Coach, Career Strategy, Match Intelligence,
Resume Intelligence, Job Intelligence, ...) should import from here instead
of calling st.json() or re-implementing its own display logic. This keeps
the UI consistent and means a styling change only has to happen in one place.

None of these functions use st.json() — API responses are always rendered
as cards, badges, progress bars, metrics, or formatted text.
"""

from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def humanize(key: str) -> str:
    """Turn a snake_case / kebab-case API key into a readable label."""
    return str(key).replace("_", " ").replace("-", " ").strip().title()


def format_money(value) -> str:
    """Best-effort currency formatting — falls back to the raw value if not numeric."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"${num:,.0f}"


def progress_value(level) -> Optional[float]:
    """Normalize a 0-1 or 0-100 score into a 0-1 float for st.progress. None if not numeric."""
    try:
        level = float(level)
    except (TypeError, ValueError):
        return None
    return min(max(level / 100 if level > 1 else level, 0.0), 1.0)


def skill_label(skill) -> str:
    if isinstance(skill, dict):
        return skill.get("name") or skill.get("skill") or str(skill)
    return str(skill)


def skill_tier(pv: float) -> str:
    """Maps a 0-1 proficiency value to a readable tier label."""
    if pv >= 0.8:
        return "Expert"
    if pv >= 0.6:
        return "Advanced"
    if pv >= 0.35:
        return "Intermediate"
    return "Beginner"


def render_empty_state(title: str, message: str, icon: str = "📭") -> None:
    """Centered empty-state placeholder — used instead of a bare st.info() when a section has no data yet."""
    st.markdown(
        "<div style='text-align:center;padding:48px 16px;color:#374151;'>"
        f"<div style='font-size:44px;line-height:1;'>{icon}</div>"
        f"<div style='font-size:18px;font-weight:600;margin-top:12px;'>{title}</div>"
        f"<div style='color:#6b7280;margin-top:4px;'>{message}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Generic fallbacks (used when we don't have a more specific renderer)
# ---------------------------------------------------------------------------


def render_generic(value) -> None:
    """Fallback renderer for arbitrary dict/list/scalar structures. Never uses st.json()."""
    if value is None or value == "" or value == [] or value == {}:
        return
    if isinstance(value, (str, int, float)):
        st.write(value)
    elif isinstance(value, list):
        if value and isinstance(value[0], dict):
            for item in value:
                render_card(item)
        else:
            for item in value:
                st.markdown(f"- {item}")
    elif isinstance(value, dict):
        for k, v in value.items():
            if v in (None, "", [], {}):
                continue
            if isinstance(v, (list, dict)):
                st.markdown(f"**{humanize(k)}**")
                render_generic(v)
            else:
                st.markdown(f"**{humanize(k)}:** {v}")
    else:
        st.write(value)


def render_card(item) -> None:
    """Bordered card for a single entry — experience, roadmap steps, courses, etc."""
    if not isinstance(item, dict):
        render_generic(item)
        return

    with st.container(border=True):
        title = item.get("title") or item.get("role") or item.get("name") or item.get("position")
        subtitle = item.get("company") or item.get("institution") or item.get("provider") or item.get("issuer")
        date_range = item.get("date_range") or item.get("duration") or item.get("dates") or item.get("period")

        if title:
            st.markdown(f"**{title}**")
        meta_bits = [str(b) for b in [subtitle, date_range] if b]
        if meta_bits:
            st.caption(" · ".join(meta_bits))

        description = item.get("description") or item.get("summary") or item.get("reason")
        if description:
            st.write(description)

        bullets = item.get("bullets") or item.get("highlights") or item.get("responsibilities") or item.get("resources")
        if bullets:
            for b in bullets:
                st.markdown(f"- {b}")

        # Priority / estimated time badges, common on recommendation & roadmap cards
        footer_bits = []
        if item.get("priority"):
            footer_bits.append(f"Priority: {item['priority']}")
        if item.get("estimated_time"):
            footer_bits.append(f"Est. time: {item['estimated_time']}")
        if footer_bits:
            st.caption(" · ".join(footer_bits))

        handled = {
            "title", "role", "name", "position", "company", "institution", "provider", "issuer",
            "date_range", "duration", "dates", "period", "bullets", "highlights",
            "responsibilities", "resources", "description", "summary", "reason",
            "priority", "estimated_time",
        }
        leftovers = {k: v for k, v in item.items() if k not in handled and v not in (None, "", [], {})}
        for k, v in leftovers.items():
            if isinstance(v, (list, dict)):
                st.markdown(f"**{humanize(k)}**")
                render_generic(v)
            else:
                st.markdown(f"**{humanize(k)}:** {v}")


def render_section(data) -> None:
    """Top-level dispatcher: picks a sensible layout for whatever shape came back."""
    if data in (None, "", [], {}):
        st.write("No data available.")
        return
    if isinstance(data, str):
        st.write(data)
    elif isinstance(data, list):
        if data and isinstance(data[0], dict):
            for item in data:
                render_card(item)
        else:
            render_skills(data)
    elif isinstance(data, dict):
        render_generic(data)
    else:
        st.write(data)


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


def render_skills(skills) -> None:
    """Skill pills, or progress bars + tier labels when proficiency scores are present."""
    if isinstance(skills, dict):
        for name, level in skills.items():
            pv = progress_value(level)
            if pv is not None:
                col_name, col_tier = st.columns([3, 1])
                with col_name:
                    st.markdown(f"**{name}**")
                with col_tier:
                    st.caption(skill_tier(pv))
                st.progress(pv)
            else:
                st.markdown(f"🟢 {name} — {level}")
        return

    if isinstance(skills, list):
        if skills and isinstance(skills[0], dict):
            for s in skills:
                name = s.get("name") or s.get("skill")
                pv = progress_value(s.get("level") or s.get("proficiency") or s.get("score"))
                if name and pv is not None:
                    col_name, col_tier = st.columns([3, 1])
                    with col_name:
                        st.markdown(f"**{name}**")
                    with col_tier:
                        st.caption(skill_tier(pv))
                    st.progress(pv)
                elif name:
                    st.markdown(f"🟢 {name}")
                else:
                    render_card(s)
            return

        # Plain list of skill names -> pill badges in a grid
        render_pills(skills)
        return

    render_generic(skills)


def render_pills(items) -> None:
    """Plain list of short strings/tags (keywords, cert names, etc.) as pill badges in a grid."""
    if not items:
        return
    cols = st.columns(4)
    for i, item in enumerate(items):
        with cols[i % 4]:
            st.markdown(
                "<div style='background:#eef2ff;color:#3730a3;padding:6px 12px;"
                "border-radius:16px;text-align:center;margin-bottom:8px;font-size:14px;'>"
                f"{item}</div>",
                unsafe_allow_html=True,
            )


def render_bullet_list(items) -> None:
    """
    Renders longer sentence-like items (red flags, hidden requirements, interview
    questions, resume suggestions) as plain bullets/cards instead of pills — pills
    only look right for short tags, not full sentences.
    """
    if isinstance(items, dict):
        for k, v in items.items():
            if v in (None, "", [], {}):
                continue
            st.markdown(f"**{humanize(k)}**")
            render_bullet_list(v) if isinstance(v, list) else render_generic(v)
        return
    if not isinstance(items, list):
        render_generic(items)
        return
    for item in items:
        if isinstance(item, dict):
            render_card(item)
        else:
            st.write(f"• {item}")


def render_skill_section(skills) -> None:
    """
    Handles three shapes:
      1. Gap-analysis dicts: {"learning_skills": [...], "missing_skills": [...]}
         (also accepts strongest_skills / weakest_skills as aliases)
      2. Wrapped skill lists: {"skills": [...]} — e.g. render_skill_section({"skills": strengths})
      3. Plain skill lists/dicts, passed straight through to render_skills()
    """
    if isinstance(skills, dict) and any(
        k in skills for k in ("learning_skills", "missing_skills", "strongest_skills", "weakest_skills")
    ):
        learning = skills.get("learning_skills") or skills.get("strongest_skills")
        missing = skills.get("missing_skills") or skills.get("weakest_skills")

        if learning:
            st.markdown("**Learning Skills**")
            for s in learning:
                st.success(skill_label(s))
        if missing:
            st.markdown("**Missing Skills**")
            for s in missing:
                st.warning(skill_label(s))

        handled = {"learning_skills", "missing_skills", "strongest_skills", "weakest_skills"}
        leftovers = {k: v for k, v in skills.items() if k not in handled and v not in (None, "", [], {})}
        for k, v in leftovers.items():
            st.markdown(f"**{humanize(k)}**")
            render_generic(v)
        return

    if isinstance(skills, dict) and "skills" in skills and isinstance(skills["skills"], list):
        render_skills(skills["skills"])
        return

    render_skills(skills)


_BADGE_ICONS = {"green": "🟢", "orange": "⚠️", "red": "❌", "check": "✅", "blue": "🔵", "purple": "🟣"}


def render_ai_badge(label: str = "AI-Generated Analysis") -> None:
    """Small purple pill marking a section as AI-generated (per the purple = AI Analysis convention)."""
    st.markdown(
        "<div style='display:inline-block;background:#f3e8ff;color:#6b21a8;"
        "padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;"
        f"margin-bottom:6px;'>🟣 {label}</div>",
        unsafe_allow_html=True,
    )


def _badge_note(tone: str, text: str) -> None:
    if tone == "orange":
        st.info(text, icon="⚠️")
    elif tone == "red":
        st.error(text, icon="❌")
    elif tone == "purple":
        st.markdown(f"<span style='color:#6b21a8;'>{text}</span>", unsafe_allow_html=True)
    else:
        st.caption(text)


def render_badge_list(items, tone: str = "green") -> None:
    """
    Strength/weakness/match-skill style list rendered as colored badge lines.
    tone: "green" (strengths), "check" (matched skills, ✅), "orange" (weaknesses,
    needs attention), "red" (missing/red flags, ❌).
    """
    icon = _BADGE_ICONS.get(tone, "🟢")

    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                name = item.get("name") or item.get("skill") or item.get("title")
                note = item.get("recommendation") or item.get("note") or item.get("reason")
                priority = item.get("priority")
                label = f"{icon} **{name}**" + (f"  ·  {priority} priority" if priority else "")
                st.markdown(label)
                if note:
                    _badge_note(tone, note)
            else:
                st.markdown(f"{icon} {item}")
    elif isinstance(items, dict):
        for name, note in items.items():
            st.markdown(f"{icon} **{name}**")
            if isinstance(note, (list, dict)):
                render_generic(note)
            elif note:
                _badge_note(tone, str(note))
    else:
        render_generic(items)


def render_strengths(items) -> None:
    """💪 Strengths — thin wrapper over render_badge_list for naming consistency with the design spec."""
    render_badge_list(items, tone="green")


def render_weaknesses(items) -> None:
    """⚠️ Areas to improve — thin wrapper over render_badge_list for naming consistency with the design spec."""
    render_badge_list(items, tone="orange")


# ---------------------------------------------------------------------------
# Career profile sections
# ---------------------------------------------------------------------------


def render_career_summary(data) -> None:
    """Career-summary dict rendered as headline + prose sections."""
    if isinstance(data, str):
        st.write(data)
        return
    if not isinstance(data, dict):
        render_generic(data)
        return

    headline = data.get("headline") or data.get("title")
    if headline:
        st.subheader(headline)

    summary = data.get("summary") or data.get("professional_summary")
    if summary:
        st.write(summary)

    narrative = data.get("narrative") or data.get("career_narrative")
    if narrative:
        st.markdown("### Professional Narrative")
        st.write(narrative)

    handled = {"headline", "title", "summary", "professional_summary", "narrative", "career_narrative"}
    leftovers = {k: v for k, v in data.items() if k not in handled and v not in (None, "", [], {})}
    for k, v in leftovers.items():
        st.markdown(f"**{humanize(k)}**")
        if isinstance(v, (list, dict)):
            render_generic(v)
        else:
            st.write(v)


def render_experience(data) -> None:
    """Handles both {"years": 2, "industries": [...]} summaries and lists of role cards."""
    if isinstance(data, dict) and any(k in data for k in ("years", "industries", "roles")):
        if data.get("years") is not None:
            st.write(f"• {data['years']} years experience")
        for role in data.get("roles", []) or []:
            st.write(f"• {role}")
        for industry in data.get("industries", []) or []:
            st.write(f"• {industry}")

        handled = {"years", "industries", "roles"}
        leftovers = {k: v for k, v in data.items() if k not in handled and v not in (None, "", [], {})}
        for k, v in leftovers.items():
            st.markdown(f"**{humanize(k)}**")
            render_generic(v)
        return

    render_section(data)


def render_education(data) -> None:
    """Institution / degree / CGPA / graduation, formatted like a transcript card."""
    if isinstance(data, dict):
        institution = data.get("institution") or data.get("university") or data.get("school")
        degree = data.get("degree")
        cgpa = data.get("cgpa") or data.get("gpa")
        graduation = data.get("graduation") or data.get("graduation_year") or data.get("expected_graduation")

        if institution:
            st.markdown(f"**{institution}**")
        if degree:
            st.write(degree)
        if cgpa:
            st.write(f"CGPA: {cgpa}")
        if graduation:
            st.write(f"Graduation: {graduation}")

        handled = {"institution", "university", "school", "degree", "cgpa", "gpa",
                   "graduation", "graduation_year", "expected_graduation"}
        leftovers = {k: v for k, v in data.items() if k not in handled and v not in (None, "", [], {})}
        for k, v in leftovers.items():
            st.markdown(f"**{humanize(k)}**")
            render_generic(v)
        return

    render_section(data)


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


def render_score_changes(changes: dict) -> None:
    """Renders {"career_score": [75, 81]} or {"before": .., "after": ..} as X → Y lines."""
    for key, val in changes.items():
        if isinstance(val, (list, tuple)) and len(val) == 2:
            before, after = val
            st.write(f"**{humanize(key)}:** {before} → {after}")
        elif isinstance(val, dict) and "before" in val and "after" in val:
            st.write(f"**{humanize(key)}:** {val['before']} → {val['after']}")
        else:
            st.write(f"**{humanize(key)}:** {val}")


def render_timeline(snapshots) -> None:
    """List of profile snapshots, each shown as an expander with score deltas / additions."""
    for i, snap in enumerate(snapshots):
        label = snap.get("snapshot_label") or f"Snapshot #{i + 1}"
        created = snap.get("created_at", "N/A")
        with st.expander(f"📌 {label}  —  {created}"):
            payload = snap.get("snapshot_payload") or snap
            if not isinstance(payload, dict):
                render_generic(payload)
                continue

            changes = payload.get("changes") or payload.get("score_changes")
            if changes:
                render_score_changes(changes)

            added = payload.get("added_skills") or payload.get("added")
            if added:
                st.markdown("**Added**")
                for a in added:
                    st.write(f"• {a}")

            if not changes and not added:
                render_generic(payload)


# ---------------------------------------------------------------------------
# Recommendations / roadmap / forecast
# ---------------------------------------------------------------------------


def render_recommendations(data) -> None:
    """Dict of recommendation categories -> expander + cards, or a flat list of cards."""
    if isinstance(data, dict):
        for key, value in data.items():
            with st.expander(f"📚 {humanize(key)}"):
                render_section(value)
    else:
        render_section(data)


def render_learning_roadmap(data) -> None:
    """Dict of time-boxed sections (week/month/etc) -> expanders with cards or checklists."""
    if isinstance(data, dict):
        for key, value in data.items():
            with st.expander(f"🗺️ {humanize(key)}"):
                render_section(value)
    else:
        render_section(data)


def render_learning_plan(data: dict) -> None:
    """Cadence-based learning plan: daily / weekly / monthly / books / projects / etc."""
    sections = [
        ("daily", "📅 Daily"),
        ("weekly", "📆 Weekly"),
        ("monthly", "🗓️ Monthly"),
        ("quarterly", "📊 Quarterly"),
        ("yearly", "📈 Yearly"),
        ("books", "📚 Books"),
        ("projects", "🔨 Projects"),
        ("certifications", "📜 Certifications"),
        ("courses", "🎓 Courses"),
        ("research_papers", "📄 Research Papers"),
        ("open_source_contributions", "🌐 Open Source"),
    ]
    for key, label in sections:
        items = data.get(key, [])
        if items:
            with st.expander(label, expanded=(key in ("daily", "weekly"))):
                for item in items:
                    if isinstance(item, dict):
                        render_card(item)
                    else:
                        st.write(f"• {item}")


def render_salary_projection(projection: dict) -> None:
    """Formatted salary breakdown instead of a raw JSON dump."""
    if not isinstance(projection, dict):
        st.write(projection)
        return

    range_fields = [
        ("low", "Low"), ("min", "Low"), ("minimum", "Low"),
        ("median", "Median"), ("expected", "Median"), ("average", "Median"), ("mid", "Median"),
        ("high", "High"), ("max", "High"), ("maximum", "High"),
    ]
    found = {}
    for field_key, label in range_fields:
        if field_key in projection and label not in found:
            found[label] = projection[field_key]

    if found:
        cols = st.columns(len(found))
        for col, (label, value) in zip(cols, found.items()):
            with col:
                st.metric(label, format_money(value))

    if projection.get("currency"):
        st.caption(f"Currency: {projection['currency']}")

    growth = projection.get("growth_rate") or projection.get("yoy_growth")
    if growth is not None:
        try:
            st.write(f"**Projected Growth:** {float(growth):.1%}")
        except (TypeError, ValueError):
            st.write(f"**Projected Growth:** {growth}")

    note = projection.get("note") or projection.get("notes") or projection.get("commentary")
    if note:
        st.write(note)

    handled = {k for k, _ in range_fields} | {"currency", "growth_rate", "yoy_growth", "note", "notes", "commentary"}
    leftovers = {k: v for k, v in projection.items() if k not in handled and v not in (None, "", [], {})}
    for key, value in leftovers.items():
        label = humanize(key)
        if isinstance(value, dict):
            st.markdown(f"**{label}**")
            for sub_key, sub_value in value.items():
                st.write(f"• {humanize(sub_key)}: {format_money(sub_value)}")
        elif isinstance(value, list):
            st.markdown(f"**{label}**")
            for item in value:
                st.write(f"• {item}")
        else:
            st.write(f"**{label}:** {format_money(value) if isinstance(value, (int, float)) else value}")


def render_forecast(forecasts: list) -> None:
    """List of forecast horizons, each with probabilities, trajectory, and salary projection."""
    for f in forecasts:
        with st.expander(f"📅 {f.get('horizon', 'Unknown Horizon')}  —  Confidence: {f.get('confidence_score', 0):.0%}"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Hiring Probability", f"{f.get('hiring_probability', 0):.0%}")
                st.metric("Promotion Probability", f"{f.get('promotion_probability', 0):.0%}")
            with col2:
                st.write(f"**Trajectory:** {f.get('career_trajectory', 'N/A')}")
                st.write(f"**Timeline:** {f.get('estimated_timeline', 'N/A')}")

            if f.get("predicted_job_titles"):
                st.markdown("**Predicted Job Titles**")
                for title in f["predicted_job_titles"]:
                    st.write(f"• {title}")

            if f.get("salary_projection"):
                with st.expander("💰 Salary Projection"):
                    render_salary_projection(f["salary_projection"])


# ---------------------------------------------------------------------------
# Strategy / progress tracking
# ---------------------------------------------------------------------------


def render_progress_snapshot(data) -> None:
    """Overall completion percent + completed skills/certs/projects, as a progress card."""
    if not isinstance(data, dict):
        render_generic(data)
        return

    pct = data.get("progress_percent") or data.get("percent_complete") or data.get("completion_percent")
    if pct is not None:
        pv = progress_value(pct)
        if pv is not None:
            st.markdown(f"**Overall Progress:** {pv * 100:.0f}%")
            st.progress(pv)
        else:
            st.markdown(f"**Overall Progress:** {pct}")

    completed_skills = data.get("completed_skills")
    if completed_skills:
        st.markdown("**Completed Skills**")
        render_pills(completed_skills) if isinstance(completed_skills, list) else render_generic(completed_skills)

    completed_certs = data.get("completed_certifications")
    if completed_certs:
        st.markdown("**Completed Certifications**")
        render_pills(completed_certs) if isinstance(completed_certs, list) else render_generic(completed_certs)

    completed_projects = data.get("completed_projects")
    if completed_projects:
        st.markdown("**Completed Projects**")
        for p in completed_projects:
            st.write(f"• {p}")

    handled = {
        "progress_percent", "percent_complete", "completion_percent",
        "completed_skills", "completed_certifications", "completed_projects",
    }
    leftovers = {k: v for k, v in data.items() if k not in handled and v not in (None, "", [], {})}
    for k, v in leftovers.items():
        st.markdown(f"**{humanize(k)}**")
        render_generic(v) if isinstance(v, (list, dict)) else st.write(v)


def render_roadmap_step(step: dict, index: int) -> None:
    """A single strategy roadmap step — title, priority, duration, outcomes, dependencies."""
    title = step.get("title") or step.get("topic") or f"Step {index + 1}"
    priority = step.get("priority", "")
    st.markdown(f"**{index + 1}. {title}**" + (f"  `{priority}`" if priority else ""))
    if step.get("duration_weeks"):
        st.write(f"Duration: {step['duration_weeks']} week(s)")
    if step.get("timeframe"):
        st.write(f"Timeframe: {step['timeframe']}")
    if step.get("expected_outcomes"):
        st.write("Expected outcomes: " + ", ".join(step["expected_outcomes"]))
    if step.get("dependencies"):
        st.write("Dependencies: " + ", ".join(step["dependencies"]))
    st.write("---")


def render_roadmap_section(data) -> None:
    """A strategy roadmap: dict of sub-sections (weekly_roadmap, monthly_roadmap, ...) each a step list."""
    if isinstance(data, dict):
        for section_key, section_data in data.items():
            with st.expander(humanize(section_key), expanded=True):
                if isinstance(section_data, list):
                    if section_data and isinstance(section_data[0], dict):
                        for i, step in enumerate(section_data):
                            render_roadmap_step(step, i)
                    else:
                        for step in section_data:
                            st.write(f"• {step}")
                else:
                    render_section(section_data)
    else:
        render_section(data)


# Alias matching the naming convention requested in the design spec.
render_roadmap = render_roadmap_section


def render_checklist(items) -> None:
    """Weekly/monthly goals rendered as a checklist (☑ done / ☐ pending) instead of cards or JSON."""
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                label = item.get("title") or item.get("goal") or item.get("name") or "Untitled goal"
                done = bool(item.get("completed") or item.get("done") or item.get("status") == "completed")
                box = "☑" if done else "☐"
                st.markdown(f"{box} {label}")
                deadline = item.get("deadline") or item.get("due_date")
                if deadline:
                    st.caption(f"Due: {deadline}")
            else:
                st.markdown(f"☐ {item}")
    else:
        render_generic(items)


def render_certifications(items) -> None:
    """📜 Certifications — cards with provider/issuer, status, and date when structured, pills otherwise."""
    if isinstance(items, list) and items and isinstance(items[0], dict):
        for cert in items:
            with st.container(border=True):
                name = cert.get("name") or cert.get("title", "Certification")
                status = cert.get("status")
                st.markdown(f"**{name}**" + (f"  ·  {status}" if status else ""))
                meta_bits = []
                issuer = cert.get("issuer") or cert.get("provider")
                if issuer:
                    meta_bits.append(f"Issuer: {issuer}")
                date = cert.get("date") or cert.get("issued_date") or cert.get("completed_date")
                if date:
                    meta_bits.append(str(date))
                if meta_bits:
                    st.caption(" · ".join(meta_bits))
                handled = {"name", "title", "status", "issuer", "provider", "date", "issued_date", "completed_date"}
                leftovers = {k: v for k, v in cert.items() if k not in handled and v not in (None, "", [], {})}
                for k, v in leftovers.items():
                    st.write(f"**{humanize(k)}:** {v}" if not isinstance(v, (list, dict)) else f"**{humanize(k)}**")
                    if isinstance(v, (list, dict)):
                        render_generic(v)
    elif isinstance(items, list):
        render_pills(items)
    else:
        render_generic(items)


def render_projects(items) -> None:
    """🔨 Project recommendation/portfolio cards — name, description, technologies, outcomes, GitHub, duration."""
    if not isinstance(items, list):
        render_generic(items)
        return

    for proj in items:
        if not isinstance(proj, dict):
            st.write(f"• {proj}")
            continue
        with st.container(border=True):
            title = proj.get("title") or proj.get("name", "Untitled Project")
            difficulty = proj.get("difficulty", "")
            st.markdown(f"**{title}**" + (f"  ·  `{difficulty}`" if difficulty else ""))

            if proj.get("description"):
                st.write(proj["description"])

            col1, col2 = st.columns(2)
            with col1:
                if proj.get("technologies"):
                    st.write("**Technologies:** " + ", ".join(proj["technologies"]))
                if proj.get("skills_gained"):
                    st.write("**Skills gained:** " + ", ".join(proj["skills_gained"]))
                outcomes = proj.get("outcomes") or proj.get("expected_outcomes")
                if outcomes:
                    st.write("**Outcomes:** " + (", ".join(outcomes) if isinstance(outcomes, list) else outcomes))
            with col2:
                duration = proj.get("estimated_duration") or proj.get("duration")
                if duration:
                    st.write(f"**Duration:** {duration}")
                if proj.get("resume_value"):
                    st.write(f"**Resume Value:** {proj['resume_value']}")
                github = proj.get("github") or proj.get("github_url") or proj.get("repo_url")
                if github:
                    st.write(f"**GitHub:** {github}")

            handled = {
                "title", "name", "difficulty", "description", "technologies", "skills_gained",
                "outcomes", "expected_outcomes", "estimated_duration", "duration", "resume_value",
                "github", "github_url", "repo_url",
            }
            leftovers = {k: v for k, v in proj.items() if k not in handled and v not in (None, "", [], {})}
            for k, v in leftovers.items():
                st.write(f"**{humanize(k)}:** {v}" if not isinstance(v, (list, dict)) else f"**{humanize(k)}**")
                if isinstance(v, (list, dict)):
                    render_generic(v)


def render_verdict(data) -> None:
    """Final recommendation / verdict, shown as a colored callout (green/red/blue) plus reasoning."""
    if isinstance(data, str):
        st.info(data)
        return
    if not isinstance(data, dict):
        render_generic(data)
        return

    verdict = data.get("verdict") or data.get("recommendation") or data.get("decision")
    reasoning = data.get("reasoning") or data.get("explanation") or data.get("summary")

    if verdict:
        verdict_lower = str(verdict).lower()
        positive = ("yes", "apply", "strong", "recommend", "good fit", "go for it")
        negative = ("no", "skip", "avoid", "weak", "not recommend", "poor fit")
        if any(w in verdict_lower for w in positive):
            st.success(f"**{verdict}**")
        elif any(w in verdict_lower for w in negative):
            st.error(f"**{verdict}**")
        else:
            st.info(f"**{verdict}**")

    if reasoning:
        st.write(reasoning)

    handled = {"verdict", "recommendation", "decision", "reasoning", "explanation", "summary"}
    leftovers = {k: v for k, v in data.items() if k not in handled and v not in (None, "", [], {})}
    for k, v in leftovers.items():
        st.markdown(f"**{humanize(k)}**")
        render_generic(v) if isinstance(v, (list, dict)) else st.write(v)


# ---------------------------------------------------------------------------
# Resume content
# ---------------------------------------------------------------------------


def render_resume_content(content) -> None:
    """Parsed resume version content — dispatches to summary/skill/experience/education renderers."""
    if not isinstance(content, dict):
        render_generic(content)
        return

    if content.get("summary") or content.get("headline") or content.get("narrative"):
        render_career_summary(content)

    if content.get("skills"):
        st.markdown("**Skills**")
        render_skill_section(content["skills"])

    experience = content.get("experience") or content.get("work_experience")
    if experience:
        st.markdown("**Experience**")
        render_experience(experience)

    if content.get("education"):
        st.markdown("**Education**")
        render_education(content["education"])

    certifications = content.get("certifications")
    if certifications:
        st.markdown("**Certifications**")
        if isinstance(certifications, list) and certifications and isinstance(certifications[0], str):
            render_pills(certifications)
        else:
            render_section(certifications)

    handled = {
        "summary", "headline", "narrative", "skills", "experience", "work_experience",
        "education", "certifications",
    }
    leftovers = {k: v for k, v in content.items() if k not in handled and v not in (None, "", [], {})}
    for k, v in leftovers.items():
        st.markdown(f"**{humanize(k)}**")
        render_generic(v)