import datetime
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django_q.models import Schedule
from django_q.tasks import schedule

base_dir = settings.BASE_DIR


class Command(BaseCommand):

    def handle(self, *args, **options):

        date = timezone.now() + datetime.timedelta(days=1)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        schedule(
            "coldfront.core.allocation.tasks.update_statuses",
            schedule_type=Schedule.DAILY,
            next_run=date,
        )

        schedule(
            "coldfront.core.allocation.tasks.send_expiry_emails",
            schedule_type=Schedule.DAILY,
            next_run=date,
        )

        schedule(
            "coldfront.core.group.tasks.grant_usersupport_global_project_manager",
            name="Grant RIS-UserSupport Manager Status over All Projects",
            schedule_type=Schedule.MINUTES,
            next_run=(timezone.now() + datetime.timedelta(minutes=5)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ),
        )
