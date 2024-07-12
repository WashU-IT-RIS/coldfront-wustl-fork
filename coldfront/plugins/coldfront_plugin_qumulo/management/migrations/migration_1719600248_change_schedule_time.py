from django_q.models import Schedule


def run() -> None:
    print("changing ad poller to 1 minute")
    ad_poller_schedule = Schedule.objects.get(name="Update Pending Allocations")

    ad_poller_schedule.schedule_type = Schedule.MINUTES
    ad_poller_schedule.minutes = 1
    ad_poller_schedule.save()
