from django.contrib.auth.models import User
from coldfront.core.billing.models import Allocation


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
        is_eligble: bool = False
        # TODO: add additional eligibility criteria here, such as checking if the user has a certain role or is part of a specific group
        # if user.is_staff:
        #    is_eligible = False
        #    return
        # is the user a PI on any allocations?
        # if Allocation.objects.filter(pi=self.user).exists():
        #     is_eligble = True


        return is_eligble
        # placeholder for inspecting the user's allocations and determining if they are eligible for a subsidy

    def get_user(self) -> User:
        return self.user

    def factory(cls, washu_key: str) -> "BillableUser":
        # Factory method to create a BillableUser instance based on a WashU key
        user = User.objects.get(username=washu_key)
        return cls(user)

    def factory_by_allocation(cls, allocation: Allocation) -> "BillableUser":
        # Factory method to create a BillableUser instance based on an Allocation
        return cls(allocation.pi.username)
    
    def __is_staff(self) -> bool:
        # check with AD for staff status, for now we will just check the is_staff field on the user model
        is_staff = False # self.user.is_staff
        return is_staff
    
    def __str__(self):
        return f"BillableUser(washu_key={self.washu_key})"

    factory = classmethod(factory)
    factory_by_allocation = classmethod(factory_by_allocation)
