import json

from aps_forma_issues.root_causes import SafetyRootCause


def test_members_are_plain_strings_matching_their_ids():
    assert SafetyRootCause.HUMAN_ERROR == "08afdebc-35fb-4cf4-9c3e-521906250108"
    assert isinstance(SafetyRootCause.HUMAN_ERROR, str)


def test_members_serialize_to_their_raw_id_not_the_enum_repr():
    body = {"rootCauseId": SafetyRootCause.HUMAN_FAILED_TO_IDENTIFY_UNSAFE_CONDITION}

    encoded = json.dumps(body)

    assert encoded == '{"rootCauseId": "4ea3583b-4d6c-4295-b3c2-77bb3079b6bb"}'


def test_all_members_have_unique_ids():
    ids = [member.value for member in SafetyRootCause]
    assert len(ids) == len(set(ids))
