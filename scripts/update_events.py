#!/usr/bin/env python3
"""Fetch iCal feeds listed in scripts/feeds.json and write events.auto.json.

Hand-curated content stays in data.json; this file only holds auto-listed
upcoming events, and is regenerated from scratch on every run.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
LOCAL_TZ = ZoneInfo("Europe/London")
NOTE_MAX = 220


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "belfast-wit-hub-updater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text)


def unescape(v):
    return (v.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",")
             .replace("\\;", ";").replace("\\\\", "\\"))


def parse_events(text):
    events, cur = [], None
    for line in unfold(text).splitlines():
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            head, value = line.split(":", 1)
            name, *params = head.split(";")
            cur[name.upper()] = (value, dict(p.split("=", 1) for p in params if "=" in p))
    return events


def to_local(value, params):
    """Return (date, 'HH:MM' or '') in Europe/London."""
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value, "%Y%m%d").date(), ""
    if value.endswith("Z"):
        dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
    else:
        dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
        dt = dt.replace(tzinfo=ZoneInfo(params["TZID"]) if "TZID" in params else LOCAL_TZ).astimezone(LOCAL_TZ)
    return dt.date(), dt.strftime("%H:%M")


def safe_url(u):
    return u if re.match(r"^https?://", u or "", re.I) else ""


def convert(ev, feed):
    if "DTSTART" not in ev or "SUMMARY" not in ev:
        return None
    start, time = to_local(*ev["DTSTART"])
    out = {
        "id": "auto-" + re.sub(r"[^a-z0-9]+", "-", ev.get("UID", ("", {}))[0].lower()).strip("-"),
        "title": unescape(ev["SUMMARY"][0]),
        "org": feed["org"],
        "start": start.isoformat(),
        "time": time,
        "venue": unescape(ev["LOCATION"][0]).strip() if ev.get("LOCATION") and ev["LOCATION"][0].strip() else feed.get("defaultVenue", ""),
        "url": safe_url(ev.get("URL", ("", {}))[0]) or safe_url(feed.get("pageUrl") or feed["url"]),
        "auto": True,
    }
    if "DTEND" in ev:
        end, _ = to_local(*ev["DTEND"])
        if ev["DTEND"][1].get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", ev["DTEND"][0]):
            end -= timedelta(days=1)
        if end > start:
            out["end"] = end.isoformat()
    desc = unescape(ev.get("DESCRIPTION", ("", {}))[0]).strip()
    desc = re.sub(r"\s+", " ", re.sub(r"https?://\S+", "", desc)).strip()
    if len(desc) > NOTE_MAX:
        desc = desc[:NOTE_MAX].rsplit(" ", 1)[0] + "…"
    out["note"] = ("Listed automatically from the organiser’s calendar. " + desc).strip()
    return out


def main():
    feeds = json.loads((ROOT / "scripts" / "feeds.json").read_text())["feeds"]
    events, failed = [], False
    for feed in feeds:
        try:
            text = fetch(feed["url"])
            if "BEGIN:VCALENDAR" not in text:
                raise ValueError("response is not an iCal calendar")
            for ev in parse_events(text):
                item = convert(ev, feed)
                if item:
                    events.append(item)
        except Exception as exc:
            failed = True
            print("FAILED " + feed["name"] + ": " + str(exc), file=sys.stderr)
    if failed:
        sys.exit(1)
    events.sort(key=lambda e: (e["start"], e["title"]))
    out = {"events": events}
    (ROOT / "events.auto.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print("wrote %d event(s)" % len(events))


if __name__ == "__main__":
    main()
