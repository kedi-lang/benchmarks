"""Task 1 — rules early, work late.

Rules come in the first message; eight noisy logs each hide one incident line. The answer needs
the rules and every incident fact, read long before the end. Deterministic per seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SERVICES = ["billing", "search", "legacy", "auth", "payments", "ingest"]
OWNERS = ["ayse", "mehmet", "zeynep", "can", "elif", "deniz", "baran", "ece"]
LOG_COUNT = 8
NOISE_LINES = 260


@dataclass(frozen=True)
class Incident:
    log: str
    incident_id: str
    service: str
    severity: int
    owner: str


def incidents(seed: int) -> list[Incident]:
    rng = random.Random(seed)
    severities = rng.sample(range(1, 10), LOG_COUNT)
    services = [rng.choice(SERVICES) for _ in range(LOG_COUNT)]
    services[rng.randrange(LOG_COUNT)] = "legacy"  # at least one ignored incident
    return [
        Incident(
            log=f"log_{i + 1}",
            incident_id=f"inc-{rng.randint(1000, 9999)}",
            service=services[i],
            severity=severities[i],
            owner=OWNERS[i],
        )
        for i in range(LOG_COUNT)
    ]


def log_text(seed: int, name: str) -> str:
    found = {item.log: item for item in incidents(seed)}
    if name not in found:
        return f"No log named {name!r}."
    item = found[name]
    rng = random.Random(f"{seed}-{name}")
    lines = [
        f"{i:04d} {rng.choice(SERVICES)} worker-{rng.randint(1, 30)} "
        f"status={rng.choice(['ok', 'retry', 'slow', 'ok', 'ok'])} latency_ms={rng.randint(3, 1500)} "
        f"trace={rng.getrandbits(40):010x}"
        for i in range(NOISE_LINES)
    ]
    lines.insert(
        rng.randrange(NOISE_LINES),
        f"INCIDENT {item.incident_id} service={item.service} severity={item.severity} owner={item.owner}",
    )
    return "\n".join(lines)


TASK = """\
You are auditing service logs. Rules for the whole task:
1. Ignore every incident from service `legacy`.
2. Report incident ids in UPPERCASE.
3. `owner` is the owner of the reported incident with the highest severity.
Read log_1 through log_8 with read_log, one call at a time, in order. Each log contains one
INCIDENT line among routine lines. After reading all eight, give the final report."""


def expected(seed: int) -> dict:
    reported = [i for i in incidents(seed) if i.service != "legacy"]
    top = max(reported, key=lambda i: i.severity)
    return {"incidents": sorted(i.incident_id.upper() for i in reported), "owner": top.owner}


def grade(seed: int, answer: dict) -> dict:
    want = expected(seed)
    got = sorted(str(x) for x in answer.get("incidents", []))
    return {
        "incidents_exact": got == want["incidents"],
        "uppercase": all(x == x.upper() for x in got),
        "legacy_excluded": not any(
            x.lower() in {i.incident_id for i in incidents(seed) if i.service == "legacy"} for x in got
        ),
        "owner": answer.get("owner") == want["owner"],
        "found": len(set(got) & set(want["incidents"])),
        "want": len(want["incidents"]),
    }
