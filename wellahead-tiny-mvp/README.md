# WellAhead — Tomorrow, made manageable

A single local Streamlit page combines a day calendar, recorded wearable context, and self-reported expected stress into one optional suggestion. The calendar uses fixed inputs; no wearable or Calendar API is connected. The larger application remains unchanged.

## Run

Use Python 3.12 or newer:

```sh
cd wellahead-tiny-mvp
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
cp .env.example .env
streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Direct dependencies are in `requirements.txt`; `requirements.lock.txt` records the versions checked for this prototype. Open the local URL printed by Streamlit.

Set `GEMINI_API_KEY` privately in `.env` to use Gemini. `GEMINI_MODEL` defaults to the team's configured `gemini-3.5-flash-lite`; exported environment variables take precedence. Credentials are not copied from the larger app. With **Scripted mode** off, each explicit **Get suggestion** click makes one SDK request, with a 15-second request timeout and automatic retries disabled. Other controls and reruns never call the model.

For recording, check **Scripted mode** or set `WELLAHEAD_SCRIPTED=true`. Results are labeled **AI suggestion** or **Scripted preview**. Missing credentials, provider failure, or invalid output shows **AI unavailable — showing a scripted preview**. Invalid model output is rejected before generating that labeled fallback. The prompt limits claims, but schema checks do not guarantee semantic safety of generated wording.

## Recording path

1. Choose **Packed day**, **Usual sleep**, and **Low** stress. Get a two-minute screen break at 12:30. Switch to **Lighter day** and resubmit to show a ten-minute walk at 10:00.
2. Choose **Packed day** and **High** stress. A five-minute quiet pause starts at 12:30. **Find another gap** moves the same action to 15:00. Rejecting both gaps removes the draft, without moving it into the evening.
3. Choose **Shorter sleep** and **Moderate** stress. A ten-minute wind-down appears in the evening strip at 20:30. Reject that gap to move to 21:15.
4. Use **View suggestion** to highlight the card. **This time works** makes the block solid and records acceptance. **Skip** removes it. Neither writes to an external calendar.
5. **Not sure** holds without another question. Changing any context control clears the previous result and acceptance until resubmission.

The five fixed actions belong to Movement, Screen break, Quiet recovery, and Sleep routine. The transparent priority is Not sure → hold; High → quiet pause; otherwise Shorter sleep → evening wind-down; otherwise Low/Packed → screen break; Low/Lighter → ten-minute walk; Moderate → five-minute walk. No fitting gap means hold. Action duration and allowed window are fixed; neither the model nor an alternate-slot request may change them.

Daytime totals are 455 minutes (Packed) and 180 minutes (Lighter), with 45 evening busy minutes separately. Step medians stay at 7,500 and 4,500; sleep switches between seven and six recorded hours against a usual seven. There is no sleep-analysis pipeline or inferred stress score. Priority, eligibility, and placement are deterministic design choices; the LLM can choose only the eligible action or hold and write its explanation. These rules are not claimed to be medically optimal.

## Persistence and reset

Ignored `var/latest-review.json` stores only the latest fixture version, review date, scenario, sleep context, answer, validated decision/action, evidence, explanation, processing mode, current slot, rejected gap IDs, and state. Reload restores rejected gaps and acceptance without another model request. **Start over** removes the file and clears the screen. Old fixture versions are ignored. This is one local file shared by browser sessions, not multi-user storage.

Each alternate request rejects the entire current gap and advances chronologically within that action's window. Placement text is generated from the current slot; the model cannot put precise times into its explanation.

## Completion checks — 2026-11-04

- Checked all 16 day/sleep/stress combinations against the six policy examples, plus fixed medians, sleep values, daytime/evening totals, and interval subtraction.
- Checked every action's duration and window, all untried-gap transitions and exhaustion, no-gap holds, and persistence/restore. Mismatched actions, extra duration fields, missing branch evidence, and unknown evidence IDs failed validation.
- Chromium checked category/duration changes, exact daytime and evening placements, rejected gaps, pending/accepted styling, highlight, context invalidation, reload, skip, missing-key fallback, and reset. No comprehensive testing framework was added.
- One real Gemini check for Packed day + Shorter sleep + Moderate stress used only fictional inputs and the existing private key. It returned HTTP 504. **No genuine model result was obtained for this revision**; the clearly labeled fallback worked. No local model was loaded.
- Updated presentation captures are in `screenshots/`: `packed-low.png`, `lighter-low.png`, `high-first.png`, `high-alternate.png`, `wind-down.png`, `wind-down-alternate.png`, and `not-sure.png`. These are scripted results.

UI copy is deliberately concise, following the user's explicit direction to remove repeated prototype/disclaimer text. The underlying data and real-model boundary remain documented here. This build stops at the proposal interaction and does not demonstrate real integrations or health benefit.
