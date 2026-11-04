from agent_compaction import task3


def test_override_owner_in_another_letter_case_applies_the_change_but_fails_strict():
    case = task3.scenario("override", 114)
    want = task3.expected(case)
    grade = task3.grade(case, {"incidents": want["incidents"], "owner": want["owner"].title()})
    assert grade["change_applied"] and not grade["owner"] and not grade["strict"]


def test_override_owner_of_another_incident_does_not_apply_the_change():
    case = task3.scenario("override", 106)
    want = task3.expected(case)
    grade = task3.grade(case, {"incidents": want["incidents"], "owner": "ece"})
    assert want["owner"] == "baran" and not grade["change_applied"]
