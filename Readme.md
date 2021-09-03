
# Node cli

## Introduction:

Executable name - radixnode

All the below commands can be executed on Ubuntu 20.04 ( supported OS) as below

```
radixnode <sub command>
```

To download the cli, following instructions from [here](https://docs.radixdlt.com/main/node/cli-install.html)

The main purpose of this cli is to enable node runners

1. To interact with node using common API calls
2. To setup node quickly on a fresh ubuntu machine using docker compose or systemd
3. To setup monitoring for the node. Currently supports monitoring the API exposed by the node.

## Interaction with node on api endpoints


To list the endpoints supported by cli 
```shell script
$ radixnode api


usage: radixnode [-h]
                 {validation,account,health,version,universe,metrics,system}
radixnode: error: the following arguments are required: apicommand
```

To list the methods supported by the endpoints say for example account endpoint

```shell script
$radixnode api account
usage: radixnode [-h] {register-validator,unregister-validator,get-info} ...

account commands

positional arguments:
  {register-validator,unregister-validator,get-info}
```


| **Sub Commands** | **Options** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| api account get-info | - | - | Returns the response from POST request using get_info method on /account |
| api account register-validator | - |<ul><li>1. Name of your validator:</li><li>2. Info URL of your validator:</li></ul>| Returns the response on POST using register_validator method on /account  |
| api account unregister-validator | - |-| Returns the response on POST using unregister_validator method on /account  |
| api validation get-validator-info | - | - | Returns the response of POST request using get_validator_info method on /validation  |
| api validation get-current-epoch-data | - | - | Returns the response of POST request using get_current_epoch_data method on /validation  |
| api health | - | - | Returns the response of GET request on /health endpoint  |
| api version | - | - | Returns the response of GET request on /version endpoint  |
| api universe | - | - | Returns the response of GET request on /universe endpoint  |
| api metrics | - | - | Returns the response of GET request on /metrics endpoint  |
| api metrics | - | - | Returns the response of GET request on /metrics endpoint  |
| api system api-get-configuration | - | - | Returns the response of POST request using api_get_configuration on /system endpoint  |
| api system api-get-data | - | - | Returns the response of POST request using api_get_data on /system endpoint  |
| api system bft-get-configuration | - | - | Returns the response of POST request using bft_get_configuration on /system endpoint  |
| api system bft-get-data | - | - | Returns the response of POST request using bft_get_data on /system endpoint  |
| api system mempool-get-configuration | - | - | Returns the response of POST request using mempool_get_configuration on /system endpoint  |
| api system mempool-get-data | - | - | Returns the response of POST request using mempool_get_data on /system endpoint  |
| api system ledger-get-latest-proof | - | - | Returns the response of POST request using ledger_get_latest_proof on /system endpoint  |
| api system ledger-get-latest-proof | - | - | Returns the response of POST request using ledger_get_latest_proof on /system endpoint  |
| api system ledger-get-latest-epoch-proof | - | - | Returns the response of POST request using ledger_get_latest_epoch_proof on /system endpoint  |
| api system radix-engine-get-configuration | - | - | Returns the response of POST request using radix_engine_get_configuration on /system endpoint  |
| api system radix-engine-get-data | - | - | Returns the response of POST request using radix_engine_get_data on /system endpoint  |
| api system sync-get-configuration | - | - | Returns the response of POST request using sync_get_configuration on /system endpoint  |
| api system sync-get-data | - | - | Returns the response of POST request using sync_get_data on /system endpoint  |
| api system networking-get-configuration | - | - | Returns the response of POST request using networking_get_configuration on /system endpoint  |
| api system networking-get-data | - | - | Returns the response of POST request using networking_get_data on /system endpoint  |
| api system checkpoints-get-checkpoints | - | - | Returns the response of POST request using checkpoints_get_checkpoints on /system endpoint  |



## Setup/Update docker

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| docker configure| - | - | Prints out instruction to logout and login at the end if required |
| docker setup |-n or --nodetype <(fullnode or archivenode>, required,<br/> -t or --trustednode <IP of node on network>, required. <br/> -u or --update, optional| <br/>- Displays URL of composefile being used and prompts to continue <br/>- Prompts to back up the file, if the compose file exists <br/>- Prompts about generation of key if doesn&#39;t exist or just the password if key already exists <br/>- Displays the compose file asking user to start the node with Y/n| <br/> -Setups the docker compose file for the node type <br/> -Create key if not present and then asks for password <br/>- Prints out instruction to stop and start the docker containers, if user chooses not to start the containers at the end |
| docker start |<br/> -t or --trustednode <IP of node on network>, required.<br/> -f or --composefile <name of the composefile>required|<br/>- Prompts about generation of key otherwise just password if key already exists| Setups the environment variables and brings up the container |
| docker stop |<br/> -f or --composefile <name of the composefile>,required <br/>-v or --removevolumes, optional|| Stops the docker containers and removes volumes if one wants to clear the volumes. Externally mounted volumes won&#39;t be cleared even with -v option |

## Setup/Update systemd

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| systemd configure |-|<br/>- Prompts for radixdlt user password| Prints out instructions to edit sudoers file and add public ssh key for password less login |
| systemd setup |<br/> -r or --release <releasetag>, optional defaults to latest radixdlt release (core software)<br/> -x or --nginxrelease optional, defaults to latest radixdlt-nginx release<br/> <br/> -n or --nodetype <fullnode or archivenode>, required,<br/> -t or --trustednode <IP of radixnode on network>, required.<br/> -i or --hostip <ip of the host>,required<br/> -u or --update, optional|<br/>- Displays URL of node binary and nginx binary being downloaded and prompts to continue<br/>- Prompts to back up files for node service, if the below files exists<br/>-- environment<br/> -- config<br/> -- radixdlt-node.service<br/> - Prompts if user wants to setup nginx. If yes , then prompts for backup on existing nginx files<br/> - Prompts for existing nginx secrets before recreating them||
| systemd restart |-|-||
| systemd stop  |<br/> -s or --services <nginx or radixdlt-node>, defaults=all|-| Stop the service based on the option. If option not provided , it stops both |

## Nginx Passwords

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| auth set-admin-password |<br/> -m or --setupmode 'DOCKER or SYSTEMD', required|<br/>- Prompts for nginx admin password to be changed or to be setup||
| auth set-superadmin-password |<br/> -m or --setupmode 'DOCKER or SYSTEMD', required|<br/>- Prompts for nginx admin password to be changed or to be setup||
| auth set-metrics-password |<br/> -m or --setupmode 'DOCKER or SYSTEMD', required|<br/>- Prompts for nginx admin password to be changed or to be setup||

## Monitoring

| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| monitoring setup |-|-| Uses hardcoded cli version to download the aritfacts. Creates external volumes for prometheus and grafana and starts up the monitoring containers |
| monitoring start |-|-| Starts the docker containers related to monitoring |
| monitoring stop |<br/> -v or --removevolumes|-| Stops the docker containers and removes volumes if one wants to clear the volumes. Externally created/mounted volumes won&#39;t be cleared even with -v option |

# Other commands
| **Sub Commands** | **Arguments** | **Prompts** | **Comments** |
| --- | --- | --- | --- |
| optimise-node |-|<br/>- Prompts asking to setup limits <br/>- Prompts asking to setup swap and size of swap in GB|- |
|version |-|-|Prints out the version of cli |


### More usage instructions

To list all subcommands
```shell script
# To list the subcommands
radixnode -h
usage: radixnode.py [-h]
                    {docker,systemd,api,monitoring,version,optimise-node,auth}

positional arguments:
  {docker,systemd,api,monitoring,version,optimise-node,auth}
                        Subcommand to run

optional arguments:
  -h, --help            show this help message and exit
```

To list options/arguements for the subcommand
```shell script
# Check the options for a subcommand such as start-docker
radixnode docker -h

usage: radixnode.py [-h] {setup,start,stop,configure} ...

Docker commands

positional arguments:
  {setup,start,stop,configure}

optional arguments:
  -h, --help            show this help message and exit

```
