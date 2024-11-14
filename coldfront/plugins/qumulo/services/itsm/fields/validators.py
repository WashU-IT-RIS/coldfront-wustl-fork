import re, json


# This is copy from coldfront/plugins/qumulo/validators.py
# loading the validator from Django causes an exception due to app requirements.
def validate_ticket(ticket: str, validate: bool = True):
    if not validate:
        return True

    if isinstance(ticket, int):
        return True

    if re.match("\d+$", ticket):
        return True

    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return True

    return False


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


def presence(value, presence: bool = True):
    if presence:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value)
    return True


def length(value, conditions):
    allow_blank = conditions.get("allow_blank")
    if allow_blank:
        if not bool(value):
            return True

    if not bool(value):
        return False

    maximum_length = conditions.get("maximum")
    if len(value) <= maximum_length:
        return True
    return False


def inclusion(value, accepted_values):
    return value in accepted_values


def validate_json(value, conditions={}):
    if conditions.get("allow_blank"):
        if value in [None, ""]:
            return True

    try:
        bool(json.loads(value))
    except:
        return False
    return True

# TODO
def ad_record_exist(value, validate: bool = True):
    if not validate:
        return True

    return True

# TODO
def uniqueness(value, validate: bool = True):
    if not validate:
        return True

    return True
