# import json
import os

# import secrets
# import uuid
# from datetime import datetime, timezone

# from coldfront.core.allocation.models import (
#     AllocationAttribute,
#     AllocationAttributeType,
# )

PENDING_ATTESTATION_EVENT_ATTRIBUTE_NAME = "pending_attestation_event"


def pre_onboard_group_name() -> str:
    return os.environ.get("AD_PRE_ONBOARD_GROUP", "ris-pre-onboard")


def attestation_gate_enabled() -> bool:
    """Feature flag: the attestation gate makes every new storage allocation
    access grant depend on a live Workday connection (via the
    IntegrationHub-managed `shared_lib` package -- not a pip dependency of
    this project, so it may not be importable in every environment this
    plugin runs in). Defaults to disabled so existing grant behavior is
    unaffected until this is explicitly turned on with working Workday
    credentials confirmed reachable from wherever ColdFront runs.
    """
    return os.environ.get("ATTESTATION_GATE_ENABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def find_completed_attestation(wustlkey, ad_api, completed_records):
    """Returns the Workday completed-attestation record (see
    utils/workday_api.WorkdayAPI.get_completed_attestations) for wustlkey,
    or None if they have no record of a completed attestation for the
    current cycle -- i.e. they are NOT yet clear to provision new access.
    Access is only granted once a completed record is found; merely being
    absent from an overdue list is not treated as clearance.

    completed_records is normally fetched once per request/run via
    WorkdayAPI().get_completed_attestations() and passed in by the caller,
    so granting access to several users in the same allocation-users
    request doesn't re-query Workday once per user. Workday's records are
    keyed by universal_id (AD's wustlEduId), not wustlkey, so each is
    resolved via ad_api.find_wustlkey_by_universal_id; a record that fails
    to resolve can't be matched to any user, so it's skipped rather than
    treated as a failure.
    """
    for record in completed_records:
        try:
            resolved_wustlkey = ad_api.find_wustlkey_by_universal_id(
                record["universal_id"]
            )
        except Exception:  # noqa: BLE001 - unresolvable record, not a match
            continue
        if resolved_wustlkey == wustlkey:
            return record
    return None


# def _event_id() -> str:
#     return f"evt_{uuid.uuid4().int % 10**9:09d}"


# def _timestamp() -> str:
#     return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# def _restoration_token(user_id: str) -> str:
#     return f"{user_id}_{secrets.token_hex(6)}"


# def build_pending_attestation_event(username, allocation_id, scope, attestation_cycle_id=None) -> dict:
#     """Builds the same event schema documented in
#     ../ris-user-management-tmp/python/README.md#log-event-schema, so an
#     event logged here reads the same way as one logged by that repo's CLI
#     (they don't share code or a process -- this is convergent by design, not
#     a shared library).

#     `revoked_entitlements` holds a single "coldfront" entitlement -- despite
#     the field's name, nothing was revoked here; the grant was withheld
#     pending attestation. The action is named to start with `ACCESS_REVOKED`
#     so ris-user-management-tmp's `restore` command accepts an exported copy
#     of this event without needing --force, if this ever needs to be restored
#     from that side instead of via restore_pending_attestation_access.
#     """
#     return {
#         "event_id": _event_id(),
#         "timestamp": _timestamp(),
#         "action": "ACCESS_REVOKED_PENDING_ATTESTATION",
#         "user_id": username,
#         "revoked_entitlements": [{"system": "coldfront", "allocation_id": allocation_id, "scope": scope}],
#         "attestation_cycle_id": attestation_cycle_id,
#         "restoration_token": _restoration_token(username),
#         "source_event_id": None,
#     }


# def record_pending_attestation_event(access_allocation, username, scope, attestation_cycle_id=None) -> dict:
#     """Withholds a storage allocation access grant: records it as a
#     `pending_attestation_event` AllocationAttribute on `access_allocation`
#     (the rw or ro access allocation the grant was for) instead of creating
#     the AllocationUser/AD group membership that would normally grant it.
#     Returns the event dict that was stored (as JSON) on the attribute.
#     """
#     storage_allocation_pk = access_allocation.get_attribute("storage_allocation_pk")
#     event = build_pending_attestation_event(username, storage_allocation_pk, scope, attestation_cycle_id)
#     AllocationAttribute.objects.create(
#         allocation_attribute_type=AllocationAttributeType.objects.get(
#             name=PENDING_ATTESTATION_EVENT_ATTRIBUTE_NAME
#         ),
#         allocation=access_allocation,
#         value=json.dumps(event),
#     )
#     return event


# def get_pending_attestation_events():
#     """Returns [(attribute, event_dict), ...] for every currently-pending
#     attestation event across all allocations, oldest first. Used by the
#     restore_pending_attestation_access management command to find users who
#     may have attested since being held. Attributes whose value isn't valid
#     JSON (shouldn't happen -- only record_pending_attestation_event writes
#     this attribute type) are skipped rather than raising.
#     """
#     attributes = AllocationAttribute.objects.filter(
#         allocation_attribute_type__name=PENDING_ATTESTATION_EVENT_ATTRIBUTE_NAME
#     ).order_by("created")

#     events = []
#     for attribute in attributes:
#         try:
#             events.append((attribute, json.loads(attribute.value)))
#         except (TypeError, ValueError):
#             continue
#     return events
