from typing import List
import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, Paginator
from django.views.generic import View
from django.http import HttpResponse


from coldfront.core.user.models import (
    User
)
from coldfront.core.resource.models import Resource


class ClientListItem:
    wustl_key: str
    email: str

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ClientListCSVView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="client_list.csv"'

        writer = csv.writer(response)
        writer.writerow(['WUSTL Key', 'Email'])

        all_users = User.objects.all()
        for user in all_users:
            writer.writerow([user.username, user.email])

        return response
