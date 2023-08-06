# Ansible Collection - `anophelesgreyhoe.googlebackupdr`

## Collection Dependencies

The [Google Cloud SDK](https://cloud.google.com/sdk/) must be installed in
order to retrieve an access token.

## Included modules

| Name              | Description                              |
| ----------------- | ---------------------------------------- |
| `backup`          | Create a backup of an application        |

See module documentation for more information on usage.

## Examples

Rather than simple playbooks as below, you may wish to create your own
collections/roles for greater flexibility, and to allow these to be called from
other playbooks.

### `backup`

#### Back up a Google Backup and DR Application

In the context of Google Backup and DR, an 'application' represents any
backup target, whether a GCE instance (snapshot), database, etc.

```yaml
- name: Back up an application
  hosts: all
  gather_facts: false
  vars:
    token: "{{ lookup('ansible.builtin.pipe', 'gcloud auth print-access-token') }}"
  tasks:
    - anophelesgreyhoe.googlebackupdr.backup:
        api_url: "https://gbdr-api.backupdr.googleusercontent.com/actifio/"
        access_token: "{{ token }}"
        template_name: "snapshot_B-1d-14d"
        policy_name: "daily-snap"
        app_name: "{{ inventory_hostname_short }}"
        label: "On-demand backup"
      delegate_to: localhost
      throttle: 1
```
