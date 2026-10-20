from django.utils import timezone
from django.core.management.base import BaseCommand
from django_q.tasks import schedule
from django_q.models import Schedule

SCHEDULED_FOR_20TH_DAY_AT_5_AM = timezone.now().replace(day=20, hour=5, minute=0)


class Command(BaseCommand):

    def handle(self, *args, **options):
        print(
            "Scheduling polling monthly notification of users with allocations near limit"
        )
        schedule(
            "coldfront.plugins.qumulo.tasks.notify_users_with_allocations_near_limit",
            name="Notify Users with Allocations Near Limit",
            schedule_type=Schedule.MONTHLY,
            next_run=SCHEDULED_FOR_20TH_DAY_AT_5_AM,
        )
        print(
            "Scheduled polling monthly notification of users with allocations near limit"
        )
