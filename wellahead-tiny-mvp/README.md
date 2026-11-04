# WellAhead — Tomorrow, made manageable

A local Streamlit page for exploring how an example day, wearable context, and expected stress shape a small planning suggestion. The larger `wellahead-mvp/` application is unchanged.

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

Set `GEMINI_API_KEY` privately in ignored `.env` for model responses. `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite`. Each explicit **Get suggestion** or **Get an answer** click makes one request, with a 15-second timeout and no automatic retry. Set `WELLAHEAD_SCRIPTED=true` or choose **Scripted mode** in Settings to use local responses without model calls. The UI labels AI and scripted results.

## Walkthrough

Choose **Packed day** in **Settings**, then **Usual sleep / Low** and **Get suggestion**. Change the calendar schedule to **Lighter day** in Settings and submit again to show the different action category. Choose **Packed day / High** to see a ten-minute quiet pause at 12:30; **Find another gap** moves it to 15:00. Choose **Shorter sleep / Moderate** to see a twenty-minute evening wind-down. Actions last 10–20 minutes. **This time works** records the choice locally; no event is written to Calendar. The page derives the Packed/Lighter label from the selected calendar's scheduled minutes.

The packed 09:00–17:00 window has 7h 35m scheduled and 0h 25m free. The evening window has 0h 45m scheduled and 1h 15m free. The page shows step medians (7,500 → 4,500), selected sleep (6h or 7h versus 7h usual), resting heart rate (75 bpm), and HRV (24.55 ms). These fixed example values are planning context, not scores or health interpretations. They are the only wearable-like values sent with an explicit model request. The private health sample and Calendar APIs are not loaded or queried by this UI.

To demonstrate free-text input, enter: **“I’m expecting a stressful day. What small break could fit my schedule?”** Select **Get an answer** to receive a short response using the displayed schedule and context. Gemini does not provide diagnosis or medical advice.

## Local state and privacy

`var/latest-review.json` stores only the most recent selected scenario and review state. It is ignored by Git. **Start over** clears the review. Never commit `.env`, credentials, private health responses, or local state files.
