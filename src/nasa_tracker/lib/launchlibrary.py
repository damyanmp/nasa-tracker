"""Artemis mission data from The Space Devs' Launch Library 2 (LL2).

LL2 is a community-maintained launch database (dates, status, crew). The free
tier allows ~15 requests/hour, so results are cached on disk for 6 hours and a
stale cache is reused if the API is unreachable or rate-limited.

Reference: https://ll.thespacedevs.com/docs/
"""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

LL2_ARTEMIS_URL = (
    "https://ll.thespacedevs.com/2.3.0/launches/"
    "?program=15&mode=detailed&limit=30&ordering=net"   # program 15 = Artemis
)
HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"

CACHE_TTL_S = 6 * 3600
_ARTEMIS_NAME_RE = re.compile(r"^Artemis [IVXLC]+$")

# Horizons IDs known up front; later Orions are resolved by COSPAR designator.
KNOWN_NAIF = {"Artemis I": -1023, "Artemis II": -1024}


def cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    d = Path(base) / "nasa-tracker"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_cache(name: str) -> tuple[Optional[Any], float]:
    """Return (data, age_seconds) or (None, inf)."""
    p = cache_dir() / name
    try:
        return json.loads(p.read_text()), time.time() - p.stat().st_mtime
    except Exception:
        return None, float("inf")


def _write_cache(name: str, data: Any) -> None:
    try:
        (cache_dir() / name).write_text(json.dumps(data))
    except Exception:
        pass   # cache is best-effort


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def window_label(net: Optional[datetime], precision: Optional[str]) -> str:
    """Human label for a launch NET given LL2's precision name."""
    if not net:
        return "TBD"
    p = (precision or "").lower()
    if p in ("second", "minute", "hour"):
        return net.strftime("%Y-%m-%d %H:%M UTC")
    if p == "day":
        return net.strftime("%Y-%m-%d")
    if p == "month":
        return net.strftime("%b %Y")
    if p.startswith("quarter"):
        return f"Q{(net.month - 1) // 3 + 1} {net.year}"
    if p.startswith("year half"):
        return f"{'H1' if net.month <= 6 else 'H2'} {net.year}"
    if p in ("year", "fiscal year"):
        return str(net.year)
    return f"~{net.strftime('%b %Y')} (est.)"


_ROLE_ABBR = {
    "commander": "CDR", "spacecraft commander": "CDR", "pilot": "PLT",
    "mission specialist": "MS",
}


def _crew(stage: dict) -> list[str]:
    out = []
    for c in stage.get("launch_crew") or []:
        a = c.get("astronaut") or {}
        role = ((c.get("role") or {}).get("role") or "")
        if "test device" in role.lower() or "indicator" in role.lower():
            continue   # Artemis I mannequins / plushies
        agency = (a.get("agency") or {}).get("abbrev") or ""
        tag = _ROLE_ABBR.get(role.lower(), role)
        if agency and agency != "NASA":
            tag = f"{tag}, {agency}" if tag else agency
        out.append(f"{a.get('name', '?')} ({tag})" if tag else a.get("name", "?"))
    return out


def parse_launches(results: list[dict], now: Optional[datetime] = None) -> list[dict]:
    """Turn LL2 launch records into plain mission dicts (JSON-serialisable)."""
    now = now or datetime.now(tz=timezone.utc)
    missions = []
    for r in results:
        # Far-future launches may have no mission record yet — fall back to
        # the launch name, e.g. "SLS Block 1B | Artemis VI".
        name = ((r.get("mission") or {}).get("name") or "").strip()
        if not name:
            name = (r.get("name") or "").split("|")[-1].strip()
        if not _ARTEMIS_NAME_RE.match(name):
            continue   # skip EFT-1, abort tests, Gateway etc.
        stage = (r.get("rocket") or {}).get("spacecraft_stage") or {}
        if isinstance(stage, list):
            stage = stage[0] if stage else {}
        net = _parse_dt(r.get("net"))
        precision = (r.get("net_precision") or {}).get("name")
        end = _parse_dt(stage.get("mission_end"))
        abbrev = ((r.get("status") or {}).get("abbrev") or "").lower()

        if abbrev in ("success", "in flight", "partial failure"):
            status = "completed" if end and end <= now else "active"
        elif abbrev == "failure":
            status = "failed"
        else:
            status = "upcoming"

        exact = (precision or "").lower() in ("second", "minute", "hour")
        crew = _crew(stage)
        spacecraft = (stage.get("spacecraft") or {}).get("name") or "Orion"
        missions.append({
            "name": name,
            "nickname": spacecraft + (f" — {stage['destination']}" if stage.get("destination") else ""),
            # Every Orion flight after Artemis I is crewed; crew may not be named yet.
            "crewed": bool(crew) or name != "Artemis I",
            "launch_utc": net.isoformat() if net and (status != "upcoming" or exact) else None,
            "splashdown_utc": end.isoformat() if end else None,
            "status": status,
            "crew": crew,
            "description": " ".join(((r.get("mission") or {}).get("description") or "").split()),
            "window": "" if status != "upcoming" else window_label(net, precision),
            "designator": r.get("launch_designator") or "",
        })
    return missions


async def _resolve_naif(client: httpx.AsyncClient, designators: set[str]) -> dict[str, int]:
    """Look up Horizons IDs for Orion spacecraft by COSPAR designator."""
    if not designators:
        return {}
    try:
        resp = await client.get(HORIZONS_API, params={
            "format": "text", "COMMAND": "'Orion'", "MAKE_EPHEM": "NO",
        }, timeout=15)
        text = resp.text
    except Exception:
        return {}
    found: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"^\s*(-\d+)\s+.*?\s(\d{4}-\d{3})[A-Z]\s", line)
        if m and m.group(2) in designators:
            found[m.group(2)] = int(m.group(1))
    return found


async def fetch_artemis(force: bool = False) -> tuple[Optional[list[dict]], str]:
    """Return (missions, source_note). missions is None if nothing is available."""
    cached, age = _read_cache("artemis.json")
    if cached is not None and age < CACHE_TTL_S and not force:
        return cached, "Launch Library 2 (cached)"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(LL2_ARTEMIS_URL, timeout=15)
            resp.raise_for_status()
            missions = parse_launches(resp.json().get("results", []))
            if not missions:
                raise ValueError("no Artemis missions in response")
            need = {m["designator"] for m in missions
                    if m["designator"] and m["name"] not in KNOWN_NAIF}
            resolved = await _resolve_naif(client, need)
        for m in missions:
            m["naif_id"] = KNOWN_NAIF.get(m["name"]) or resolved.get(m["designator"], 0)
        _write_cache("artemis.json", missions)
        return missions, "Launch Library 2"
    except Exception as e:
        if cached is not None:
            return cached, f"Launch Library 2 (offline cache, {age / 3600:.0f}h old — {type(e).__name__})"
        return None, f"Launch Library 2 unavailable ({type(e).__name__})"
