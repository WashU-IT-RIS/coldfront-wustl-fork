import datetime
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
import formencode
from formencode import validators, Invalid
import json

from coldfront.core.constants import BILLING_CYCLE_OPTIONS


class AttributeValidator:

    def __init__(self, value):
        self.value = value

    def validate_int(self):
        try:
            validate = validators.Int()
            validate.to_python(self.value)
        except:
            raise ValidationError(f"Invalid Value {self.value}. Value must be an int.")

    def validate_float(self):
        try:
            validate = validators.Number()
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f"Invalid Value {self.value}. Value must be an float."
            )

    def validate_yes_no(self):
        try:
            validate = validators.OneOf(["Yes", "No"])
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f"Invalid Value {self.value}. Value must be an Yes/No value."
            )

    def validate_date(self):
        try:
            datetime.datetime.strptime(self.value.strip(), "%Y-%m-%d")
        except:
            raise ValidationError(
                f"Invalid Value {self.value}. Date must be in format YYYY-MM-DD and date must be today or later."
            )

    def validate_json(self):
        try:
            _ = json.loads(self.value)
        except:
            raise ValidationError(
                f"Invalid Value. Value must be valid JSON:\n {self.value}"
            )

    def validate_billing_cycle(self):
        try:
            validate = validators.OneOf(BILLING_CYCLE_OPTIONS)
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f"Invalid Value {self.value}. Value must be one of {BILLING_CYCLE_OPTIONS}."
            )

class AllocationAttributeValidator:

    def __init__(self, value):
        self.value = value

    def validate_billing_cycle(self):
        try:
            validate = validators.OneOf(BILLING_CYCLE_OPTIONS)
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f"Invalid Value {self.value}. Value must be one of {BILLING_CYCLE_OPTIONS}."
            )

# jprew - TODO - do we need this?
# class ProjectAttributeValidator:
#     pass