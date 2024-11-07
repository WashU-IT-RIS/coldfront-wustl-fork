import re


# This is copy from coldfront/plugins/qumulo/validators.py
# loading the validator from Django causes an exception due to app requirements.
# TODO: Investigate
def validate_ticket(ticket: str):
    if isinstance(ticket, int):
        return True
    if re.match("\d+$", ticket):
        return True
    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return True
    raise Exception(
        f'Service desk ticket "{ticket}" must have format: ITSD-12345 or 12345',
    )


def numericallity(value: int, conditions: dict):
    if value is None:
        return False
    an_integer = conditions.get("only_integer")
    if an_integer is True:
        if not isinstance(value, int):
            return False
    minimum = conditions.get("greater_than")
    if minimum is not None:
        greater_than_minimum = value > minimum
        if not greater_than_minimum:
            return False
    maximum = conditions.get("less_than_or_equal_to")
    if maximum is not None:
        less_than_or_equal_to = value <= maximum
        if not less_than_or_equal_to:
            return False
    return True


def presence_of(value, presence:bool):
     if presence:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value)
     return True


def length_of(value, conditions):
    allow_blank = conditions.get("allow_blank")
    if allow_blank:
        if not bool(value):
            return True

    if not bool(value):
        return False

    maximum_length = allow_blank = conditions.get("maximum")
    if len(value) <= maximum_length:
        return True
    return False

def inclusion_of(value, accepted_values):
    return value in accepted_values