# aps-forma-issues

Python library for creating an Autodesk Forma Issue with an attached image. 


### Authentication is delegated

The authentication is decoupled, to allow easy switch between ssa and 3-legged auth token.

The TokenProvider protocol is specified in [auth.py](./src/aps_forma_issues/auth.py), but any other object with a
`get_token` method works too.

Every request just needs a bearer token, not a particular auth flow.


## Usage

Illustration on how to use it with 'aps-ssa' library:

```python
from pathlib import Path

from aps_ssa import SsaAuth, SsaConfig
from aps_forma_issues import FormaIssuesClient, FormaIssuesConfig, IssueInput

auth = SsaAuth(SsaConfig(
    client_id="<your-client-id>",
    client_secret="<your-client-secret>",
    service_account_id="<your-service-account-id>",
    key_id="<your-ssa-key-id>",
    private_key_path="./secrets/ssa_private_key.pem",
))
# or: auth = SsaAuth(SsaConfig.from_env())

config = FormaIssuesConfig(
    project_id="<your-forma-project-id>",
    upload_folder_id="<docs-folder-id>",  # image is uploaded here, see below
)
# or: config = FormaIssuesConfig.from_env()

client = FormaIssuesClient(config, auth)

image_path = Path("situation.jpg")
situation_image_bytes = image_path.read_bytes()

result = client.create_issue_with_image(
    IssueInput(
        title="Possible work near suspended load",
        description="Worker observed within the swing radius of an active crane lift.",
        issue_subtype_id="<subtype-id-for-lifting-operations>",
        assigned_to="<safety-manager-user-id>",
        root_cause_id=SafetyRootCause.HUMAN_ERROR,
    ),
    image_bytes=situation_image_bytes,
    filename=image_path.name,
)

print(result.issue_id, result.attachment_id, result.web_view_url)
```

### Root cause presets

Forma Issues has a lot of out-of-the-box "Safety" root cause category:

```python
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
```

These presets can be used as follows:
```python
from aps_forma_issues import IssueInput, SafetyRootCause

IssueInput(..., root_cause_id=SafetyRootCause.HUMAN_ERROR)
```

## Sample
Check [aps-forma-issues sample](./sample/) for illustration on usage and integration. 
