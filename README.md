# Belfast Women in Tech Hub

An independent, static information page listing events, news, award winners and communities for women in tech in Belfast. Plain HTML, CSS and JavaScript, with no build step, hosted on GitHub Pages.

## How it works

| File | Purpose |
| --- | --- |
| `index.html` | The page: layout, styling and rendering code. |
| `data.json` | All hand-curated content: events, news, awards, groups and sources. |
| `events.auto.json` | Upcoming events listed automatically from organiser calendars. Don't edit by hand. |
| `images/` | Photos, referenced from `data.json` (`images/events/`, `images/groups/`). |
| `scripts/` | `update_events.py` and `feeds.json`, which fetch the calendar feeds. |
| `.github/workflows/update-events.yml` | Runs the script daily and commits any changes. |

Whether an event shows as upcoming, happening now or past is worked out in the visitor's browser from today's date, so it stays correct without any edit.

## Updating content

Edit `data.json`, commit and push. The site redeploys within a couple of minutes.

- **Event:** add an object to `events` with `id`, `title`, `org`, `start` (`YYYY-MM-DD`), `time`, `venue`, `note` and `url`. Optional: `end` for multi-day events, `approx: true` when only the month is known, `start: null` for date TBC.
- **News:** add to `news`, newest first (it is displayed in the order written).
- **Photo:** add `"image": "images/events/your-file.jpg"` and `"imageAlt": "description"` to any event, news item or group. Resize to about 1600px wide and strip metadata first.
- **Freshness:** bump `meta.dataCheckedDate` whenever you re-check the sources.

## Automatic event listing

A scheduled GitHub Action reads the calendar feeds in `scripts/feeds.json` (currently the Women In Tech Belfast Meetup iCal feed) and writes `events.auto.json`. An auto-listed event is hidden if a hand-written event on the same date has a matching title.

To add another organiser, add an entry to `scripts/feeds.json` (the feed must be iCal). Run it manually from the **Actions** tab, or locally with `python3 scripts/update_events.py`.

## Preview locally

The page loads its data with `fetch()`, which browsers block on `file://`, so serve the folder:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Notes

- Information is compiled from the public sources listed at the bottom of the page. Always check an organiser's own page before travelling to an event.
- Not affiliated with any organisation listed.
