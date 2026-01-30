# sponsor has an email
# if found, should convert email to whashu_key
# if not found, should reject migration
# if multiple found, should reject migration

# billing_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify

# technical_contact has an email
# if found, should convert email to whashu_key
# if not found, should set to None and notify

# create sub allocations from the project_dir in itms comment fields
# if project_dir exists, should create sub allocations
# if not, should skip

# create users from the rw and ro in the itms comment fields
# if user exists, should create user
# if not, should skip and notify

