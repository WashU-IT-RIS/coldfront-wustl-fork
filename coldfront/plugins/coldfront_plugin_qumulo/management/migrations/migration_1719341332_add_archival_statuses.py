from coldfront.core.allocation.models import AllocationStatusChoice


def run() -> None:
    print("Adding Archival Allocation Statuses")
    AllocationStatusChoice.objects.get_or_create(name="Invalid")
    AllocationStatusChoice.objects.get_or_create(name="Ready for deletion")
    AllocationStatusChoice.objects.get_or_create(name="Deleted")
