from django.contrib.auth.models import User
from coldfront.core.allocation.models import Allocation
from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI

def is_eligible_for_subsidy(washu_key: str) -> bool:
    user = BillableUser.factory(washu_key)
    return user.is_eligible_for_subsidy()


class BillableUser:
    def __init__(self, user: User):
        self.user = user
        self.washu_key = self.__get_washu_key()

    def __get_washu_key(self) -> str:
        return self.user.username

    def is_eligible_for_subsidy(self) -> bool:
        is_eligible: bool = False
        if self.__is_faculty():
            is_eligible = True
        return is_eligible

    def __is_faculty(self) -> bool:
        return ActiveDirectoryAPI().is_faculty_member(self.washu_key)

    def get_user(self) -> User:
        return self.user

    def factory(cls, washu_key: str) -> "BillableUser":
        # Factory method to create a BillableUser instance based on a WashU key
        user = User.objects.get(username=washu_key)
        return cls(user)

    def factory_by_allocation(cls, allocation: Allocation) -> "BillableUser":
        # Factory method to create a BillableUser instance based on an Allocation
        return cls(allocation.pi.username)

    def __str__(self):
        return f"BillableUser(washu_key={self.washu_key})"

    factory = classmethod(factory)
    factory_by_allocation = classmethod(factory_by_allocation)
