

This is node runner cli which can be used for Ubuntu 20.04 to bring up the node and query endpoints. It uses python3 which comes installed on Ubuntu 20.04 and all modules that are inbuild in python3.
One can find the hardware/OS specification for the node [here](https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment)

## nodecli script
The nodecli.py script helps to run node in two modes - Docker compose and Systemd. It has inbuilt help which you can check by running below. User running this script should have sudo without password access.


### Installation
wget  -O  nodecli.py https://github.com/radixdlt/node-runner/releases/download/<latest version>/nodecli.py


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

Download the latest release of script by running command. Latest release can be found [here](https://github.com/radixdlt/node-runner/releases)

```shell script
wget  -O  nodecli.py <url_to_latest_location>
```

## Docker compose mode

#### To check if python is installed
```shell script
# Python3 comes default on ubuntu20.04
which python
```

#### To install all necessary packages and configure user for Docker Mode
```shell script
python3 nodecli.py configure-docker
```
If you have run this command for first time, command will split out instruction to logout and log back in

#### Setup nginx password if node is run on Docker
```shell script
python3 nodecli.py admin-password -m DOCKER
```

#### To bring up the node in Docker mode
Below command is using 1.0-beta.32 release. Pick up the latest yml from latest release [location](https://github.com/radixdlt/radixdlt/releases/)

-t or --trustednode option requires a node from radix network. You can get an ip from  list  in this [location](https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment)
 
```shell script
python3 nodecli.py start-docker  \
 -f https://github.com/radixdlt/radixdlt/releases/download/1.0-beta.32/radix-fullnode-compose.yml \
 -t 52.48.95.182
```

#### To stop the node in Docker mode
```shell script
python3 nodecli.py stop-docker
```

## SystemD mode
#### To install all necessary packages and configure user for SystemD mode

```shell script
python3 nodecli.py configure-systemd
```
If you have run this command for first time, command will split out instructions to carry out before running next command


#### Setup nginx password if node is run on SystemD
```shell script
python3 nodecli.py admin-password -m SYSTEMD
```

#### To bring up the node in systemD mode
Below command is using 1.0-beta.32 release. 

For radix core distribution url, _option -b or --nodebinaryUrl_, pick up the url of latest radixdlt-dist zip file from latest release from this [location](https://github.com/radixdlt/radixdlt/releases/). 

For nginx config distribution url, _option -c or --nginxconfigUrl_, pick up the url of latest archive node or full node zip files from this [location](https://github.com/radixdlt/radixdlt-nginx/releases/)

Option _-t or --trustednode_ requires a node from radix network. You can get an ip from  list  in this [location](https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment)

Option _-n or -nodetype_  is one of two nodes - archive or fullnode and should match to nginx config distribution url

Option _-i or --hostip_ is the static IP of your node

```shell script
python3 nodecli.py start-systemd \
 -b https://github.com/radixdlt/radixdlt/releases/download/1.0-beta.32/radixdlt-dist-1.0-beta.32.zip \
 -c https://github.com/radixdlt/node-runner/releases/download/v1.4.0/radixdlt-nginx-archive-conf.zip \
 -t 52.48.95.182 \
 -n archive \
 -i 18.132.198.185
```


## Interact with node API

#### To fetch the node address 
```shell script
python3 nodecli.py nodeaddress
```

#### To register your node as validator
```shell script
python3 nodecli.py registervalidator
```

#### To show your validator info
```shell script
python3 nodecli.py showvalidator
```

##Monitoring
####Installation
The monitoring setup uses system/info endpoint and requires nginx admin password. Run below command by replacing you nginx admin password 
```shell script
NGINX_ADMIN_PASSWORD=<your_nginx_admin_password> python3 nodecli.py setup_monitoring
```
This command, fetches the file from the release, that the `nodecli.py` is pointing to.  If for any reasons, one wants to update the configs,  one can download initial version using above command 
To update the config, one has to bring down the monitoring using below `stop-monitoring` command

If the monitoring is setup on different instance/machine, one can pass the IP as below

```shell script
NGINX_ADMIN_PASSWORD=<your_nginx_admin_password> NODE_END_POINT=https://<your node IP> python3 nodecli.py setup_monitoring
```


#### Stopping monitoring
```shell script
python3 nodecli.py stop_monitoring
```

#### Restarting the monitoring
One can restart the monitoring using updated config files by running below command. 
```shell script
BASIC_AUTH_USER_CREDENTIALS=admin:<your_nginx_admin_password>  NODE_END_POINT=https://<your node IP> docker-compose -f monitoring/node-monitoring.yml up -d
```
`<your node IP>` - your node's ip. localhost will not work even though you may be running on same machine as this variable is referenced inside docker container of metrics exporter


#### Viewing dashboard
Grafana can be accessed on port 3000. The monitoring can be setup on different machine or on same machine where the node runs.
If the monitoring is setup on same instance as node , to access the dashboard outside the node, one has to open up the port 3000 for grafana. 
If it is on different instance, then firewall on that instance needs to allow traffic on port 3000
Then nn any browser type http://<node-ip>:3000 to access the grafana. For the first time , the password admin/admin allows you to login. Then change the grafana admin password to something of your choice

