from datetime import datetime, timezone

from nasa_tracker.lib.launchlibrary import parse_launches, window_label

NOW = datetime(2026, 11, 11, tzinfo=timezone.utc)


def _launch(name, net, precision, status, end=None, crew=()):
    return {
        "mission": {"name": name, "description": "desc"},
        "net": net,
        "net_precision": {"name": precision} if precision else None,
        "status": {"abbrev": status},
        "launch_designator": None,
        "rocket": {"spacecraft_stage": {
            "mission_end": end,
            "destination": "Low Earth Orbit",
            "spacecraft": {"name": "Orion 004"},
            "launch_crew": [
                {"astronaut": {"name": n, "agency": {"abbrev": a}}, "role": {"role": r}}
                for n, a, r in crew
            ],
        }},
    }


def test_window_labels():
    d = datetime(2027, 6, 30, tzinfo=timezone.utc)
    assert window_label(d, "Month") == "Jun 2027"
    assert window_label(d, "Year Half 1") == "H1 2027"
    assert window_label(d, "Quarter 2") == "Q2 2027"
    assert window_label(d, None) == "~Jun 2027 (est.)"
    assert window_label(None, "Month") == "TBD"


def test_status_mapping_and_filtering():
    results = [
        _launch("EFT-1", "2014-12-05T12:05:00Z", "Second", "Success"),
        _launch("Artemis II", "2026-04-01T22:35:12Z", "Second", "Success",
                end="2026-04-11T00:07:27Z"),
        _launch("Artemis III", "2027-06-30T00:00:00Z", "Month", "TBD",
                crew=[("Luca Parmitano", "ESA", "Pilot"), ("Andre Douglas", "NASA", "Mission Specialist")]),
        _launch("Artemis IV", "2028-01-10T00:00:00Z", "Day", "Success"),  # launched, no end yet
    ]
    ms = {m["name"]: m for m in parse_launches(results, now=NOW)}
    assert "EFT-1" not in ms
    assert ms["Artemis II"]["status"] == "completed"
    a3 = ms["Artemis III"]
    assert a3["status"] == "upcoming" and a3["launch_utc"] is None and a3["window"] == "Jun 2027"
    assert a3["crew"] == ["Luca Parmitano (PLT, ESA)", "Andre Douglas (MS)"]
    assert ms["Artemis IV"]["status"] == "active"


def test_mannequins_are_not_crew():
    r = _launch("Artemis I", "2022-11-16T06:47:44Z", "Second", "Success",
                end="2022-12-11T17:40:30Z",
                crew=[("Commander Moonikin Campos", "NASA", "Anthropomorphic Test Device")])
    (m,) = parse_launches([r], now=NOW)
    assert m["crew"] == [] and m["crewed"] is False


def test_missing_mission_record_uses_launch_name():
    r = _launch("x", "2030-09-30T00:00:00Z", None, "TBD")
    r["mission"] = None
    r["name"] = "SLS Block 1B | Artemis VI"
    (m,) = parse_launches([r], now=NOW)
    assert m["name"] == "Artemis VI" and m["crewed"] is True and m["window"] == "~Sep 2030 (est.)"
