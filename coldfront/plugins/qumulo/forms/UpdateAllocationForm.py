from coldfront.core.allocation.models import Allocation, AllocationStatusChoice
from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm
from django import forms


class UpdateAllocationForm(AllocationForm):
    def __init__(self, *args, **kwargs):
        self.allocation_id = kwargs.pop("allocation_id", None)
        super().__init__(*args, **kwargs)

        self.fields["storage_name"].disabled = True
        self.fields["storage_filesystem_path"].disabled = True

        self.fields["storage_filesystem_path"].validators = []
        self.fields["storage_name"].validators = []

        self.fields["prepaid_expiration"] = forms.DateTimeField(
            help_text="Allocation is paid until this date",
            label="Prepaid Expiration Date",
            required=False,
        )
        self.fields["prepaid_expiration"].disabled = True
        self.fields["rw_users"].required = self._rw_user_required()

    def _rw_user_required(self) -> bool:
        required = True
        if self.allocation_id is not None:
            allocation = Allocation.objects.get(pk=self.allocation_id)
            ready_for_deletion_id = AllocationStatusChoice.objects.get(
                name="Ready for deletion"
            ).id
            if allocation.status_id == ready_for_deletion_id:
                required = False
        return required
