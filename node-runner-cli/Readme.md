This is node runner cli which can be used for Ubuntu 20.04 to bring the nodes and query endpoints. It uses python3 which comes installed on Ubuntu 20.04 and all modules that are inbuild in python3.
One can find the hardware/OS specification for the node can be found [here](https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment)

##nodecli script
The nodecli.py script helps to run node in two modes - Docker compose and Systemd. It has inbuilt help which you can check by running below


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

#### Setup nginx password if node is run on Docker
```shell script
python3 nodecli.py admin-password -m DOCKER
```

#### To bring up the node in Docker mode
Below command is using 1.0-beta.32 release. Pick up the latest yml from latest release from this [location](https://github.com/radixdlt/radixdlt/releases/)

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

#### Setup nginx password if node is run on Docker
```shell script
python3 nodecli.py admin-password -m SYSTEMD
```

#### To bring up the node in systemD mode
Below command is using 1.0-beta.32 release. 

For radix core distribution, _option -b or --nodebinaryUrl_, pick up the latest radixdlt-dist zip file from latest release from this [location](https://github.com/radixdlt/radixdlt/releases/). 

For nginx config distribution, _option -c or --nginxconfigUrl_, pick up the latest archive node or full node zip files from this [location](https://github.com/radixdlt/radixdlt-nginx/releases/)

Option _-t or --trustednode_ requires a node from radix network. You can get an ip from  list  in this [location](https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment)

Option _-n or -nodetype_  is one of two nodes - archive or fullnode

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


