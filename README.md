![ColdFront](docs/pages/images/logo-lg.png)

# ColdFront - Resource Allocation System

[![Documentation Status](https://readthedocs.org/projects/coldfront/badge/?version=latest)](https://coldfront.readthedocs.io/en/latest/?badge=latest)

ColdFront is an open source resource and allocation management system designed to provide a
central portal for administration, reporting, and measuring scientific impact
of cyberinfrastructure resources. ColdFront was created to help high performance computing (HPC) centers manage access to a diverse set of resources across large groups of users and provide a rich set of
extensible meta data for comprehensive reporting. The flexiblity of ColdFront allows centers to manage and automate their policies and procedures within the framework provided or extend the functionality with [plugins](docs/pages/index.md#extensibility). ColdFront is written in Python and released under the GPLv3 license.

## Features

- Allocation based system for managing access to resources
- Self-service portal for users to request access to resources for their research group
- Collection of Project, Grant, and Publication data from users
- Center director approval system and annual project review process
- Email notifications for expiring/renewing access to resources
- Ability to define custom attributes on resources and allocations
- Integration with 3rd party systems for automation, access control, and other system provisioning tasks

[Read more](docs/pages/index.md)

## Community Supported Plugins

- [OpenStack Plugin](https://github.com/nerc-project/coldfront-plugin-openstack)
- [Keycloak User Search](https://github.com/nerc-project/coldfront-plugin-keycloak)
- [Starfish Plugin](https://github.com/fasrc/sftocf)

_Submit a PR to add your plugin to the list above._

## Qumulo Plugin: Allocation Access-User REST API

The Qumulo plugin exposes a small REST API for managing and querying who has
read/write (`rw`) or read-only (`ro`) access to a Storage2 allocation's AD
groups. In addition to the usual ColdFront session login, these endpoints
accept an OAuth2 `client_credentials` bearer token, so external systems can
call them without a logged-in browser session.

### Authentication

Requests are authenticated with either:

- **Session cookie** — the normal logged-in ColdFront session.
- **OAuth2 bearer token** — issued by [django-oauth-toolkit](https://github.com/jazzband/django-oauth-toolkit)
  via the `client_credentials` grant.

To set up a machine client:

1. Register an OAuth2 Application in the Django admin at `/o/applications/`
   with **Client type: Confidential** and **Authorization grant type: Client credentials**.
2. Request a token:

   ```bash
   curl -X POST https://<host>/o/token/ \
     -u "<client_id>:<client_secret>" \
     -d "grant_type=client_credentials"
   ```

   ```json
   {"access_token": "...", "expires_in": 36000, "token_type": "Bearer", "scope": "read write"}
   ```

3. Send the token on subsequent requests: `Authorization: Bearer <access_token>`.

Each endpoint below declares the scope it requires (`read` or `write`); a
token must carry that scope, or the request must come from an authenticated
session.

### Endpoints

**`POST /qumulo/allocation/<allocation_id>/access-users/`** — scope: `write`

Adds one or more usernames to the allocation's `rw` and/or `ro` AD access
groups.

```json
{"rw_users": ["wustlkey1"], "ro_users": ["wustlkey2"]}
```

Returns `200` with the users that were newly added (existing members are
skipped) and the AD group names, or `400` if the body isn't valid JSON or
doesn't include a non-empty `rw_users`/`ro_users` array:

```json
{
  "allocation_id": 42,
  "added_users": {"rw": ["wustlkey1"], "ro": ["wustlkey2"]},
  "pending_users": {"rw": [], "ro": []},
  "storage_acl_name": {"rw": "storage-foo-rw", "ro": "storage-foo-ro"}
}
```

`pending_users` is only ever non-empty when the [attestation gate](#attestation-gated-access-provisioning)
is enabled and withheld a grant pending attestation — see below.

**`DELETE /qumulo/allocation/<allocation_id>/access-users/`** — scope: `write`

Removes usernames from both the `rw` and `ro` AD access groups.

```json
{"users": ["wustlkey1"]}
```

Returns `200` with the users that were removed, or `400` for an invalid body:

```json
{
  "allocation_id": 42,
  "removed_users": {"rw": ["wustlkey1"], "ro": []},
  "storage_acl_name": {"rw": "storage-foo-rw", "ro": "storage-foo-ro"}
}
```

**`GET /qumulo/allocation/users/<username>/`** — scope: `read`

Lists every Storage2 allocation the given user has `rw` and/or `ro` access
to. Returns `404` if the username doesn't exist.

```json
{
  "username": "wustlkey1",
  "allocations": [
    {
      "allocation_id": 42,
      "project_id": 7,
      "project_name": "Example Project",
      "storage_name": "foo",
      "storage_filesystem_path": "/storage2/foo",
      "status": "Active",
      "access": ["ro", "rw"]
    }
  ]
}
```

### Attestation-gated access provisioning

`AllocationUsersApiView`'s `POST` (grant) can optionally check a user's
Workday access-attestation status before granting them `rw`/`ro` access,
instead of granting unconditionally. This is off by default — set
`ATTESTATION_GATE_ENABLED=true` to turn it on.

Access is only granted once Workday shows the attestation as **completed**
(`assignmentStatus1 = 'Completed'`) — being merely absent from an overdue
list is not treated as clearance. For each newly-granted username:

- **Attestation completed:** granted immediately, exactly as before —
  included in the response's `added_users`.
- **Attestation not (yet) completed:** the grant is withheld. The user is
  added to a holding AD group instead (`AD_PRE_ONBOARD_GROUP`, default
  `ris-pre-onboard`), and a `pending_attestation_event` is recorded (as a
  private `AllocationAttribute` on the `rw`/`ro` access allocation) —
  included in the response's `pending_users` instead of `added_users`. The
  event's shape matches the schema `ris-user-management-tmp/python/README.md`
  documents (`event_id`/`timestamp`/`action`/`user_id`/`revoked_entitlements`/
  `attestation_cycle_id`/`restoration_token`/`source_event_id`), with
  `action: "ACCESS_REVOKED_PENDING_ATTESTATION"` and a single `coldfront`
  entitlement in `revoked_entitlements` — the two systems don't share code,
  but a logged event reads the same way in both.

**Closing the loop:** `python manage.py restore_pending_attestation_access`
re-checks Workday for every pending event; a user who now shows up as
completed is granted the withheld access, removed from the pre-onboard
group, and has their pending event cleared. `--dry-run` reports what would
happen without changing anything. `add_scheduled_restore_pending_attestation_access`
wires this up to run hourly via `django-q`.

This depends on a live Workday connection through the IntegrationHub-managed
`shared_lib` package (not a pip dependency of this project — see
`coldfront/plugins/qumulo/utils/workday_api.py`), plus
`WORKDAY_URL`/`WORKDAY_TENANT`/`WORKDAY_OAUTH_CLIENT_ID`/
`WORKDAY_OAUTH_CLIENT_SECRET`/`WORKDAY_OAUTH_REFRESH_TOKEN`. Confirm those
are reachable from wherever ColdFront actually runs before enabling the
gate — if the Workday call itself fails (network, missing `shared_lib`, bad
credentials) while the gate is enabled, that failure propagates as an
unhandled error on the grant request rather than silently granting or
silently withholding access.

### API Setup

`django-oauth-toolkit` is included in `coldfront/plugins/qumulo/requirements.txt`.
After installing dependencies, run migrations so its `Application`/`AccessToken`
tables exist:

```bash
pip install -r requirements.txt
python manage.py migrate oauth2_provider
```

## Documentation

For more information on installing and using ColdFront see our [documentation here](https://coldfront.readthedocs.io)

## Contact Information

If you would like a live demo followed by QA, please contact us at
ccr-coldfront-admin-list@listserv.buffalo.edu. You can also contact us for
general inquiries and installation troubleshooting.

If you would like to join our mailing list to receive news and updates, please
send an email to listserv@listserv.buffalo.edu with no subject, and the
following command in the body of the message:

subscribe ccr-open-coldfront-list@listserv.buffalo.edu first_name last_name

## License

ColdFront is released under the GPLv3 license. See the LICENSE file.

## Testing

### Setup

To run tests, the following variables should be included in a `.env` file in the root directory of the repo:

```
PLUGIN_QUMULO=True
PLUGIN_INTEGRATEDBILLING=True
AD_SERVER_NAME=foo
AD_USERNAME=bar
AD_USER_PASS=bah
QUMULO_INFO={"Storage2": {"path": "/foo/bar", "host": "foo","port": "8000","user": "admin","pass": "bar" }}
```

### Running

A complete test suite can be run with `manage.py test`. You can target sub-groups of tests by including a specifying argument. Ex: `manage.py.test coldfront.plugins.qumulo.tests` will run only unit tests for the qumulo plugin.

Typically, you'll want to run non integration tests separately, which can be done with `python manage.py test --exclude-tag integration`. Integrations can be run with `python manage.py test --tag integration`.

### Set up Local Environment and Run tests

1. Go to the root of the `coldfront-wustl-fork` repo.
2. Create a (Python) virtual environment: `python3 -mvenv coldfront-venv`
3. Activate the virtual environment: `source coldfront-venv/bin/activate`
4. Install the dependencies

```
pip install --upgrade pip
pip install -r requirements-dev.txt
```

5. Run a test to verify the installation: `python manage.py test coldfront.plugins.qumulo.tests`

**Steps for local development**

```
python3 -mvenv coldfront-venv
source coldfront-venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
python manage.py test coldfront.plugins.qumulo.tests
```

### Integration Test ENV

Integration Tests need to be run while connected to a VPN. The following variables need to be included for functioning integration tests. Credentials should be stored in the `pass` store.

```
PLUGIN_QUMULO=True
PLUGIN_INTEGRATEDBILLING=True
QUMULO_HOST=
QUMULO_PORT=
QUMULO_USER=
QUMULO_PASS=
DEBUG=TRUE
AD_USER_PASS=
AD_USERNAME=
AD_SERVER_NAME=
AD_GROUPS_OU=OU=QA,OU=RIS,OU=Groups,DC=accounts,DC=ad,DC=wustl,DC=edu
STORAGE2_PATH=
```
