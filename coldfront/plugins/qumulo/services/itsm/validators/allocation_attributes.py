import re

# This is copy from coldfront/plugins/qumulo/validators.py
# loading the validator from Django causes an exception due to app requirements. 
# TODO: Investigate
def validate_ticket(ticket: str):
    if re.match("\d+$", ticket):
        return
    if re.match("ITSD-\d+$", ticket, re.IGNORECASE):
        return
    raise Exception(
        f"Service desk ticket \"{ticket}\" must have format: ITSD-12345 or 12345",
    )
