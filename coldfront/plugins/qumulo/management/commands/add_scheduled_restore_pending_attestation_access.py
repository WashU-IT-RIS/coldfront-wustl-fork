# from django.core.management.base import BaseCommand

# from django_q.models import Schedule

# from coldfront.plugins.qumulo.management.commands.restore_pending_attestation_access import (
#     Command as RestorePendingAttestationAccessCommand,
# )


# class Command(BaseCommand):
#     def handle(self, *args, **options):
#         print("Scheduling restore of pending attestation access")
#         Schedule.objects.get_or_create(
#             func="coldfront.plugins.qumulo.management.commands.add_scheduled_restore_pending_attestation_access.restore_pending_attestation_access",
#             name="Restore Pending Attestation Access",
#             schedule_type=Schedule.HOURLY,
#             repeats=-1,
#         )


# def restore_pending_attestation_access() -> None:
#     RestorePendingAttestationAccessCommand().restore_pending_attestation_access(dry_run=False)
