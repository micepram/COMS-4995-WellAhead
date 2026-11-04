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
st.title("Tomorrow, made manageable")

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
    start, end, height = (540, 1020, 640) if window == "daytime" else (1200, 1320, 130)
    scale = height / (end-start)
    blocks = []
    for tick in range(start, end+1, 60):
        blocks.append(f'<div class="hour" style="top:{(tick-start)*scale}px"><span>{clock(tick)}</span></div>')
    for left, right in context[window]["busy"]:
        blocks.append(f'<div class="busy" style="top:{(left-start)*scale}px;height:{(right-left)*scale}px">Busy</div>')
    if slot and slot["window"] == window:
        accepted = review["state"] == "accepted"
        label = "Confirmed" if accepted else "Suggested"
        action = ACTIONS[review["action_id"]]
        color = "#167a55" if accepted else "#305bc2"
        style = "solid" if accepted else "dashed"
        blocks.append(f'<div class="action" style="top:{(slot["start"]-start)*scale}px;height:{action["minutes"]*scale}px;border-style:{style};border-color:{color};background:{color}20"><div class="action-label">{label}<br>{escape(action["category"])} · {action["minutes"]} min<br>{clock(slot["start"])}–{clock(slot["end"])}</div></div>')
    st.html(f'<div class="timeline" style="height:{height+20}px">' + "".join(blocks) + '</div>')


st.html('''<style>
.timeline {position:relative;margin:14px 0 8px;font:13px system-ui;color:#263247}
.hour {position:absolute;left:0;right:0;border-top:1px solid #cbd5e1;height:1px}
.hour span {position:absolute;top:-9px;background:white;padding-right:7px}
.busy,.action {position:absolute;left:60px;width:calc(100% - 230px);box-sizing:border-box}
.busy {background:#e6e9ed;border:1px solid #c4cad3;border-radius:3px;padding:0 5px;font-size:11px;line-height:12px;color:#263247;overflow:hidden}
.action {border-width:2px;border-radius:2px}
.action-label {position:absolute;left:calc(100% + 12px);top:-10px;width:158px;font-size:12px;font-weight:600;color:#263247;background:white}
</style>''')
with st.sidebar:
    st.subheader("Settings")
    scripted = st.checkbox("Scripted mode", value=os.getenv("WELLAHEAD_SCRIPTED", "false").lower() == "true")
    if st.button("Start over"):
        STORE.unlink(missing_ok=True)
        st.session_state.clear()
        st.rerun()

calendar_control, sleep_control = st.columns(2)
with calendar_control:
    scenario = st.radio("Your day", ["Packed day", "Lighter day"], horizontal=True, key="scenario", on_change=invalidate)
with sleep_control:
    sleep_context = st.radio("Recorded wearable context", ["Usual sleep", "Shorter sleep"], horizontal=True, key="sleep_context", on_change=invalidate)
context = facts(scenario, sleep_context)
review = st.session_state.review
slot = review["current_slot"] if review else None
tomorrow = date.fromisoformat(st.session_state.review_date) + timedelta(days=1)
st.caption(f"Tomorrow · {tomorrow.strftime('%A, %d %B')}")

left, right = st.columns([1.1, 1], gap="large")
with left:
    st.subheader(f"{scenario} · {tomorrow.strftime('%a %d %b')}")
    scheduled = context["daytime"]["scheduled_minutes"]
    st.write(f"**Scheduled time, 09:00–17:00: {scheduled // 60}h {scheduled % 60:02d}m**")
    timeline(context, "daytime", slot, review)
    st.write("**Evening: 20:00–22:00** · 45 minutes scheduled")
    timeline(context, "evening", slot, review)
    if slot and st.button("View suggestion"):
        st.session_state.highlight = True
        st.rerun()
    with st.expander("Exact calendar intervals"):
        for window in ("daytime", "evening"):
            st.write("**" + window.capitalize() + "**")
            for start, end in context[window]["busy"]:
                st.write(f"Busy: {clock(start)}–{clock(end)}")
            for gap in context[window]["gaps"]:
                st.write(f"Available gap: {clock(gap['start'])}–{clock(gap['end'])} ({gap['end']-gap['start']} minutes)")

with right:
    with st.container(border=True):
        st.subheader("Plan tomorrow")
        st.write(f"**Recorded steps:** previous week median {context['previous_median']:,.0f}; recent week median {context['recent_median']:,.0f}.")
        st.write(f"**Recorded sleep:** last night {context['sleep_hours']} hours; usual {context['usual_sleep_hours']} hours.")
        stress = st.radio("How stressed do you expect to feel tomorrow?", ANSWERS, index=None, key="stress", on_change=invalidate)
        st.caption("Your expectation, not a wearable measurement.")
        if st.button("Get suggestion", disabled=stress is None, type="primary"):
            with st.spinner("Finding a suggestion…"):
                result, mode = suggest(stress, context, scripted)
            updated = new_review(context, stress, result, mode)
            st.session_state.review_date = updated["review_date"]
            persist(updated)
    if review:
        if st.session_state.highlight:
            st.html('<style>.st-key-suggestion_card {outline:3px solid #305bc2;outline-offset:3px;border-radius:8px}</style>')
        with st.container(border=True, key="suggestion_card"):
            st.subheader("Your suggestion")
            if st.session_state.highlight:
                st.caption("Selected suggestion")
            if review["processing_mode"] == "unavailable_preview":
                st.warning("AI unavailable — showing a scripted preview")
            st.caption("AI suggestion" if review["processing_mode"] == "llm" else "Scripted preview")
            st.write(review["explanation"])
            if review["state"] == "no-slot":
                st.info("No other suitable time available.")
            elif review["state"] == "held":
                st.info("No suggestion for now.")
            elif review["state"] == "skipped":
                st.info("Suggestion skipped.")
            else:
                action = ACTIONS[review["action_id"]]
                st.write(f"**{action['title']}**")
                st.caption(f"{action['category']} · {action['minutes']} minutes · {slot['window'].capitalize()}")
                st.write(f"{tomorrow.isoformat()} · {clock(slot['start'])}–{clock(slot['end'])}")
                if review["state"] == "accepted":
                    st.success("Confirmed")
                else:
                    st.info("Suggested")
                    if st.button("This time works"):
                        persist({**review, "state": "accepted"})
                    if st.button("Find another gap"):
                        persist(change_slot(review, context))
                    if st.button("Skip"):
                        persist({**review, "state": "skipped", "current_slot": None})
            with st.expander("Why this suggestion?"):
                st.write(f"**Recorded wearable context:** step medians {context['previous_median']:,.0f} and {context['recent_median']:,.0f}; {sleep_context.lower()}, {context['sleep_hours']} hours versus {context['usual_sleep_hours']} usual hours.")
                st.write(f"**Scheduled commitments:** {scenario}, {scheduled} daytime minutes and {context['evening']['scheduled_minutes']} evening minutes.")
                st.write(f"**Your expected stress:** {review['answer']}.")
