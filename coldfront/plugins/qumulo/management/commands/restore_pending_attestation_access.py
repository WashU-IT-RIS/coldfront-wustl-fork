from django.core.management.base import BaseCommand

from coldfront.plugins.qumulo.utils.acl_allocations import AclAllocations
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI
from coldfront.plugins.qumulo.utils.attestation import (
    find_completed_attestation,
    get_pending_attestation_events,
    pre_onboard_group_name,
)
from coldfront.plugins.qumulo.utils.workday_api import WorkdayAPI


class Command(BaseCommand):
    help = (
        "Closes the loop opened by AllocationUsersApiView holding a user's storage "
        "allocation access grant pending attestation: for every pending_attestation_event "
        "still on record, re-checks Workday and, for a user who has since attested, grants "
        "the withheld access, removes them from the pre-onboard AD group, and clears the "
        "pending event."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Reports which pending grants would be restored without changing anything",
        )

    def handle(self, *args, **options) -> None:
        dry_run = options["dry_run"]
        self.restore_pending_attestation_access(dry_run)

    def restore_pending_attestation_access(self, dry_run: bool) -> None:
        pending_events = get_pending_attestation_events()
        if not pending_events:
            self.stdout.write("No pending attestation events found.")
            return None

        active_directory_api = ActiveDirectoryAPI()
        completed_records = WorkdayAPI().get_completed_attestations()

        for attribute, event in pending_events:
            username = event["user_id"]
            access_allocation = attribute.allocation

            if find_completed_attestation(username, active_directory_api, completed_records) is None:
                self.stdout.write(f" - {username}: not yet completed, leaving held (event {event['event_id']})")
                continue

            if dry_run:
                self.stdout.write(
                    f" - {username}: attestation now current, would restore access to "
                    f"allocation {access_allocation.pk} (event {event['event_id']})"
                )
                continue

            storage_acl_name = access_allocation.get_attribute("storage_acl_name")
            AclAllocations.add_user_to_access_allocation(username, access_allocation)
            active_directory_api.add_user_to_ad_group(wustlkey=username, group_name=storage_acl_name)
            active_directory_api.remove_member_from_group(username, pre_onboard_group_name())
            attribute.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f" - {username}: attestation now current, restored access to allocation "
                    f"{access_allocation.pk} (event {event['event_id']})"
                )
            )
