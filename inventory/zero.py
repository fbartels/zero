#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess

try:
    import json
except ImportError:
    import simplejson as json


class ZeroInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.zero_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.zero_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print(self.inventory)

    # Example inventory for testing.
    def zero_inventory(self):
        inventory = {
            "all": {
                "hosts": []
            },
            "_meta": {
                "hostvars": {}
            }  
        }

        # Check if TERRAFORM_ENABLED is set
        terraform_enabled = int(os.getenv('TERRAFORM_ENABLED', 0))

        # Check if ZERO_NODES is set
        if not terraform_enabled:
            # We're running on a custom inventory
            zero_nodes = os.getenv('ZERO_NODES', "")

            if zero_nodes and zero_nodes != "":
                i = 1
                #node_count = zero_nodes.split(",").length
                for node in zero_nodes.split(","):
                    inventory['all']['hosts'].append("zero-{}".format(i))
                    inventory['_meta']['hostvars']["zero-{}".format(i)] = {
                        "ansible_host": node
                    }
                    i += 1
                
                # Set Docker Group
                inventory["docker"] = []
                for node in inventory['all']['hosts']:
                    inventory["docker"].append(node)

                # Set Manager Group
                inventory["manager"] = []
                for node in inventory['all']['hosts']:
                    inventory["manager"].append(node)
                
                # Set Swarm Group
                inventory["swarm"] = {
                    "children": ["docker"]
                }

                # Set Storidge Group
                inventory["storidge"] = {
                    "children": ["manager"]
                }
            inventory = json.dumps(inventory)
        else:
            inventory_path = os.path.dirname(os.path.abspath(__file__))
            tf_path = "{}/{}".format(inventory_path,"../terraform/")
            os.environ["TF_STATE"] = tf_path
            os.environ["TF_HOSTNAME_KEY_NAME"] = "name"
            args = sys.argv[1:]
            command = ["/usr/local/bin/terraform-inventory"] + args + [tf_path]
            process = subprocess.run(command, check=True, stdout=subprocess.PIPE, universal_newlines=True)
            inventory = process.stdout
    
        return inventory

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

# Get the inventory.
ZeroInventory()