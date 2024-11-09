itsm_to_coldfront_map:
  sponsor:
    coldfront:
      - entity: user
        attributes: # AD should pull the attributes for personal info such as first, last, and email.
          - name: username
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
                ad_record_exist: true
      - entity: project
        attributes:
          - name: name
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
          - name: pi
            value:
              type: int
              transforms: null
              foreign_key: User.objects.get(username)
              validates:
                presence: true
    itsm_value:
      entity: service_provision
      attribute: sponsor
      type: string
  acl_group_members:
    coldfront:
      - entity: user
        aggregate_create: True
        attributes: # AD should pull the attributes for personal info such as first, last, and email.
          - name: username
            value:
              type: string
              transforms: acl_group_members_to_aggregate_create_users
              validates:
                presence: true
                length:
                  maximum: 128
                ad_record_exist: true
      - entity: project
        attributes:
          - name: name
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
          - name: pi
            value:
              type: int
              transforms: null
              foreign_key: User.objects.get(username)
              validates:
                presence: true
    itsm_value:
      entity: service_provision
      attribute: sponsor
      type: string
  department_number:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: department_number
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
    itsm_value:
      entity: service_provision
      attribute: department_number
      type: string
      nulls: true
  funding_number:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: cost_center
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
    itsm_value:
      entity: service_provision
      attribute: funding_number
      type: string
      nulls: true
  billing_contact:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: billing_contact
          - name: value
            value:
              type: string
              transforms: null
              validates:
                length:
                  maximum: 128
                  allow_blank: true
    itsm_value:
      entity: service_provision
      attribute: billing_contact
      type: string
      nulls: true
  technical_contact:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: technical_contact
          - name: value
            value:
              type: string
              transforms: null
              validates:
                length:
                  maximum: 128
                  allow_blank: true
    itsm_value:
      entity: service_provision
      attribute: technical_contact
      type: string
      nulls: true
  secure:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: secure
          - name: value
            value:
              type: Yes/No
              transforms: boolean_to_yes_no
              validates:
                inclusion: [true, false]
    itsm_value:
      entity: service_provision
      attribute: secure
      type: boolean
  service_desk_ticket_number:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_ticket
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                validate_ticket: true
    itsm_value:
      entity: service_provision
      attribute: service_desk_ticket_number
      type: string
  audit:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: audit
          - name: value
            value:
              type: Yes/No
              transforms: truthy_and_falsy_to_boolean_to_yes_no
              validates:
                inclusion: [true, false, null]
    itsm_value:
      entity: service_provision
      attribute: audit
      type: string
      values: ["0", "1", "false", "true", null]
  billing_startdate:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: billing_startdate
          - name: value
            value:
              type: Date
              transforms: date_to_Date
              validates:
                presence: true # Is the conditionally necessary?
    itsm_value:
      entity: service_provision
      attribute: billing_startdate
      type: date
      nulls: true
  sponsor_department_number:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: sponsor_department_number
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true # is this conditionally necessary?
                length:
                  maximum: 128
    itsm_value:
      entity: service_provision
      attribute: sponsor_department_number
      type: string
      nulls: true
  fileset_name:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: fileset_name
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_filesystem_path
          - name: value
            value:
              type: string
              transforms: fileset_name_to_storage_filesystem_path
              validates:
                presence: true
                uniqueness: true
                length:
                  maximum: 128
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_export_path
          - name: value
            value:
              type: string
              transforms: fileset_name_to_storage_export_path
              validates:
                presence: true
                uniqueness: true
                length:
                  maximum: 128
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_name
          - name: value
            value:
              type: string
              transforms: fileset_name_to_storage_name
              validates:
                presence: true
                length:
                  maximum: 128
    itsm_value:
      entity: service_provision
      attribute: fileset_name
      type: string
      nulls: true # found nulls and found duplicates
  fileset_alias:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: fileset_alias
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
    itsm_value:
      entity: service_provision
      attribute: fileset_alias
      type: string
      nulls: true # found nulls and found duplicates
  exempt:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: exempt
          - name: value
            value:
              type: Yes/No
              transforms: boolean_to_yes_no
              validates:
                inclusion: [true, false]
    itsm_value:
      entity: service_provision
      attribute: exempt
      type: boolean
      nulls: true # Most likely, the default value was added after some records had been created
      defaults_to: false
  service_rate_category:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: service_rate_category
          - name: value
            value:
              type: string
              transforms: null
              validates:
                inclusion: ["condo", "consumption", "subscription"]
    itsm_value:
      entity: service_provision
      attribute: service_rate_category
      type: string
      values: ["condo", "consumption", "subscription"] # if the status is active
      nulls: true
  comment:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: comment
          - name: value
            value:
              type: Attribute Expanded Text
              transforms: none
              validates:
                json:
                  allow_blank: true
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_protocols
          - name: value
            value:
              type: string
              transforms: comment_to_protocols
              validates:
                presence: true
                length:
                  maximum: 128
                inclusion: ["smb", "nfs"]
                defaults_to: smb # why?
    itsm_value:
      entity: service_provision
      attribute: comment
      type: text
      nulls: true
  billing_cycle:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: billing_cycle
          - name: value
            value:
              type: string
              transforms: null
              validates:
                presence: true
                length:
                  maximum: 128
                inclusion: [monthly, yearly, quarterly, prepaid, fiscal year]
                defaults_to: monthly
    itsm_value:
      entity: service_provision
      attribute: billing_cycle
      type: string # In fact the data type is a user defined named billing_cycle with labels: [ monthly, yearly, quarterly, prepaid, fiscal year]. For simplicity, let's set it to string.
      nulls: true
  subsidized:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: subsidized
          - name: value
            value:
              type: Yes/No
              transforms: boolean_to_yes_no
              validates:
                inclusion: [true, false]
    itsm_value:
      entity: service_provision
      attribute: subsidized
      type: boolean
      nulls: true
  quota:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: storage_quota
          - name: value
            value:
              type: Int
              transforms: string_to_integer_parsing_value_and_unit_to_Int
              validates:
                presence: true
                numericallity:
                  only_integer: true
                  greater_than: 0
                  less_than_or_equal_to: 2000
    itsm_value:
      entity: service_provision
      attribute: department_number
      type: string
      nulls: true
  allow_nonfaculty:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: allow_nonfaculty
          - name: value
            value:
              type: Yes/No
              transforms: boolean_to_yes_no
              validates:
                inclusion: [true, false] # should NULL default to false?
      - entity: project_attribute
        attributes:
          - name: name
            value: allow_nonfaculty
          - name: value
            value:
              type: Yes/No
              transforms: boolean_to_yes_no
              validates:
                inclusion: [true, false] # should NULL default to false?
    itsm_value:
      entity: service_provision
      attribute: department_number
      type: boolean
      nulls: true
  sla:
    coldfront:
      - entity: allocation_attribute
        attributes:
          - name: name
            value: sla
          - name: value
            value:
              type: string
              transforms: null
              validates:
                length:
                  maximum: 128
                  allow_blank: true
    itsm_value:
      entity: service_provision
      attribute: sla
      type: string
  id: null
  name: null
  department_name: null
  creation_timestamp: null
  service_id: null
  status: null
  who: null
  parent_id: null
  is_condo_group: null
