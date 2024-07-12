from ...forms import AllocationForm


class BaseTestableAllocationForm(AllocationForm):
    def __init__(self, *args, **kwargs):
        self.params_key = "taf_class_params"
        self.form_is_valid = None
        super().__init__(*args, **self._filter_params(**kwargs))

    def _filter_params(self, **kwargs):
        def filter_func(pair):
            key, value = pair
            if key == self.params_key:
                return False
            return True

        return dict(filter(filter_func, kwargs.items()))


class TestableS3AllocationForm(BaseTestableAllocationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.s3_validation_ran = False
        if self._check_params_validate(**kwargs) is True:
            self.form_is_valid = self.is_valid()

    def _check_params_validate(self, **kwargs):
        return kwargs.get(self.params_key, False).get("validate", False)

    def _validate_s3_allocation_name(self, name: str):
        super()._validate_s3_allocation_name(name)
        self.s3_validation_ran = True
