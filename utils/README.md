# Coldfront Utilities

This directory was created as a space for Coldfront-related utilities that have
yet to be integrated into the application as features.  Some brief notes on the
utilities and their use are listed below.

## Coldfront AD Utils (`coldfront_ad_utils.py`)

This is currently a Python module that sub-classes the main Active Directory API
class used by the application in
`coldfront/plugins/qumulo/utils/active_directory_api.py`.  It provides a user
lookup function, `get_user_department`, that returns the "Display Name" and
"Department Name" for a WUSTL Key.

## ITSM Users (`itsm_users.py`)

This is a script that collects data from ITSM using its REST API.  The script
outputs 2 files: Storage1-AllocationPIs.csv, which contians a list of active
Storage1 allocations and the WUSTL key of the associated PI or sponsor.  The
second output file is a list of WUSTL keys associated with active Storage1
allocations.

## Allocation Storage Report (`allocation_storage_report.py`)

This script consumes the allocation-related output of the ITSM script detailed
above and the Storage2 and Storage3 User List Reports below.  It reads all of
the storage allocation reports outputted by the scripts and performs Active
Directory Lookups on the PI/sponsor associated with the allocation.  It then
outputs a report on allocations that are associated with the Department of
Medicine.  More information on the request for this report is available in
ITSD-40376.

## User Storage Report (`user_storage_report.py`)

This script consumes the user-related output of the ITSM script detailed above
and the Storage2 and Storage3 User List Reports below.  It reads all of the
users and performs Active Directory lookups on the WUSTL keys provided.  It
outputs a list of user's names, WUSTL keys and the name of the department
with which they are affiliated.

## Storage2 and Storage3 User List Reports (`user_list.py`)

As of 20260622, the user list reports script has been updated to provide
WUSTL key-only reports.  This feature can be accessed by setting the
`USER_LIST_ID_ONLY` environment variable to `true` when running the script.
When the value is not set, the script runs the e-mail address report described
later in this section.  When the "user ID only" feature is executed, the script
outputs 2 files that contain data similar to and have the same naming
convention as the ITSM Users script described above.  The Storage2 version of
the report outputs Storage2-AllocationPIs.csv and Storage2-UserList.csv.  The
Storage3 output files are named Storage3-AllocationPIs.csv and
Storage3-UserList.csv.

The default behavior of the `user_list.py` script provides lists of e-mail
addresses for users that have access to Coldfront resources--currently
`Storage2` and `Storage3` are supported.  The script can be run by
uploading/copying it into a running Coldfront container/pod and piping its
contents to the `coldfront shell` command.  The following `kubectl` example
uploads the script to the `/tmp` directory in the job scheduler container:

  `kubectl cp ./user_list.py
    coldfront-qcluster-deployment-86d445f9df-lgzv8:/tmp/user_list.py
    -n coldfront`

More details on and usage examples of the `kubectl` command can be found here:

  https://kubernetes.io/docs/reference/kubectl/generated/kubectl_cp/

Current deployments in both production and QA have a container naming scheme
where `coldfront-deployment-*` is the container for the main web server
process and `coldfront-qcluster-deployment*` is the container for the job
scheduler.  Either of these containers are suitable for running the script.

The reports can be run by piping or directing the script to the standard input
of a `coldfront shell` command.  The script reads the value of the
`USER_LIST_RESOURCE` environment variable to generate the report for the
desired resource and prints the report to its standard output.  Here is an
example that generates a report for `Storage3` and saves it to a CSV file:

  `USER_LIST_RESOURCE=Storage3 coldfront shell < ./user_list.py
    > ./Storage3-UserList-20260107.csv`

The CSV file can then be downloaded with the following command:

  `kubectl cp 
    coldfront-qcluster-deployment-86d445f9df-lgzv8:/tmp/Storage3-UserList-20260107.csv ~/tmp/Storage3-UserList-20260107.csv 
   -n coldfront`

At the time the script was created, a number of IDs did not have associated
e-mail addresses--some of the IDs are service accounts, but others may be
linked to incompletely configured users.  Those unassociated IDs are listed
at the bottom of the report.

## Coldfront Users (`coldfront_users.sh`)

This shell script is, in effect, a wrapper around a series of `kubectl`
commands that run the `user_list.py` script (detailed above) on a running
Coldfront pod.  It accepts the name of the pod and the name of the storage
service (currently Storage2 and Storage3 are supported) as command-line
parameters.  When run, the script copies the `user_list.py` script to the
pod, then runs the script to generate the user ID-only version of its report
for the service (see the description of that functionality above) and then
transfers the data from the pod to the local system before exiting.
