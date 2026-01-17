# Coldfront Utilities

This directory was created as a space for Coldfront-related utilities that have
yet to be integrated into the application as features.  Some brief notes on the
utilities and their use are listed below.

## Storage2 and Storage3 User List Reports

The `user_list.py` script provides lists of e-mail addresses for users that
have access to Coldfront resources--currently `Storage2` and `Storage3` are
supported.  The script can be run by uploading/copying it into a running
Coldfront container/pod and piping its contents to the `coldfront shell`
command.  The following `kubectl` example uploads the script to the `/tmp`
directory in the job scheduler container:

  `kubectl cp ./user_list.py
    coldfront-qcluster-deployment-86d445f9df-lgzv8:/tmp/user_list.py
    -n coldfront`

More details on and usage examples of the `kubectl` command can be found here:

  https://kubernetes.io/docs/reference/kubectl/generated/kubectl_cp/

Current deployments in both production and QA have a container naming scheme
where `coldfront-deployment-*` is the container for the main web server
process and `coldfront-qcluster-deployment*` is the container for the job
scheduler.  Either of these containers are suitable for running the script.

The reports can be run by piping the script to the standard input of a
`coldfront shell` command.  The script reads the value of the
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
