"""Read-only UI. This module has no model or suggestion entry point."""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st

from assistant import ROOT, clock
from sources import calendar_context, health_sample, load_snapshot, refresh_calendar, save_snapshot

SNAPSHOT = ROOT / "var" / "calendar-snapshot.json"


def render_preview(timeline):
    timezone = os.getenv("CALENDAR_TIMEZONE", "Europe/Amsterdam")
    try:
        target = (datetime.now(ZoneInfo(timezone)).date()+timedelta(days=1)).isoformat()
    except (ZoneInfoNotFoundError, ValueError):
        st.error("Configure a valid IANA CALENDAR_TIMEZONE before refreshing Calendar.")
        return
    st.caption(f"Tomorrow · {target} · {timezone} · Proposal prototype · Read-only · Model processing off")
    sample = health_sample(os.getenv("HEALTH_SAMPLE_PATH", ""))
    saved = load_snapshot(SNAPSHOT, target, timezone)
    left, right = st.columns([1, 1.25], gap="large")
    with right:
        st.subheader("Wearable observations")
        if sample["status"] == "loaded":
            streams = sample["streams"]
            successes = sum(s["http_status"] == 200 for s in streams)
            st.caption(f"Saved API sample · {successes}/{len(streams)} streams returned HTTP 200 · {sum(s['paginated'] for s in streams)} have more pages")
            for column, card in zip(st.columns(3), sample["cards"], strict=True):
                with column, st.container(border=True):
                    st.caption(card["label"])
                    value = card.get("value")
                    st.markdown(f"### {value:g}" if value is not None else "### —")
                    st.caption(f"{card['unit']} · {card.get('source_date', 'Date unavailable')}")
                    if card["kind"] == "sleep" and value is not None:
                        st.caption(f"{int(value)//60}h {int(value)%60:02d}m")
            captured = sample.get("captured_at")
            if captured:
                st.caption(f"Export captured: {captured} (export folder timestamp)")
            retrievals = {c.get('retrieved_at') for c in sample['cards']}
            st.caption("Retrieval time: not present in the saved responses" if None in retrievals else "Retrieved: " + ", ".join(sorted(retrievals)))
            st.info("Insufficient history for a trend comparison")
            st.caption("Descriptive observations · Partial step samples are not daily totals")
            with st.expander("Available streams and evidence"):
                st.dataframe([{"Stream": s['stream'], "HTTP": s['http_status'], "Records in sample": s['count'],
                               "More pages": "Yes" if s['paginated'] else "No token returned"} for s in streams], hide_index=True)
                for card in sample['cards']:
                    st.caption(f"{card['label']}: {card['date_count']} distinct source dates · {card.get('evidence_id','No observation')}")
                st.caption("Source dates and sleep end offsets are preserved. No usual baseline is inferred. No private values are sent to the model.")
        elif sample["status"] == "unconfigured":
            st.info("Set HEALTH_SAMPLE_PATH to the saved response file or export directory.")
        else:
            st.error("The configured health sample could not be read. Check its path and saved-response format.")
        st.caption("For category-changing suggestions, select Fictional interaction above.")
    with left:
        heading, refresh = st.columns([2, 1], vertical_alignment="center")
        with heading:
            st.subheader("Primary Calendar")
        with refresh:
            refresh_clicked = st.button("Refresh calendar", use_container_width=True)
        if refresh_clicked:
            with st.spinner("Reading busy intervals…"):
                value, error = refresh_calendar(os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN", ""), target, timezone)
            st.session_state.calendar_error = error
            st.session_state.calendar_live = value
            if value:
                try:
                    save_snapshot(SNAPSHOT, value)
                    saved = value
                except OSError:
                    st.warning("Calendar retrieved, but the local snapshot could not be saved.")
        error = st.session_state.get("calendar_error")
        current = st.session_state.get("calendar_live")
        if current and (current['target_day'] != target or current['timezone'] != timezone):
            current = None
        if error:
            st.warning("Calendar unavailable — availability unknown")
            st.caption(error)
            if saved and st.button("Show saved snapshot"):
                st.session_state.calendar_error = None
                st.session_state.calendar_live = None
                st.rerun()
            current = None
        else:
            live = current is not None
            current = current or saved
            if current:
                label = "Live Calendar — retrieved at" if live else "Saved Calendar snapshot — captured at"
                st.caption(f"{label} {current['retrieved_at']}")
        if current:
            context = calendar_context(current)
            total = context['daytime']['scheduled_minutes']
            st.caption(f"09:00–17:00 · {total//60}h {total%60:02d}m scheduled")
            timeline(context, 'daytime', None, None)
            st.caption(f"Evening · 20:00–22:00 · {context['evening']['scheduled_minutes']} minutes scheduled")
            timeline(context, 'evening', None, None)
            if not current['busy']:
                st.caption("Successful query: no recorded busy intervals in the planning windows.")
            with st.expander("Calendar intervals and candidate gaps"):
                for window in ('daytime','evening'):
                    st.write('**'+window.capitalize()+'**')
                    for start,end in context[window]['busy']:
                        st.write(f"Busy: {clock(start)}–{clock(end)}")
                    for gap in context[window]['gaps']:
                        st.write(f"Candidate gap: {clock(gap['start'])}–{clock(gap['end'])}")
                st.caption(f"Snapshot {current['identity']} · {current['timezone']} · Primary calendar only")
                for bounds in current["busy"]:
                    st.caption(bounds["start"] + " → " + bounds["end"])
        elif not error:
            st.info("Calendar unavailable — availability unknown")
            st.caption("Refresh Calendar after configuring its free/busy token.")
        if not current:
            st.caption("FILL IN: verify Calendar access")
