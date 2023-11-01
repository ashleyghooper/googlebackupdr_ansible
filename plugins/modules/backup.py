#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ashley Hooper <ashleyghooper@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = r"""
---
module: backup

short_description: On-demand Google Backup and DR backup

description:
  - Perform an on-demand backup of an application in Google Backup and DR.

version_added: "1.0.0"

author:
  - "Ashley Hooper (@ashleyghooper)"

options:
  api_url:
    description:
      - The URL of the Google Backup and DR instance.
    type: str
    required: true

  access_token:
    description:
      - The GCP access token to be used to authenticate to Google Backup and DR.
    type: str
    required: true

  template_name:
    description:
      - The name of the SLA Template to be used to back up the application.
    type: str
    required: true

  policy_name:
    description:
      - The name of the SLA Template Policy to be used to back up the application.
    type: str
    required: true

  app_name:
    description:
      - The name of the Google Backup and DR application to create a backup of.
    type: str
    required: true

  label:
    description:
      - The label to apply to the backup.
    type: str

requirements:
  - "python >= 2.6"
"""

EXAMPLES = r"""
- name: Back up an application
  hosts: all
  gather_facts: false
  vars:
    token: lookup('ansible.builtin.pipe', 'gcloud auth print-access-token')
  tasks:
    - anophelesgreyhoe.googlebackupdr.backup:
        api_url: https://gbdr-api.backupdr.googleusercontent.com/actifio/
        access_token: "{{ token }}"
        template_name: snapshot_B-1d-14d
        app_name: "{{ inventory_hostname_short }}"
      delegate_to: localhost
      throttle: 1
"""

# TODO: Add Ansible module RETURN section

from ansible.module_utils.basic import AnsibleModule
import requests



class Backup(object):
    """
    Back up appplications in Google Backup and DR.
    """

    def __init__(self, solarwinds):
        self.changed = False

    def application(self, module):
        # results = None
        have_access = False
        params = module.params

        api_url = params["api_url"].rstrip("/")
        access_token = params["access_token"].rstrip()
        template_name = params["template_name"]
        policy_name = params["policy_name"]
        app_name = params["app_name"]
        label = params["label"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        auth_resp = requests.post(f"{api_url}/session", headers=headers)
        if auth_resp.status_code != 200:
            module.fail_json(changed=False, msg="Failed authentication - ensure you have authenticated with gcloud")

        session_json = auth_resp.json()
        try:
            session_id = session_json["id"]
        except KeyError:
            module.fail_json(msg="Failed to get session ID on authentication")

        try:
            have_access = [True for r in session_json["rights"] if r["id"] == "Access to Backup & Recover"][0]
        except Exception:
            pass

        if not have_access:
            module.fail_json(changed=False, msg="You do not have access to invoke BackupNow")

        headers["backupdr-management-session"] = f"Actifio {session_id}"

        tpl_resp = requests.get(f"{api_url}/slt", headers=headers)
        try:
            tpl_id = [t["id"] for t in tpl_resp.json()["items"] if t["name"] == template_name][0]
        except Exception:
            module.fail_json(msg=f"Failed to retrieve SLA template '{template_name}'")

        pol_resp = requests.get(f"{api_url}/slt/{tpl_id}/policy", headers=headers)
        try:
            pol_id = [p["id"] for p in pol_resp.json()["items"] if p["name"] == policy_name][0]
        except Exception:
            module.fail_json(msg=f"Failed to retrieve SLA template policy '{policy_name}' for SLA template '{template_name}'")

        app_resp = requests.get(f"{api_url}/application", headers=headers)
        try:
            app_id = [a["id"] for a in app_resp.json()["items"] if a["appname"] == app_name][0]
        except Exception:
            module.fail_json(msg=f"Failed to retrieve application '{app_name}'")

        backup_body = {
            "policy": {
                "id": int(pol_id)
            }
        }
        if label:
            backup_body["label"] = label

        backup_resp = requests.post(f"{api_url}/application/{app_id}/backup", headers=headers, json=backup_body)

        if backup_resp.status_code < 200 or backup_resp.status_code > 204:
            module.fail_json(msg=f"Failed to initiate backup of application '{app_name}' (HTTP {backup_resp.status_code}: {backup_resp.json})")

        module.exit_json(changed=True, msg=f"Backup initiated for application '{app_name}'")


# ==============================================================
# main

def main():

    argument_spec = dict(
        api_url=dict(type="str"),
        access_token=dict(type="str"),
        template_name=dict(type="str"),
        policy_name=dict(type="str"),
        app_name=dict(type="str"),
        label=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    backup = Backup(module)

    # check mode: exit changed
    if module.check_mode:
        module.exit_json(changed=True, backup=backup)
    else:
        app_backup = backup.application(module)

    # module.exit_json(**res_args)


if __name__ == "__main__":
    main()
