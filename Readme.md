
# Node cli

## Introduction:

Executable name - radixnode

All the below commands can be executed on Ubuntu 20.04 ( supported OS) as below

**./radixnode <sub command>**

The main purpose of this cli is to enable node runners

1. To interact with node using common API calls
2. To setup node quickly on a fresh ubuntu machine using docker compose or systemd
3. To setup monitoring for the node. Currently supports on API monitoring.

## Interaction with node

| **Sub Commands** | **Options** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| get-node-address | - | - | Returns the response on GET /node |
| get-peers | - | - | Returns the response on GET /system/peers |
| register-validator | - |<ul><li>1. Name of your validator:</li><li>2. Info URL of your validator:</li></ul>| Returns the response on POST /node/execute |
| validator-info | - | - | Returns the response on POST /node/validator |
| system-info | - | - | Returns the response on POST /system/info |


## Setup/Update docker

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| configure-docker | - | - | Prints out instruction to logout and login at the end if required |
| setup-docker |<br/> -r or --release <releasetag>, required <br/> -n or --nodetype <(fullnode or archivenode>, required,<br/> -t or --trustednode <ip of node on network>, required. <br/> -u or --update, optional| <br/>- Displays url of composefile being used and prompts to continue <br/>- Prompts to back up the file, if the compose file exists <br/>- Prompts about generation of key if doesn&#39;t exist or just the password if key already exists <br/>- Displays the compose file asking user to start the node with Y/n| Setups the docker compose file for the node typeCreate key if not present and then asks for passwordPrints out instruction to stop and start the docker containers, if user chooses not to start the containers at the end |
| start-docker |<br/> -t or --trustednode <ip of node on network>, required.<br/> -f or --composefile <name of the composefile>required|<br/>- Prompts about generation of key otherwise just password if key already exists| Setups the environment variables and brings up the container |
| stop-docker |<br/> -f or --composefile <name of the composefile>,required <br/>-v or --removevolumes, optional|| Stops the docker containers and removes volumes if one wants to clear the volumes. Externally mounted volumes won&#39;t be cleared even with -v option |

## Setup/Update systemd

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| configure-systemd ||<br/>- Prompts for radixdlt user password| Prints out instructions to edit sudoers file and add public ssh key for password less login |
| start-systemd |<br/> -r or --release <releasetag>, required<br/> -n or --nodetype <fullnode or archivenode>, required,<br/> -t or --trustednode <ip of radixnode on network>, required.<br/> -i or --hostip <ip of the host>,required<br/> -u or --update, optional|<br/>- Displays url of node binary and nginx binary being downloaded and prompts to continue<br/>- Prompts to back up files for node service, if the below files exists<br/>-- environment<br/> -- config<br/> -- radixdlt-node.service<br/> - Prompts if user wants to setup nginx. If yes , then prompts for backup on existing nginx files<br/> - Prompts for existing nginx secrets before recreating them||
| stop-systemd |<br/> -s or --services <nginx or radixdlt-node>, defaults=all|| Stop the service based on the option. If option not provided , it stops both |

## Nginx Passwords

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| set-admin-password |<br/> -m or --setupmode <DOCKER or SYSTEMD>, required|<br/>- Prompts for nginx admin password to be changed or to be setup||

## Monitoring

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| setup-monitoring ||| Uses hardcoded cli version to download the aritfacts. Creates external volumes for prometheus and grafana and starts up the monitoring containers |
| stop-monitoring |<br/> -v or --removevolumes|| Stops the docker containers and removes volumes if one wants to clear the volumes. Externally created/mounted volumes won&#39;t be cleared even with -v option |

### More usage instructions

To list all subcommands
```shell script
# To list the subcommands
python3 nodecli.py --help

usage: nodecli.py [-h]
                  {start-docker,start-systemd,stop-docker,configure-docker,configure-systemd,admin-password,nodeaddress,peers,registervalidator,showvalidator,systeminfo}
                  ...

positional arguments:
  {start-docker,start-systemd,stop-docker,configure-docker,configure-systemd,admin-password,nodeaddress,peers,registervalidator,showvalidator,systeminfo}

optional arguments:
  -h, --help            show this help message and exit
```

To list options/arguements for the subcommand
```shell script
# Check the options for a subcommand such as start-docker
python3 nodecli.py start-docker -h

usage: nodecli.py start-docker [-h] -f COMPOSEFILEURL -t TRUSTEDNODE

optional arguments:
  -h, --help            show this help message and exit
  -f COMPOSEFILEURL, --composefileurl COMPOSEFILEURL
                        URl to download the docker compose file
  -t TRUSTEDNODE, --trustednode TRUSTEDNODE
                        Trusted node on radix network
```
