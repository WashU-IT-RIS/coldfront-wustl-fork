from django.contrib.auth.models import User
from coldfront.core.allocation.models import Allocation
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI


def is_eligible_for_subsidy(washu_key: str) -> bool:
    user = BillableUser.factory(washu_key)
    return user.is_eligible_for_subsidy()


class BillableUser:
    def __init__(self, washu_key: str):
        self.washu_key = washu_key
        self.user = User.objects.filter(username=washu_key).first()

    def is_eligible_for_subsidy(self) -> bool:
        try:
            return self.__is_faculty_member()
        except Exception as e:
            raise ValueError(f"Cannot determine the user's eligibility for subsidy.")

    def __is_faculty_member(self) -> bool:
        return ActiveDirectoryAPI().is_faculty_member(self.washu_key)

    def get_user(self) -> User:
        return self.user

    def factory(cls, washu_key: str) -> "BillableUser":
        # Factory method to create a BillableUser instance based on a WashU key
        user = User.objects.filter(username=washu_key).first()
        if not user:
            raise ValueError(f"No user found with WashU key: {washu_key}")
        return cls(washu_key)

    def factory_by_allocation(cls, allocation: Allocation) -> "BillableUser":
        # Factory method to create a BillableUser instance based on an Allocation
        user = allocation.project.pi
        if not user:
            raise ValueError("No PI found for the given allocation")
        return cls(user.username)

    def __str__(self):
        return f"BillableUser(washu_key={self.washu_key})"

    factory = classmethod(factory)
    factory_by_allocation = classmethod(factory_by_allocation)
