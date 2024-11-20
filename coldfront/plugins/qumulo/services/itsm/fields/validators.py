import re, json

import coldfront.core.allocation.models as coldfront_models


# This is copy from coldfront/plugins/qumulo/validators.py
# loading the validator from Django causes an exception due to app requirements.
def validate_ticket(ticket: str, validate: bool = True):
    if not validate:
        return

    if isinstance(ticket, int):
        return

    if re.match("\d+$", ticket):
        return

    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return

    return f"{ticket} is not in the format ITSD-12345 or 12345"


def numericallity(value: int, conditions: dict):
    if value is None:
        return f"{value} is not a number"

    an_integer = conditions.get("only_integer")
    if an_integer is True:
        if not isinstance(value, int):
            return f"{value} is not an integer"

    minimum = conditions.get("greater_than")
    if minimum is not None:
        greater_than_minimum = value > minimum
        if not greater_than_minimum:
            return f"must be greater than {minimum}"

    maximum = conditions.get("less_than_or_equal_to")
    if maximum is not None:
        less_than_or_equal_to = value <= maximum
        if not less_than_or_equal_to:
            return f"must be less than or equals to {maximum}"

    return


def presence(value, presence: bool = True):
    if presence:
        if value is None:
            return "must be specified"

        if isinstance(value, str):
            if not bool(value):
                return "must not be blank"
    return


def length(value, conditions):
    allow_blank = conditions.get("allow_blank")
    if allow_blank:
        if not bool(value):
            return

    if not bool(value):
        return "must not be blank"

    maximum_length = conditions.get("maximum")
    if len(value) <= maximum_length:
        return
    return f"exceeds the limit of {maximum_length}: {value}"


def inclusion(value, accepted_values):
    if isinstance(value, list):
        value_list = value
        if all(element in accepted_values for element in value_list):
            return

    if value in accepted_values:
        return

    return f"{value} is not amongst {accepted_values}"


def validate_json(value, conditions={}):
    if conditions.get("allow_blank"):
        if value in [None, ""]:
            return

    try:
        bool(json.loads(value))
    except:
        return "is not a valid JSON"
    return


# TODO check if the user exists
def ad_record_exist(value, validate: bool = True):
    if not validate:
        return

    return


# This is a simple uniqueness validator that finds if a record exists for a
# given entity (table), attribute (field), and value.
# Note that the field is hardcoded to allocation_attribute_type__name since I need to 
# figure out how to pass the entity_attribute from the conditions['entity_attribute'] to the filter. 
# This seemed promissing to no avail: exec(f"{conditions['entity_attribute']}")
def uniqueness(value, conditions):

    # SELECT "allocation_allocationattribute"."id", "allocation_allocationattribute"."created", "allocation_allocationattribute"."modified", "allocation_allocationattribute"."allocation_attribute_type_id", "allocation_allocationattribute"."allocation_id", "allocation_allocationattribute"."value" FROM "allocation_allocationattribute" INNER JOIN "allocation_allocationattributetype" ON ("allocation_allocationattribute"."allocation_attribute_type_id" = "allocation_allocationattributetype"."id") WHERE ("allocation_allocationattributetype"."name" = storage_name AND "allocation_allocationattribute"."value" = /storage2-dev/jin810)
    exists = (
        getattr(coldfront_models, conditions["entity"])
        .objects.filter(
            allocation_attribute_type__name=conditions["attribute_name_value"],
            value=value,
        )
        .exists()
    )

    if exists:
        return f"{value} is not unique"

    return
