# sponsor has an email
# if found, should convert email to whashu_key
# if not found, should reject migration
# if multiple found, reject migration with an exception

# billing_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify through a warning message

# technical_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify through a warning message

# create sub allocations from the project_dir in itsm comment fields
# if project_dir exists, should create sub allocations
# if not, should skip since the allocation has no sub allocations

# create users from the rw and ro in the itsm comment fields
# if user exists, should create user
# if not, should skip and notify through a warning message

