from coldfront.plugins.qumulo.forms.AllocationForm import AllocationForm


class UpdateAllocationForm(AllocationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["storage_name"].disabled = True
        self.fields["storage_filesystem_path"].disabled = True

        self.fields["storage_filesystem_path"].validators = []
        self.fields["storage_name"].validators = []
