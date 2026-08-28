"""Preset root causes for `IssueInput.root_cause_id`.

These are Autodesk's out-of-the-box "Safety" root cause category
"""

from __future__ import annotations

from enum import Enum

SAFETY_CATEGORY_ID = "93d1b9cb-deb0-4166-9a48-5f0227feaacb"


class SafetyRootCause(str, Enum):
    """Root causes under Autodesk's "Safety" category.

    Members are `str` subclasses, so they're usable directly wherever a
    plain `root_cause_id` string is expected:

        from aps_forma_issues import IssueInput, SafetyRootCause

        IssueInput(..., root_cause_id=SafetyRootCause.HUMAN_ERROR)
    """

    EQUIPMENT_IMPROPER_EQUIPMENT = "5ef898ac-b931-4e16-9038-9d2f2a2ab0cb"
    EQUIPMENT_IMPROPER_MAINTENANCE = "60665f4e-dc28-4f7e-9ac6-149995179d61"
    EQUIPMENT_LACK_OF_INSPECTION = "d8b0077b-e6b4-49c5-a208-987706b70b68"
    HUMAN_FAILED_TO_IDENTIFY_UNSAFE_CONDITION = "4ea3583b-4d6c-4295-b3c2-77bb3079b6bb"
    HUMAN_FATIGUE = "426e7b91-4790-4650-9749-47482463ca44"
    HUMAN_ERROR = "08afdebc-35fb-4cf4-9c3e-521906250108"
    HUMAN_IGNORANCE_OF_PROCEDURE = "2ed65fa9-dfcd-4bc3-876d-922c4d01d59e"
    HUMAN_IGNORANCE_OF_USE_OF_PPE = "85e38278-00d7-488d-be34-fa283d2b43fc"
    HUMAN_LACK_OF_COORDINATION = "81beea1c-cdfa-445e-9314-b174c0a8358f"
    HUMAN_LACK_OF_SKILL_OR_TRAINING = "798b71b3-4249-4793-b62d-57f2eea35115"
    HUMAN_MENTAL_STRESS = "c98378f4-f274-4d10-b153-cf48bb497a71"
    MANAGEMENT_DESIGN_DEFICIENCY = "e6bbede9-c08d-44d7-8f3b-0610c18932a3"
    MANAGEMENT_IMPROPER_HOUSEKEEPING = "ddef18cf-2667-4bcd-aa83-1c07bea7c28c"
    MANAGEMENT_INSUFFICIENT_PLANNING = "9e784840-8dc3-4e63-82b6-645812ffafd5"
    MANAGEMENT_LACK_OF_COORDINATION = "48e2b269-6d2b-40d1-8a5f-c9607cb10713"
    MANAGEMENT_LACK_OF_PROCEDURE = "3ede3f70-3a32-408d-a2e3-b24c47e402d7"
    MANAGEMENT_LACK_OF_PROTECTIVE_SAFETY_EQUIPMENT = "58c333e8-0835-4c7a-803e-ac5ec292df22"
    MANAGEMENT_WORK_PERMIT_NOT_FOLLOWED = "8b9975d8-909c-4adb-bb42-c5528625463c"
    MATERIAL_MATERIAL_COMPONENT_FAILURE = "fe778380-f14a-4e8b-8736-37f047f7bf98"
    MATERIAL_WRONG_MATERIAL = "767f7984-47e0-4ee4-9536-1ca2ffe4e6d8"
