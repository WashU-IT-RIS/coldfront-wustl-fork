from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, Paginator
from django.views.generic import ListView


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


class ClientListView(LoginRequiredMixin, ListView):

    model = User
    template_name = "client_list_view.html"
    context_object_name = "client_list"
    paginate_by = 25

    def get_queryset(self):


        view_list: List[ClientListItem] = []

        # jprew - for now, just find all users on the theory they're at least listed on a
        # project if not an allocation
        all_users = User.objects.all()
        for user in all_users:
            item = ClientListItem(wustl_key=user.username, email=user.email)
            view_list.append(item)

        return view_list

    def _handle_pagination(
        self, client_list: List[ClientListItem], page_num, page_size
    ):
        paginator = Paginator(client_list, page_size)

        try:
            next_page = paginator.page(page_num)
        except EmptyPage:
            next_page = paginator.page(paginator.num_pages)

        return next_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["allocation_list"] = self.get_queryset()
        clients_count = len(self.get_queryset())
        context["client_count"] = clients_count

        allocation_list = context.get("client_list")

        page_num = self.request.GET.get("page")
        if page_num is None or type(page_num) is not int:
            page_num = 1

        allocation_list = self._handle_pagination(
            allocation_list, page_num, self.paginate_by
        )

        return context
