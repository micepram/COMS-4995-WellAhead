"""One day, recorded context, and one user-confirmed suggestion."""
import os
from datetime import date, timedelta
from html import escape

import streamlit as st
from dotenv import load_dotenv

from assistant import ACTIONS, ANSWERS, ROOT, change_slot, clock, facts, new_review, restore, save, suggest

load_dotenv(ROOT / ".env")
STORE = ROOT / "var" / "latest-review.json"
st.set_page_config(page_title="WellAhead — Tomorrow, made manageable", layout="wide")

if "review" not in st.session_state or st.session_state.get("ui_version") != 3:
    review = restore(STORE)
    st.session_state.review = review
    st.session_state.scenario = review["scenario"] if review else "Packed day"
    st.session_state.sleep_context = review["sleep_context"] if review else "Usual sleep"
    st.session_state.stress = review["answer"] if review else None
    st.session_state.review_date = review["review_date"] if review else date.today().isoformat()
    st.session_state.highlight = False
    st.session_state.ui_version = 3


def invalidate():
    st.session_state.review = None
    st.session_state.highlight = False
    st.session_state.review_date = date.today().isoformat()
    STORE.unlink(missing_ok=True)


def persist(review):
    try:
        save(STORE, review)
    except OSError:
        st.error("Could not save your choice. Please try again.")
        return
    st.session_state.review = review
    st.rerun()


def timeline(context, window, slot, review):
    start, end = (540, 1020) if window == "daytime" else (1200, 1320)
    position = lambda value: 100 * (value-start) / (end-start)
    blocks = []
    for tick in range(start, end+1, 60):
        blocks.append(f'<div class="hour" style="top:{position(tick)}%"><span>{clock(tick)}</span></div>')
    for left, right in context[window]["busy"]:
        blocks.append(f'<div class="busy" title="Busy {clock(left)}–{clock(right)}" style="top:{position(left)}%;height:{position(right)-position(left)}%">Busy</div>')
    if slot and slot["window"] == window:
        accepted = review["state"] == "accepted"
        label = "Confirmed" if accepted else "Suggested"
        action = ACTIONS[review["action_id"]]
        color = "#167a55" if accepted else "#305bc2"
        style = "solid" if accepted else "dashed"
        blocks.append(f'<div class="action" style="top:{position(slot["start"])}%;height:{position(slot["end"])-position(slot["start"])}%;border-style:{style};border-color:{color};background:{color}20"><div class="action-label">{label} · {action["minutes"]} min<br>{escape(action["category"])} · {clock(slot["start"])}–{clock(slot["end"])}</div></div>')
    st.html(f'<div class="timeline {window}">' + "".join(blocks) + '</div>')


st.html('''<style>
[data-testid="stMainBlockContainer"] {padding:3.6rem 2rem .75rem;max-width:1600px}
[data-testid="stVerticalBlock"] {gap:.5rem}
[data-testid="stHeadingWithActionElements"] h2 {font-size:1.65rem;padding:0;line-height:1.2}
[data-testid="stHeadingWithActionElements"] h3 {font-size:1.2rem;padding:0;line-height:1.2}
[data-testid="stMarkdownContainer"] p {margin-bottom:.2rem;font-size:.9rem}
[data-testid="stCaptionContainer"] p {font-size:.78rem;line-height:1.35}
[data-testid="stDivider"] {margin:.2rem 0}
[data-testid="stAlert"] {padding:.35rem .65rem}
.timeline {position:relative;margin:12px 0 16px;font:12px system-ui;color:#263247}
.timeline.daytime {height:clamp(200px,calc(100dvh - 450px),400px)}
.timeline.evening {height:90px}
.hour {position:absolute;left:0;right:0;border-top:1px solid #cbd5e1;height:1px}
.hour span {position:absolute;top:-8px;background:white;padding-right:7px}
.busy,.action {position:absolute;left:52px;width:calc(100% - 225px);box-sizing:border-box}
.busy {background:#e6e9ed;border:1px solid #c4cad3;border-radius:3px;padding:0 5px;font-size:10px;line-height:11px;color:#263247;overflow:hidden}
.evening .busy {font-size:9px;line-height:9px}
.action {border-width:2px;border-radius:2px}
.action-label {position:absolute;left:calc(100% + 10px);top:-8px;width:162px;font-size:11px;line-height:1.2;font-weight:600;color:#263247;background:white}
@media (max-width:900px) {[data-testid="stMainBlockContainer"] {padding-left:1rem;padding-right:1rem}}
</style>''')
header, settings = st.columns([7, 1], vertical_alignment="center")
with header:
    st.markdown("## Tomorrow, made manageable")
with settings:
    settings_panel = st.popover("Settings", use_container_width=True)
with settings_panel:
    scripted = st.checkbox("Scripted mode", value=os.getenv("WELLAHEAD_SCRIPTED", "false").lower() == "true")
    if st.button("Start over"):
        STORE.unlink(missing_ok=True)
        st.session_state.clear()
        st.rerun()

scenario = st.session_state.scenario
sleep_context = st.session_state.sleep_context
context = facts(scenario, sleep_context)
review = st.session_state.review
slot = review["current_slot"] if review else None
tomorrow = date.fromisoformat(st.session_state.review_date) + timedelta(days=1)
st.caption(f"Tomorrow · {tomorrow.strftime('%A, %d %B')}")

left, right = st.columns([1, 1.25], gap="large")
with left:
    scheduled = context["daytime"]["scheduled_minutes"]
    st.markdown(f"**{scenario} · 09:00–17:00** · {scheduled // 60}h {scheduled % 60:02d}m scheduled")
    timeline(context, "daytime", slot, review)
    st.caption("**Evening · 20:00–22:00** · 45 minutes scheduled")
    timeline(context, "evening", slot, review)
    calendar_details, view = st.columns([3, 2], vertical_alignment="top")
    with view:
        if slot and st.button("View suggestion", use_container_width=True):
            st.session_state.highlight = True
            st.rerun()
    with calendar_details:
        with st.expander("Calendar details"):
            for window in ("daytime", "evening"):
                st.write("**" + window.capitalize() + "**")
                for start, end in context[window]["busy"]:
                    st.write(f"Busy: {clock(start)}–{clock(end)}")
                for gap in context[window]["gaps"]:
                    st.write(f"Gap: {clock(gap['start'])}–{clock(gap['end'])}")

with right:
    with st.container(border=True):
        st.subheader("Plan tomorrow")
        calendar_control, sleep_control = st.columns(2)
        with calendar_control:
            st.radio("Day", ["Packed day", "Lighter day"], horizontal=True, key="scenario", on_change=invalidate)
        with sleep_control:
            st.radio("Sleep", ["Usual sleep", "Shorter sleep"], horizontal=True, key="sleep_context", on_change=invalidate)
        st.caption(f"**Steps (weekly medians):** {context['previous_median']:,.0f} → {context['recent_median']:,.0f} · **Sleep:** {context['sleep_hours']}h last night / {context['usual_sleep_hours']}h usual")
        question, submit = st.columns([4, 1.4], vertical_alignment="bottom")
        with question:
            stress = st.radio("How stressed do you expect to feel tomorrow?", ANSWERS, horizontal=True, index=None, key="stress", on_change=invalidate)
        with submit:
            request_review = st.button("Get suggestion", disabled=stress is None, type="primary", use_container_width=True)
        st.caption("Your expectation, not a wearable measurement.")
        if request_review:
            with st.spinner("Finding a suggestion…"):
                result, mode = suggest(stress, context, scripted)
            updated = new_review(context, stress, result, mode)
            st.session_state.review_date = updated["review_date"]
            persist(updated)
        if review:
            st.divider()
            if st.session_state.highlight:
                st.html('<style>.st-key-suggestion_card {outline:2px solid #305bc2;outline-offset:5px;border-radius:4px}</style>')
            with st.container(key="suggestion_card"):
                mode = "AI suggestion" if review["processing_mode"] == "llm" else "Scripted preview"
                if review["processing_mode"] == "unavailable_preview":
                    st.caption("AI unavailable · Scripted preview")
                else:
                    st.caption(mode)
                if review["state"] == "no-slot":
                    st.markdown("**No other suitable time available.**")
                elif review["state"] == "held":
                    st.markdown("**No suggestion for now.**")
                elif review["state"] == "skipped":
                    st.markdown("**Suggestion skipped.**")
                else:
                    action = ACTIONS[review["action_id"]]
                    st.markdown(f"**{action['title']}**")
                    status = "Confirmed" if review["state"] == "accepted" else "Suggested"
                    st.caption(f"{status} · {action['category']} · {action['minutes']} min · {clock(slot['start'])}–{clock(slot['end'])}")
                st.write(review["explanation"])
                if review["state"] == "pending":
                    accept, alternate, skip = st.columns([1.2, 1.3, .7])
                    if accept.button("This time works", use_container_width=True):
                        persist({**review, "state": "accepted"})
                    if alternate.button("Find another gap", use_container_width=True):
                        persist(change_slot(review, context))
                    if skip.button("Skip", use_container_width=True):
                        persist({**review, "state": "skipped", "current_slot": None})
                with st.expander("Why this suggestion?"):
                    st.write(f"**Wearable context:** step medians {context['previous_median']:,.0f} and {context['recent_median']:,.0f}; {sleep_context.lower()}, {context['sleep_hours']}h versus {context['usual_sleep_hours']}h usual.")
                    st.write(f"**Schedule:** {scenario}, {scheduled} daytime minutes and {context['evening']['scheduled_minutes']} evening minutes.")
                    st.write(f"**Your expected stress:** {review['answer']}.")
