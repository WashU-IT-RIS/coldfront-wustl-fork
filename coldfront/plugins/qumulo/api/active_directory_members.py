from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from coldfront.plugins.qumulo.utils.active_directory_api import ActiveDirectoryAPI


class ActiveDirectoryMembers(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, *args, **kwargs):
        active_directory_api = ActiveDirectoryAPI()

        members = request.GET.getlist("members[]")
        ldap_members = active_directory_api.get_members(members)
        print(f"ldap_members: {ldap_members}")
        found_members = list(
            map(
                lambda member: member["attributes"]["sAMAccountName"],
                ldap_members,
            )
        )

        return JsonResponse({"validNames": found_members})
