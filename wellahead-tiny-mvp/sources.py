"""Read-only saved health observations and a narrow primary-calendar FreeBusy read."""
import hashlib
import json
import math
import os
import re
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

STREAMS = {
    "sleep": "Sleep", "steps": "Steps", "heart-rate": "Heart rate",
    "daily-heart-rate-variability": "Daily HRV", "daily-resting-heart-rate": "Resting heart rate",
    "sedentary-period": "Sedentary periods", "active-zone-minutes": "Active-zone minutes",
    "daily-respiratory-rate": "Breathing rate", "daily-oxygen-saturation": "Oxygen saturation",
    "daily-sleep-temperature-derivations": "Sleep temperature", "heart-rate-variability": "Granular HRV",
    "exercise": "Exercise",
}


def number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) and value >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires an offset")
    return parsed


def civil_day(value):
    return date(int(value["year"]), int(value["month"]), int(value["day"])).isoformat()


def health_sample(configured_path):
    """Only return a whitelist of observations and aggregate access metadata, never raw payloads."""
    if not configured_path:
        return {"status": "unconfigured", "cards": [], "streams": []}
    try:
        path = Path(configured_path)
        if not path.is_absolute():
            raise ValueError("An absolute path is required")
        if path.is_dir():
            path = path / "combined-responses.json"
        data = json.loads(path.read_text())
        entries = data.get("results", [data] if "response" in data else [])
        if not isinstance(entries, list) or not entries:
            raise ValueError("Unrecognized saved response format")
        captured = None
        match = re.fullmatch(r"api-samples-(\d{8}T\d{12}Z)", path.parent.name)
        if match:
            captured = datetime.strptime(match[1], "%Y%m%dT%H%M%S%fZ").replace(tzinfo=UTC).isoformat()
        streams, candidates = [], {"sleep": [], "rhr": [], "hrv": []}
        for entry in entries:
            stream = entry.get("stream")
            if stream not in STREAMS:
                continue
            response = entry.get("response", {})
            points = response.get("dataPoints", [])
            status = entry.get("http_status")
            retrieved = entry.get("retrieved_at", data.get("retrieved_at"))
            try:
                retrieved = instant(retrieved).isoformat() if retrieved else None
            except (ValueError, TypeError, AttributeError):
                retrieved = None
            streams.append({"stream": STREAMS[stream], "http_status": int(status) if str(status).isdigit() else None,
                            "count": len(points), "paginated": bool(response.get("nextPageToken"))})
            if str(status) != "200":
                continue
            for point in points:
                kind, value, source_date, source_offset = None, None, None, None
                if stream == "sleep":
                    record = point.get("sleep", {})
                    if record.get("metadata", {}).get("mainSleep") is not True:
                        continue
                    interval = record.get("interval", {})
                    end = instant(interval["endTime"])
                    offset_text = interval.get("endUtcOffset")
                    offset = None
                    # Signed source offsets must be retained; never apply the laptop timezone.
                    if offset_text is not None:
                        offset = float(offset_text.removesuffix("s"))
                        if not math.isfinite(offset) or abs(offset) > 86400:
                            raise ValueError("Invalid source offset")
                    civil = interval.get("civilEndTime", {}).get("date")
                    source_date = civil_day(civil) if civil else ((end.astimezone(UTC)+timedelta(seconds=offset)).date().isoformat() if offset is not None else end.date().isoformat())
                    source_offset = offset_text or end.strftime("%z")
                    kind = "sleep"
                    value = number(record.get("summary", {}).get("minutesAsleep")) if record.get("metadata", {}).get("processed") is True else None
                elif stream in {"daily-resting-heart-rate", "daily-heart-rate-variability"}:
                    key, field, kind = ("dailyRestingHeartRate", "beatsPerMinute", "rhr") if stream == "daily-resting-heart-rate" else ("dailyHeartRateVariability", "averageHeartRateVariabilityMilliseconds", "hrv")
                    record = point[key]
                    source_date = civil_day(record["date"])
                    value = number(record.get(field))
                if kind:
                    candidates[kind].append({"value": value, "source_date": source_date,
                        "source_offset": source_offset, "retrieved_at": retrieved,
                        "evidence_id": f"health:{kind}:{source_date}"})
        cards = []
        for kind, label, unit in [("sleep", "Main sleep", "min asleep"), ("rhr", "Resting heart rate", "bpm"), ("hrv", "Daily HRV", "ms")]:
            records = candidates[kind]
            latest = max(records, key=lambda item: item["source_date"]) if records else {}
            cards.append({"kind": kind, "label": label, "unit": unit, **latest,
                          "date_count": len({r['source_date'] for r in records})})
        if not streams:
            raise ValueError("No supported streams")
        return {"status": "loaded", "cards": cards, "streams": streams, "captured_at": captured,
                "identity": hashlib.sha256(path.read_bytes()).hexdigest()[:16]}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return {"status": "invalid", "cards": [], "streams": []}


def calendar_ranges(target_day, timezone):
    zone = ZoneInfo(timezone)
    day = date.fromisoformat(target_day)
    ranges = []
    for start, end in [(9, 17), (20, 22)]:
        left, right = [datetime.combine(day, time(hour), zone) for hour in (start, end)]
        if any(value.astimezone(UTC).astimezone(zone).replace(tzinfo=None) != value.replace(tzinfo=None) for value in [left, right]):
            raise ValueError("Invalid local planning window")
        ranges.append({"start": left.isoformat(), "end": right.isoformat()})
    return ranges


def refresh_calendar(token, target_day, timezone, *, client=None):
    if not token:
        return None, "Calendar token not configured"
    try:
        ranges = calendar_ranges(target_day, timezone)
        intervals = []
        def query(http):
            for bounds in ranges:
                response = http.post("https://www.googleapis.com/calendar/v3/freeBusy",
                    headers={"Authorization": f"Bearer {token}"}, json={"timeMin": bounds["start"],
                        "timeMax": bounds["end"], "timeZone": timezone, "items": [{"id": "primary"}]})
                if response.status_code != 200:
                    raise ValueError("Calendar access denied or request failed")
                data = response.json()
                if instant(data["timeMin"]) > instant(bounds["start"]) or instant(data["timeMax"]) < instant(bounds["end"]):
                    raise ValueError("Incomplete query coverage")
                calendars = data["calendars"]
                primary = calendars.get("primary")
                if primary is None or primary.get("errors") or "busy" not in primary:
                    raise ValueError("Calendar result unavailable")
                for item in primary["busy"]:
                    left, right = instant(item["start"]), instant(item["end"])
                    if right <= left:
                        raise ValueError("Invalid interval")
                    left, right = max(left, instant(bounds["start"])), min(right, instant(bounds["end"]))
                    if left < right:
                        intervals.append([left.astimezone(ZoneInfo(timezone)), right.astimezone(ZoneInfo(timezone))])
        if client is not None:
            query(client)
        else:
            with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as http:
                query(http)
        merged = []
        for left, right in sorted(intervals):
            if merged and left <= merged[-1][1]:
                merged[-1][1] = max(right, merged[-1][1])
            else:
                merged.append([left, right])
        snapshot = {"status": "success", "target_day": target_day, "timezone": timezone,
                    "requested_ranges": ranges, "busy": [{"start": a.isoformat(), "end": b.isoformat()} for a,b in merged],
                    "retrieved_at": datetime.now(UTC).isoformat()}
        snapshot["identity"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()[:16]
        return snapshot, None
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return None, "Calendar unavailable — availability unknown"


def save_snapshot(path, snapshot):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(".tmp")
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as stream:
        json.dump(snapshot, stream, indent=2)
    temporary.replace(path)


def load_snapshot(path, target_day, timezone):
    try:
        value = json.loads(path.read_text())
        expected = {"status", "target_day", "timezone", "requested_ranges", "busy", "retrieved_at", "identity"}
        if set(value) != expected or value["status"] != "success" or value["target_day"] != target_day or value["timezone"] != timezone:
            return None
        if value["requested_ranges"] != calendar_ranges(target_day, timezone):
            return None
        instant(value["retrieved_at"])
        for bounds in value["busy"]:
            if set(bounds) != {"start", "end"} or instant(bounds["start"]) >= instant(bounds["end"]):
                return None
            if not any(instant(r['start']) <= instant(bounds['start']) < instant(bounds['end']) <= instant(r['end']) for r in value['requested_ranges']):
                return None
        unsigned = {k:v for k,v in value.items() if k != 'identity'}
        if hashlib.sha256(json.dumps(unsigned, sort_keys=True).encode()).hexdigest()[:16] != value['identity']:
            return None
        return value
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def calendar_context(snapshot):
    from assistant import intervals
    zone = ZoneInfo(snapshot["timezone"])
    values = []
    for bounds in snapshot["busy"]:
        start, end = instant(bounds["start"]).astimezone(zone), instant(bounds["end"]).astimezone(zone)
        # Round outward so seconds never create a false free minute.
        left = start.hour*60+start.minute
        right = end.hour*60+end.minute+(1 if end.second or end.microsecond else 0)
        values.append([f"{left//60:02d}:{left%60:02d}", f"{right//60:02d}:{right%60:02d}"])
    return {"daytime": intervals(["09:00", "17:00"], values, "daytime"),
            "evening": intervals(["20:00", "22:00"], values, "evening")}
