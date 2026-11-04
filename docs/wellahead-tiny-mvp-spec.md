# WellAhead: Tiny MVP Build Spec

## Objective and scope authority

Build a low-fidelity, single-user local prototype that answers one question:

**Can the day's schedule, wearable context, and self-reported expected stress change both the type of wellbeing suggestion and its practical timing?**

This is a proposal-stage interaction prototype. Manual Google Health access and retrieval are verified as of November 4, 2026. The application connector, Calendar access, clinical benefit, and final-project completion are not established by that test.

For this build, this document replaces the larger MVP feature list. The main proposal and full implementation plan remain future scope. Do not implement their additional requirements or modify the existing application to satisfy them.

Create a separate `wellahead-tiny-mvp/` directory. Leave the existing `wellahead-mvp/` application unchanged.

## Verified wearable data and source modes

Use the locally saved November 4 API responses as a read-only input. Do not check private responses into Git, send them to an external model by default, or add an upload interface. Configure an absolute local path with `HEALTH_SAMPLE_PATH`.

The latest 11-stream run returned HTTP 200 for sleep (9 sessions), steps (4 intervals on the first page), heart rate (20 samples), daily HRV (7 records), resting heart rate (7), sedentary periods (20), active-zone minutes (20), breathing rate (7), oxygen saturation (6), sleep-temperature summaries (7), and granular HRV (20). Exercise retrieval separately returned 6 sessions. Steps, heart rate, sedentary periods, active-zone minutes and granular HRV still have continuation tokens. This is a successful sample fetch, not a full-history download or app-managed sync. Initial daily-HRV 503 recovered on retry.

Show only three wearable cards: latest main-sleep minutes asleep, daily resting heart rate, and daily HRV, with source date, unit and retrieval time. The inspected latest values are 398 minutes (6h 38m), 75 bpm, and 24.55 ms on November 4; read them from the file rather than hardcoding them as universal examples. Label these descriptive observations, not stress/readiness scores. Show a compact available-stream list and an evidence expander; do not build 11 charts. Daily HRV/resting heart rate and several other daily metrics have only seven disconnected dates. Show `Insufficient history for a trend comparison`; do not invent a usual baseline or show partial step samples as a daily total. Parse numeric strings and NaN safely.

Keep two explicit modes:

- **Verified-data preview:** saved real wearable responses plus a live or explicitly labeled Calendar snapshot. Show all source dates/statuses. Do not transmit private wearable values to a cloud model without separate opt-in. This mode is read-only: show wearable evidence, Calendar intervals and candidate gaps. Switch to the explicitly fictional interaction scenario for category-changing suggestions; do not present scripted suggestions as medical inferences from private measurements.
- **Fictional interaction scenario:** retain the two calendar layouts and two sleep contexts below for repeatable category-change demonstrations. Every fixture value is labeled fictional. Never combine fictional step baselines with real records into a claimed personal trend.

Default public recording to fictional values unless use of minimized real records has been authorized. The API-success panel can show sanitized stream counts/statuses without identifiers or health values.

## Minimal read-only Calendar integration

A working Calendar read is a target acceptance requirement, **not a verified fact yet**. Add one explicit **Refresh calendar** button using `POST https://www.googleapis.com/calendar/v3/freeBusy`, narrow `calendar.freebusy` consent, one primary calendar, and the displayed target local date. Keep token configuration server-side in ignored local environment settings; an existing authorized token can be supplied manually for this tiny build. Do not build a full OAuth/session framework, background sync, or calendar writes. No credentials in the interface, screenshots, prompts, logs or checked-in files.

Query the target day's 09:00–17:00 and 20:00–22:00 planning windows in its configured IANA timezone. Preserve offsets and intersect retrieved busy intervals with those windows, merging overlap. The UI must distinguish `Live Calendar — retrieved at …`, `Saved Calendar snapshot — captured at …`, `Fictional calendar`, and `Calendar unavailable — availability unknown`. A failed request is never an empty/free calendar. A verified empty result proves retrieval, but a useful recording should also show a known busy interval; verify that it matches the calendar before claiming it works. Retain only busy start/end intervals, requested range, timezone and retrieval status/time. No event titles or content.

Persist a successful snapshot locally for reproducible recording, clearly labeled on replay. Verified-data mode only previews gaps. Any later extension that confirms a live-calendar suggestion must recheck Calendar before confirmation and preserve pending state on failure. Gaps require user confirmation. If access is not ready, leave **FILL IN: verify Calendar access** in slides and use labeled fixtures; do not show a fabricated connected badge.

## One demonstration: Tomorrow, made manageable

1. Open a single Streamlit page with permanent **Proposal prototype** and per-source real/snapshot/fictional labels. Show the sanitized API-success panel and three wearable cards in verified-data mode; a source toggle opens the fictional interaction scenario.
2. Choose **Packed day** or **Lighter day**. These select fictional layouts in interaction mode. Verified-data mode instead uses the target-day live/saved Calendar intervals and their explicit status; no editable calendar is required.
3. See the selected day's small calendar on the left and a **Plan tomorrow** card on the right. In fictional mode, a small **Fictional wearable context** selector switches between **Usual sleep** and **Shorter sleep**. Keep activity history identical so this is a controlled demonstration, not an additional data pipeline.
4. Ask one fixed question: **How stressed do you expect to feel tomorrow?** Offer **Low**, **Moderate**, **High**, and **Not sure**, with no preselected answer. Label this **Your expectation — not a wearable measurement or prediction**.
5. On **Get suggestion**, make one model request using the displayed facts and selected answer. The model selects an eligible action from the small catalog below or holds off, with a short explanation. The fixed category policy below governs fictional scenarios only. The Get suggestion workflow runs only in fictional interaction mode. Verified-data mode demonstrates source retrieval and calendar gaps without generating a recommendation from the sparse private history.
6. Show one offered action as a dashed block inside a suitable calendar gap. Display its category, duration, and explanation, identifying the wearable facts, calendar facts, and user's answer separately. Do not show a list of simultaneous recommendations.
7. Offer **This time works**, **Find another gap**, and **Skip**. Confirming makes the proposed block solid and records acceptance locally. Finding another gap moves it to the next candidate; it never marks the action accepted. Skipping removes the proposed block.
8. If no untried gap remains, show **No other suitable gap in this demo day** with no draft. Do not reuse a rejected gap or schedule over a busy block.
9. Persist only the latest review and its state locally. Provide **Reset demo**.

Three presentation moments matter: changing the day or expected stress changes the suggestion category; changing recorded sleep can bring forward an evening wind-down option; and rejecting a time moves the same action to another eligible gap. Live Calendar retrieval is demonstrated separately from fictional branch comparisons; no multi-day planner is required.

## Small calendar and interface

- Use a vertical 09:00–17:00 timeline with hour labels, neutral busy blocks, visible gaps, and a colored proposed-action block. A small amount of HTML/CSS or a simple chart is sufficient; no calendar package is required.
- Add a compact **Evening: 20:00–22:00** strip beneath the day timeline for the wind-down option. Do not build an all-day scrollable calendar.
- Label events simply **Busy**. Do not invent meeting titles or retrieve event content.
- Show the selected scenario, tomorrow's date, and total scheduled time. Include a plain-text interval list for exact times and accessibility.
- Label a proposed block **Suggested — not confirmed**; accepted blocks read **Accepted in demo**. Use text as well as dashed/solid styling.
- Selecting the proposed block highlights its suggestion card. If Streamlit cannot support direct block clicks simply, use an adjacent native **View suggestion** button. Do not introduce custom JavaScript just for this interaction.
- Include a compact **Why this suggestion?** expander. No chat interface or additional pages.
- **This time works** explicitly confirms the slot and acceptance of the displayed action. It does not write to any external calendar.

## Fixed fictional inputs

Use one checked-in JSON fixture containing two calendar layouts and two fixed sleep contexts. In fictional mode, the two selectors and one stress question are the only context controls. The separate verified-data panel uses a configured local file and one manual Calendar refresh. Configure `GOOGLE_CALENDAR_ACCESS_TOKEN` and `CALENDAR_TIMEZONE` locally, and obtain the required Calendar scope separately from the existing health-only token. Use `HEALTH_SAMPLE_PATH` for the private sample file. No uploads, user profiles, data editing UI, or full account-connection flow.

- Previous seven completed days' recorded steps: 7,000, 7,500, 8,000, 7,200, 7,800, 7,500, 7,600.
- Most recent seven completed days: 4,000, 4,500, 5,000, 4,200, 4,800, 4,500, 4,600.
- **Usual sleep:** last night's recorded sleep 7 hours; fictional usual recorded sleep 7 hours. **Shorter sleep:** last night's recorded sleep 6 hours; fictional usual recorded sleep 7 hours. These are supplied example values, not a new sleep-analysis pipeline or a forecast of tonight's sleep.
- Fictional device-wear context: usual wear throughout; self-reported as part of the example, not inferred.
- **Packed day:** busy 09:00–12:30, 12:45–15:00, and 15:10–17:00. Gaps: 12:30–12:45 and 15:00–15:10. Total scheduled time: 7 hours 35 minutes.
- **Lighter day:** busy 09:00–10:00, 11:00–12:00, and 14:00–15:00. Gaps: 10:00–11:00, 12:00–14:00, and 15:00–17:00. Total scheduled time: 3 hours.
- Both layouts have evening busy intervals 20:00–20:30 and 21:00–21:15. Evening gaps: 20:30–21:00 and 21:15–22:00. Report the daytime totals above as **Scheduled time, 09:00–17:00**, separately from the 45 scheduled evening minutes.
- Planning windows are 09:00–17:00 for daytime actions and 20:00–22:00 for wind-down. Start an action at the beginning of the earliest untried gap in its allowed window that fits its duration. The unshown interval 17:00–20:00 is outside demo planning scope, not assumed free.
- The fictional adult has no reported activity restriction. This is an example assumption, not a screening or triage feature.

Compute medians from the arrays: 7,500 and 4,500 recorded steps. Compute scheduled minutes and gaps from the busy intervals. A few lines of deterministic code are sufficient. Do not build a general analysis engine.

Use one local demo date established when a review starts; label the calendar as tomorrow relative to that date. Save that date with the review so a restored review retains its original context. Use the configured timezone for the live Calendar query and retain source offsets/dates for real wearable data; do not reinterpret historical source days using the laptop timezone.

Never describe the step difference as proof of inactivity or the busy schedule as measured/predicted stress. **Scheduled commitments**, **Recorded wearable context**, and **Your expected stress** must appear as separate facts. A lighter calendar can still feel stressful. Every displayed gap is a candidate until the user confirms it.

## Small suggestion catalog and fictional decision policy

Use four suggestion categories, represented by five fixed action IDs. Do not generate arbitrary health advice.

| Category | Action ID | Fixed suggestion | Allowed window |
| --- | --- | --- | --- |
| Movement | `easy_walk_10` | Ten-minute easy walk the example user already feels comfortable doing | Daytime |
| Movement | `easy_walk_20` | Twenty-minute version of the same walk | Daytime |
| Screen break | `screen_break_10` | Ten minutes away from the screen and current task | Daytime |
| Quiet recovery | `quiet_break_10` | Ten-minute quiet pause away from tasks | Daytime |
| Sleep routine | `wind_down_20` | Twenty-minute screen-free quiet wind-down using a familiar routine | Evening |

No breathing protocol, exercise prescription, sleep target, treatment claim, or promised stress/sleep improvement. A wind-down is an ordinary optional routine, not a claim to correct the recorded sleep difference.

The following priority order selects the eligible demo action. This is deliberately small enough to implement as a function, not a rules engine:

1. **Not sure:** hold off; do not ask another question.
2. **High expected stress:** `quiet_break_10`, for either day and either sleep context.
3. **Low or Moderate expected stress + Shorter sleep:** `wind_down_20`, for either day.
4. **Usual sleep + Low expected stress + Packed day:** `screen_break_10`.
5. **Usual sleep + Low expected stress + Lighter day:** `easy_walk_20`.
6. **Usual sleep + Moderate expected stress:** `easy_walk_10`, for either day.
7. If no eligible gap fits the selected action, hold off. Do not move an evening action into daytime, shorten it, or choose a different action automatically.

Examples to make adaptation visible:

| Day | Recorded sleep | Expected stress | Scripted suggestion |
| --- | --- | --- | --- |
| Packed | Usual | Low | Ten-minute screen break in a short daytime gap |
| Lighter | Usual | Low | Twenty-minute easy walk in a longer daytime gap |
| Either | Usual | Moderate | Ten-minute easy walk |
| Either | Either | High | Ten-minute quiet pause |
| Either | Shorter | Low or Moderate | Twenty-minute evening wind-down |
| Either | Either | Not sure | Hold off |

These are transparent interaction design choices, not validated clinical rules. The demo must not imply that high stress always requires rest, shorter sleep always requires wind-down, or these fixed choices are medically optimal. The calendar controls timing and influences the low-stress action choice; sleep context and self-reported stress can change the category. Keep the evidence visible.

For fictional scenarios in scripted mode, select the action above. In fictional scenarios using a real model, the model may select that eligible action or hold; the server enforces the same catalog, priority order, durations, and scheduling constraints. This intentionally bounded prototype tests understandable adaptation rather than unconstrained clinical reasoning.

## Minimal implementation

- Python and Streamlit, plain default components.
- One checked-in fictional JSON fixture, one configured private wearable sample file, and ignored local files for the latest review and Calendar snapshot; no database.
- One model provider using its maintained Python SDK and an environment-variable API key. Reuse the team's configured provider if available. Never copy credentials into source or fixtures.
- One request per explicit Get suggestion submission; Streamlit reruns, viewing the card, finding another gap, accepting, skipping, and restoring saved state must not repeat it.
- A short system prompt and structured output containing `decision` (`offer` or `hold`), `action_id` (one of the five catalog IDs, or null), `evidence_ids`, and a brief `explanation`. A hold has a null action.
- Supply fixed evidence IDs for the displayed source/date-specific wearable summary, Calendar snapshot or fixture, and user's expected-stress answer. In fictional mode, include the selected sleep context and step summary. Validate that returned IDs exist and offers reference the answer plus the context determining that action: calendar for the packed/lighter low-stress branch, sleep for wind-down. The placement explanation is generated deterministically from the current gap, so moving the block does not leave stale times in model text.
- The model explains the action choice without precise slot times. The server places it, validates answer/action eligibility, and controls duration. Reject invalid offers as invalid output; do not silently substitute another model decision.
- Keep model wording short and anchored to supplied facts. It may acknowledge the user's reported expected stress; prompt against medical claims, causal claims, and inferred/predicted stress. Do not claim that schema checks guarantee semantic safety.
- On missing credentials, timeout, or invalid output, show **Model unavailable — scripted preview** and a deterministic preview of the same allowed branch. Do not silently retry or represent the preview as an LLM result.
- Allow an explicit scripted mode for recording without credentials. Always display whether a result is **LLM-generated** or **Scripted preview**.
- Save only the fixture version, review date, selected calendar scenario, selected sleep context, expected-stress answer, validated decision/action, evidence IDs, explanation, processing mode, current slot, rejected gap IDs, and pending/accepted/skipped/no-slot/held state. Never save prompts containing credentials or copy raw provider responses into the saved review. Record health/calendar source mode, snapshot identity and retrieval time. Keep optional cloud sharing off for private records by default.
- Reset removes the saved review and clears the screen. Changing the stress answer, sleep context, or calendar scenario invalidates the previous result and acceptance state until resubmission. Accepted or skipped results have no further slot controls until a new review starts.
- Finding another gap rejects the entire current gap, not just its first five minutes. Move the same action to the next untried gap in chronological order. Do not call the model again or build a search/optimization framework.

Suggested files: `app.py`, `assistant.py`, `fixture.json`, `requirements.txt`, `.env.example`, `.gitignore`, and a short `README.md`. Keep code small; do not introduce an extensible framework.

The README must explain installation, environment variables, running `streamlit run app.py`, scripted mode, resetting, and the synthetic/real-model boundary. Include a short recording path: compare Packed/Lighter with Usual sleep + Low stress; change stress to High and try another gap; then select Shorter sleep + Moderate stress to show evening wind-down. Do not claim model intelligence for the deterministic category, scheduling, or eligibility rules.

## Explicitly out of scope

- App-managed Google Health OAuth/sync, full-history pagination/backfill, uploads, multiple calendars, and background Calendar sync. The only live provider call required here is the small read-only Calendar fetch described above.
- Sleep coaching beyond the single fixed wind-down option, historical trend pipelines, multi-day plans, habit tracking, follow-up check-ins, memory, or notifications.
- Event creation/editing, drag and drop, week/month views, travel-time inference, stress prediction/scores, or automatic insertion of accepted actions into a real calendar.
- Free-form chat, agents, tool calling, RAG, embeddings, vector databases, or web search.
- Authentication, multiple users, deployment, polished dashboard, mobile layouts, or a separate frontend/backend.
- Comparative evaluation infrastructure, comprehensive test suites, production security infrastructure, or clinical screening.

The three-day plan is deliberately replaced by one proposed action for tomorrow. Calendar has a minimal live read plus labeled saved/fictional fallbacks. Wearable evidence comes from verified saved API responses. The complete application integrations, agent retrieval loop and longitudinal evaluation remain final-project scope. Prefer default Streamlit components and a basic timeline over visual polish.

## Completion checks

Demonstrate and briefly record these manual checks; no testing framework is required:

1. Both calendar layouts render correct daytime/evening intervals, scheduled totals, gaps, step medians, and selected sleep summary. Calendar facts, recorded sleep, and self-reported expected stress are separately labeled.
2. In scripted mode, exercise all six rows of the example table. Changing the day, sleep context, or stress must produce the specified category/duration or hold. Display the category and duration, not just a different explanation for the same action.
3. Packed day + High stress initially proposes 12:30–12:35. Find another gap moves it to 15:00–15:05; rejecting that gap leaves no draft despite evening availability, because this action is daytime-only. Lighter day + Usual sleep + Low stress proposes 10:00–10:10. Wind-down proposes 20:30–20:40, then 21:15–21:25 if rejected. Nothing overlaps a busy block or reuses a rejected gap.
4. In model mode, the eligible action or hold is allowed; mismatched actions, durations/windows, and unknown evidence IDs cannot bypass validation. Show at least one genuine model result if credentials are available, and report honestly if none was obtained.
5. A proposed block remains dashed/pending until This time works; confirmation makes it solid/accepted. Skip removes the block. Viewing the suggestion card highlights it without changing its state. Changing any context input clears the previous result.
6. Reload restores the latest saved review, including rejected gaps and acceptance state; Reset clears it. Only explicit Get suggestion submissions may make a model request.
7. Missing credentials or a failed request clearly identifies the scripted preview.

8. Verified-data mode reads the actual sample file, shows dated sleep/RHR/HRV values, reports sparse history and paginated streams, and never mislabels partial steps as a daily total. No private payload or token is checked into Git.
9. Live Calendar retrieves and displays a verified target-day busy interval and timestamp; repeat in saved-snapshot mode with its label. Test denied/expired access as unknown availability. If the live check cannot be completed, report it as pending and keep fixtures explicitly labeled.

Deliver the runnable prototype, a short README, and a brief honest note on which checks were performed. Capture the category-change examples and one alternate-slot interaction for the proposal presentation. Stop when these checks pass; do not expand into the full implementation plan.
