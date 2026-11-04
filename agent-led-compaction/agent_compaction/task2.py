"""Edge-case tasks: evolving state, a rule introduced mid-task, long horizons, an oversized tool result.

Built to break compaction, not to flatter it:
- UPDATE lines change an earlier incident's severity (the final owner depends on the latest value),
- RETRACT lines withdraw an earlier incident (it must not be reported),
- a POLICY CHANGE line in the middle adds a rule that is *not* in the protected prompt, so it survives
  only if compaction keeps it,
- `long` needs many compactions; `big` has one log larger than the compaction threshold.
Deterministic per (variant, seed).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

SERVICES = ["billing", "search", "auth", "payments", "ingest", "storage"]
OWNERS = [
    "ayse", "mehmet", "zeynep", "can", "elif", "deniz", "baran", "ece", "selin", "emre",
    "irem", "kerem", "nil", "ozan", "pinar", "rana", "sarp", "tuna", "umut", "yigit",
]


@dataclass(frozen=True)
class Variant:
    name: str
    logs: int
    noise_lines: int = 260
    evolving: bool = True
    big_log: int | None = None  # 1-based index of the oversized log
    big_lines: int = 1300


VARIANTS = {
    "rev": Variant("rev", logs=8),
    "long": Variant("long", logs=20),
    "big": Variant("big", logs=8, evolving=False, big_log=4),
}


@dataclass(frozen=True)
class Incident:
    log: int
    incident_id: str
    service: str
    severity: int
    owner: str


@dataclass
class Scenario:
    variant: Variant
    seed: int
    incidents: list[Incident]
    extra_lines: dict[int, list[str]] = field(default_factory=dict)  # log -> UPDATE/RETRACT/POLICY lines
    updates: dict[str, int] = field(default_factory=dict)
    retracted: set[str] = field(default_factory=set)
    policy_service: str | None = None
    policy_log: int | None = None


def scenario(variant_name: str, seed: int) -> Scenario:
    variant = VARIANTS[variant_name]
    rng = random.Random(f"{variant_name}-{seed}")
    n = variant.logs
    severities = rng.sample(range(1, 9), min(n, 8)) + [rng.randint(1, 8) for _ in range(n - min(n, 8))]
    services = [rng.choice(SERVICES) for _ in range(n)]
    services[rng.randrange(n)] = "legacy"
    ids = rng.sample(range(1000, 9999), n)
    incidents = [
        Incident(i + 1, f"inc-{ids[i]}", services[i], severities[i], OWNERS[i % len(OWNERS)])
        for i in range(n)
    ]
    result = Scenario(variant, seed, incidents)
    if not variant.evolving:
        return result

    half = n // 2
    # The mid-task policy targets a service that occurs both before and after it.
    result.policy_log = half + 1
    result.policy_service = "search"
    for index in (rng.randrange(0, half), rng.randrange(half, n)):
        if incidents[index].service != "legacy":
            incidents[index] = Incident(**{**incidents[index].__dict__, "service": "search"})

    def reportable(i: Incident) -> bool:
        return i.service not in {"legacy", "search"}

    early = [i for i in incidents[:half] if reportable(i)]
    # Promote an early incident to the top severity in a late log; retract another one in the last log.
    promoted = rng.choice(early)
    retracted = rng.choice([i for i in incidents[: n - 1] if reportable(i) and i is not promoted])
    late = [log for log in range(half + 2, n + 1)] or [n]
    result.updates[promoted.incident_id] = 10
    result.retracted.add(retracted.incident_id)
    result.extra_lines.setdefault(rng.choice(late), []).append(
        f"UPDATE {promoted.incident_id} severity=10 (re-triaged)"
    )
    result.extra_lines.setdefault(n, []).append(
        f"RETRACT {retracted.incident_id} (false alarm, do not report)"
    )
    result.extra_lines.setdefault(result.policy_log, []).append(
        "POLICY CHANGE: from now on, also ignore every incident from service `search`, "
        "including incidents already read."
    )
    return result


def log_text(case: Scenario, name: str) -> str:
    try:
        index = int(name.removeprefix("log_"))
    except ValueError:
        return f"No log named {name!r}."
    if not 1 <= index <= case.variant.logs:
        return f"No log named {name!r}."
    item = case.incidents[index - 1]
    rng = random.Random(f"{case.variant.name}-{case.seed}-{name}")
    count = case.variant.big_lines if index == case.variant.big_log else case.variant.noise_lines
    lines = [
        f"{i:04d} {rng.choice(SERVICES)} worker-{rng.randint(1, 30)} "
        f"status={rng.choice(['ok', 'retry', 'slow', 'ok', 'ok'])} latency_ms={rng.randint(3, 1500)} "
        f"trace={rng.getrandbits(40):010x}"
        for i in range(count)
    ]
    special = [
        f"INCIDENT {item.incident_id} service={item.service} severity={item.severity} owner={item.owner}",
        *case.extra_lines.get(index, []),
    ]
    for line in special:
        lines.insert(rng.randrange(len(lines)), line)
    return "\n".join(lines)


def task_text(case: Scenario) -> str:
    n = case.variant.logs
    return f"""\
You are auditing service logs. Rules for the whole task:
1. Ignore every incident from service `legacy`.
2. Report incident ids in UPPERCASE, ids only.
3. `owner` is the owner of the reported incident with the highest current severity.
Read log_1 through log_{n} with read_log, one call at a time, in order. Each log contains one
INCIDENT line among routine lines, and may contain UPDATE, RETRACT or POLICY CHANGE lines that change
earlier information; the final report must reflect the latest state. After reading all {n}, give the
final report."""


def expected(case: Scenario) -> dict:
    ignored = {"legacy"} | ({case.policy_service} if case.policy_service else set())
    reported = [
        i for i in case.incidents if i.service not in ignored and i.incident_id not in case.retracted
    ]
    severity = {i.incident_id: case.updates.get(i.incident_id, i.severity) for i in reported}
    top = max(reported, key=lambda i: (severity[i.incident_id], -i.log))
    return {"incidents": sorted(i.incident_id.upper() for i in reported), "owner": top.owner}


def grade(case: Scenario, answer: dict) -> dict:
    import re

    want = expected(case)
    raw = [str(x) for x in answer.get("incidents", [])]
    ids = sorted({m.upper() for x in raw for m in re.findall(r"inc-\d+", x, re.IGNORECASE)})
    by_id = {i.incident_id.upper(): i for i in case.incidents}
    return {
        "strict": sorted(raw) == want["incidents"] and answer.get("owner") == want["owner"],
        "lenient": ids == want["incidents"] and answer.get("owner") == want["owner"],
        "owner": answer.get("owner") == want["owner"],
        "missing": len(set(want["incidents"]) - set(ids)),
        "retracted_reported": sum(1 for x in ids if x.lower() in case.retracted),
        "policy_violations": sum(
            1 for x in ids if x in by_id and by_id[x].service == case.policy_service
        ),
        "legacy_reported": sum(1 for x in ids if x in by_id and by_id[x].service == "legacy"),
        "format_ok": raw == ids or sorted(raw) == ids,
    }
