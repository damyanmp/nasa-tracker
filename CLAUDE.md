# nasa-tracker — Claude Code Context

## Project

Standalone CLI for NASA / space mission tracking, extracted from `pentagon-management/infrastructure/cli/` on 2026-04-05.

**Location:** wherever you cloned it (e.g. `~/repos/nasa-tracker/`)

## Structure

```
nasa-tracker/
├── pyproject.toml
├── .python-version          (3.12)
└── src/nasa_tracker/
    ├── nasa.py              — CLI entry point (Typer + Rich + Textual TUI)
    └── lib/
        ├── horizons.py      — JPL Horizons API client (spacecraft ephemeris)
        └── worldmap.py      — Natural Earth land mask, Unicode half-block renderer
```

## Running

```bash
# Install
uv venv && uv pip install -e "."

# Commands
nasa                    # TUI dashboard
nasa iss                # ISS position + world map
nasa artemis status     # Current/latest Artemis mission telemetry
nasa update             # Reinstall latest from GitHub via uv
nasa probes             # Deep space probe fleet
nasa rovers             # Mars rover status
nasa launches           # Upcoming launches
```

## Data Sources

| Source | Used for |
|---|---|
| JPL Horizons API (`ssd.jpl.nasa.gov/api/horizons.api`) | Spacecraft position/velocity vectors |
| open-notify.org | ISS real-time lat/lon (its crew endpoint went stale in 2024 — don't use) |
| corquaid.github.io/international-space-station-APIs | Current ISS crew + expedition number |
| Launch Library 2 (`ll.thespacedevs.com`, program 15) | Artemis missions: dates, status, crew. Free tier ~15 req/h → disk cache `~/.cache/nasa-tracker/artemis.json`, 6h TTL, stale cache reused offline |
| rocketlaunch.live | Upcoming launch schedule |

## Key Design Decisions

- **Horizons queries:** Fetch 24h window at 1h resolution, pick closest epoch to `now` — avoids URL-encoding issues with colons in time strings.
- **Rate limiting:** `_HORIZONS_SEM = asyncio.Semaphore(3)` + 0.5s stagger between slot releases — prevents JPL from blocking burst requests on TUI startup.
- **Cache TTLs:** Artemis 2 min, ISS 1 min, launches 5 min, probes/rovers 24h (effectively once per session — they don't change meaningfully).
- **World map:** `worldmap.py` embeds a Natural Earth 50m land mask (zlib+base64, ~5KB). Renders with Unicode half-block chars (`▀▄█`) at configurable width. No external dependencies.

## Naming Conventions

- Scripts/modules: `snake_case.py`
- No documentation files unless explicitly requested

## Safety Rules

- **Ask before every change** — no exceptions
- **Never push to git** without showing diff and getting approval

## Hand-maintained data (review when refreshing)

Artemis data is live from Launch Library 2 (`lib/launchlibrary.py`);
`ARTEMIS_MISSIONS` in `nasa.py` is only the offline fallback. Orion Horizons IDs
are resolved automatically by COSPAR designator once JPL publishes them.

`PROBES` and `ROVERS` do NOT update themselves (no good live source for mission
status). Check them against NASA before releasing.
Verify any new NAIF ID with a Horizons query ("Target body name" line) — e.g.
Lucy is -49 (-234 is STEREO-A).
