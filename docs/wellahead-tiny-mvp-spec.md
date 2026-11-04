# WellAhead: Tiny MVP Build Spec

## Objective and scope authority

Build a low-fidelity, single-user local prototype that answers one question:

**Can the day's schedule, wearable context, and self-reported expected stress change both the type of wellbeing suggestion and its practical timing?**

This is a proposal-stage interaction prototype. It does not establish live API access, clinical benefit, or completion of the final course project.

For this build, this document replaces the larger MVP feature list. The main proposal and full implementation plan remain future scope. Do not implement their additional requirements or modify the existing application to satisfy them.

Create a separate `wellahead-tiny-mvp/` directory. Leave the existing `wellahead-mvp/` application unchanged.

## One demonstration: Tomorrow, made manageable

1. Open a single Streamlit page with a permanent **Fictional data — proposal prototype** label.
2. Choose **Packed day** or **Lighter day**. These are fictional scenarios, not connected accounts or editable calendars.
3. See tomorrow's small day calendar on the left and a **Plan tomorrow** card on the right. A small **Fictional wearable context** selector switches between **Usual sleep** and **Shorter sleep**. Keep activity history identical so this is a controlled demonstration, not an additional data pipeline.
4. Ask one fixed question: **How stressed do you expect to feel tomorrow?** Offer **Low**, **Moderate**, **High**, and **Not sure**, with no preselected answer. Label this **Your expectation — not a wearable measurement or prediction**.
5. On **Get suggestion**, make one model request using the displayed facts and selected answer. The model selects an eligible action from the small catalog below or holds off, with a short explanation.
6. Show one offered action as a dashed block inside a suitable calendar gap. Display its category, duration, and explanation, identifying the wearable facts, calendar facts, and user's answer separately. Do not show a list of simultaneous recommendations.
7. Offer **This time works**, **Find another gap**, and **Skip**. Confirming makes the proposed block solid and records acceptance locally. Finding another gap moves it to the next candidate; it never marks the action accepted. Skipping removes the proposed block.
8. If no untried gap remains, show **No other suitable gap in this demo day** with no draft. Do not reuse a rejected gap or schedule over a busy block.
9. Persist only the latest review and its state locally. Provide **Reset demo**.

Three presentation moments matter: changing the day or expected stress changes the suggestion category; changing recorded sleep can bring forward an evening wind-down option; and rejecting a time moves the same action to another eligible gap. None requires real integrations or a multi-day planner.

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

Use one checked-in JSON fixture containing two calendar layouts and two fixed sleep contexts. The two selectors and one stress question are the only context controls. No uploads, account connections, date picker, user profiles, or data editing UI.

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

Use one local demo date established when a review starts; label the calendar as tomorrow relative to that date. Save that date with the review so a restored review retains its original context. No timezone framework is needed.

Never describe the step difference as proof of inactivity or the busy schedule as measured/predicted stress. **Scheduled commitments**, **Recorded wearable context**, and **Your expected stress** must appear as separate facts. A lighter calendar can still feel stressful. Every displayed gap is a candidate until the user confirms it.

## Small suggestion catalog and decision policy

Use four suggestion categories, represented by five fixed action IDs. Do not generate arbitrary health advice.

| Category | Action ID | Fixed suggestion | Allowed window |
| --- | --- | --- | --- |
| Movement | `easy_walk_5` | Five-minute easy walk the fictional user already feels comfortable doing | Daytime |
| Movement | `easy_walk_10` | Ten-minute version of the same walk | Daytime |
| Screen break | `screen_break_2` | Two minutes away from the screen and current task | Daytime |
| Quiet recovery | `quiet_break_5` | Five-minute quiet pause away from tasks | Daytime |
| Sleep routine | `wind_down_10` | Ten-minute screen-free quiet wind-down using a familiar routine | Evening |

No breathing protocol, exercise prescription, sleep target, treatment claim, or promised stress/sleep improvement. A wind-down is an ordinary optional routine, not a claim to correct the recorded sleep difference.

The following priority order selects the eligible demo action. This is deliberately small enough to implement as a function, not a rules engine:

1. **Not sure:** hold off; do not ask another question.
2. **High expected stress:** `quiet_break_5`, for either day and either sleep context.
3. **Low or Moderate expected stress + Shorter sleep:** `wind_down_10`, for either day.
4. **Usual sleep + Low expected stress + Packed day:** `screen_break_2`.
5. **Usual sleep + Low expected stress + Lighter day:** `easy_walk_10`.
6. **Usual sleep + Moderate expected stress:** `easy_walk_5`, for either day.
7. If no eligible gap fits the selected action, hold off. Do not move an evening action into daytime, shorten it, or choose a different action automatically.

Examples to make adaptation visible:

| Day | Recorded sleep | Expected stress | Scripted suggestion |
| --- | --- | --- | --- |
| Packed | Usual | Low | Two-minute screen break in a short daytime gap |
| Lighter | Usual | Low | Ten-minute easy walk in a longer daytime gap |
| Either | Usual | Moderate | Five-minute easy walk |
| Either | Either | High | Five-minute quiet pause |
| Either | Shorter | Low or Moderate | Ten-minute evening wind-down |
| Either | Either | Not sure | Hold off |

These are transparent interaction design choices, not validated clinical rules. The demo must not imply that high stress always requires rest, shorter sleep always requires wind-down, or these fixed choices are medically optimal. The calendar controls timing and influences the low-stress action choice; sleep context and self-reported stress can change the category. Keep the evidence visible.

In scripted mode, select the action above. In real-model mode, the model may select that eligible action or hold; the server enforces the same catalog, priority order, durations, and scheduling constraints. This intentionally bounded prototype tests understandable adaptation rather than unconstrained clinical reasoning.

## Minimal implementation

- Python and Streamlit, plain default components.
- One JSON fixture and one ignored JSON file for the latest saved review; no database.
- One model provider using its maintained Python SDK and an environment-variable API key. Reuse the team's configured provider if available. Never copy credentials into source or fixtures.
- One request per explicit Get suggestion submission; Streamlit reruns, viewing the card, finding another gap, accepting, skipping, and restoring saved state must not repeat it.
- A short system prompt and structured output containing `decision` (`offer` or `hold`), `action_id` (one of the five catalog IDs, or null), `evidence_ids`, and a brief `explanation`. A hold has a null action.
- Supply fixed evidence IDs for the step summary, selected sleep context, calendar scenario, and user's expected-stress answer. Validate that returned IDs exist and offers reference the answer plus the context determining that action: calendar for the packed/lighter low-stress branch, sleep for wind-down. The placement explanation is generated deterministically from the current gap, so moving the block does not leave stale times in model text.
- The model explains the action choice without precise slot times. The server places it, validates answer/action eligibility, and controls duration. Reject invalid offers as invalid output; do not silently substitute another model decision.
- Keep model wording short and anchored to supplied facts. It may acknowledge the user's reported expected stress; prompt against medical claims, causal claims, and inferred/predicted stress. Do not claim that schema checks guarantee semantic safety.
- On missing credentials, timeout, or invalid output, show **Model unavailable — scripted preview** and a deterministic preview of the same allowed branch. Do not silently retry or represent the preview as an LLM result.
- Allow an explicit scripted mode for recording without credentials. Always display whether a result is **LLM-generated** or **Scripted preview**.
- Save only the fixture version, review date, selected calendar scenario, selected sleep context, expected-stress answer, validated decision/action, evidence IDs, explanation, processing mode, current slot, rejected gap IDs, and pending/accepted/skipped/no-slot/held state. Never save prompts containing credentials or raw provider responses.
- Reset removes the saved review and clears the screen. Changing the stress answer, sleep context, or calendar scenario invalidates the previous result and acceptance state until resubmission. Accepted or skipped results have no further slot controls until a new review starts.
- Finding another gap rejects the entire current gap, not just its first five minutes. Move the same action to the next untried gap in chronological order. Do not call the model again or build a search/optimization framework.

Suggested files: `app.py`, `assistant.py`, `fixture.json`, `requirements.txt`, `.env.example`, `.gitignore`, and a short `README.md`. Keep code small; do not introduce an extensible framework.

The README must explain installation, environment variables, running `streamlit run app.py`, scripted mode, resetting, and the synthetic/real-model boundary. Include a short recording path: compare Packed/Lighter with Usual sleep + Low stress; change stress to High and try another gap; then select Shorter sleep + Moderate stress to show evening wind-down. Do not claim model intelligence for the deterministic category, scheduling, or eligibility rules.

## Explicitly out of scope

- Google Health/Fitbit or Calendar APIs, OAuth, sync, wearable exports, uploads.
- Sleep coaching beyond the single fixed wind-down option, historical trend pipelines, multi-day plans, habit tracking, follow-up check-ins, memory, or notifications.
- Event creation/editing, drag and drop, week/month views, travel-time inference, stress prediction/scores, or automatic insertion of accepted actions into a real calendar.
- Free-form chat, agents, tool calling, RAG, embeddings, vector databases, or web search.
- Authentication, multiple users, deployment, polished dashboard, mobile layouts, or a separate frontend/backend.
- Comparative evaluation infrastructure, comprehensive test suites, production security infrastructure, or clinical screening.

The three-day plan is deliberately replaced by one proposed action for tomorrow. Calendar integration is represented by two fictional day layouts in one fixture. Storage is one local file. This prototype validates the interaction concept; integration feasibility remains future work. Prefer default Streamlit components and a basic timeline over visual polish.

## Completion checks

Demonstrate and briefly record these manual checks; no testing framework is required:

1. Both calendar layouts render correct daytime/evening intervals, scheduled totals, gaps, step medians, and selected sleep summary. Calendar facts, recorded sleep, and self-reported expected stress are separately labeled.
2. In scripted mode, exercise all six rows of the example table. Changing the day, sleep context, or stress must produce the specified category/duration or hold. Display the category and duration, not just a different explanation for the same action.
3. Packed day + High stress initially proposes 12:30–12:35. Find another gap moves it to 15:00–15:05; rejecting that gap leaves no draft despite evening availability, because this action is daytime-only. Lighter day + Usual sleep + Low stress proposes 10:00–10:10. Wind-down proposes 20:30–20:40, then 21:15–21:25 if rejected. Nothing overlaps a busy block or reuses a rejected gap.
4. In model mode, the eligible action or hold is allowed; mismatched actions, durations/windows, and unknown evidence IDs cannot bypass validation. Show at least one genuine model result if credentials are available, and report honestly if none was obtained.
5. A proposed block remains dashed/pending until This time works; confirmation makes it solid/accepted. Skip removes the block. Viewing the suggestion card highlights it without changing its state. Changing any context input clears the previous result.
6. Reload restores the latest saved review, including rejected gaps and acceptance state; Reset clears it. Only explicit Get suggestion submissions may make a model request.
7. Missing credentials or a failed request clearly identifies the scripted preview.

Deliver the runnable prototype, a short README, and a brief honest note on which checks were performed. Capture the category-change examples and one alternate-slot interaction for the proposal presentation. Stop when these checks pass; do not expand into the full implementation plan.
