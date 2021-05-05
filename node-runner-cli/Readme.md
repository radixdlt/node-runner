This is node runner cli which can be used for Ubuntu 20.04 to bring the nodes and query endpoints. It uses python3 which comes installed on Ubuntu 20.04 and all modules that are inbuild python3.
Specification for the node requirements can be found here https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment
## Docker compose mode

### To check if python is installed
```shell script
which python
```

### To install all necessary packages and configure user for Docker Mode

```shell script
python3 nodecli.py configure-docker
```

### Setup nginx password if node is run on Docker
```shell script
python3 nodecli.py admin-password -m DOCKER
```

### To bring up the node in Docker mode
Below command is using 1.0-beta.32 release. Pick up the latest yml from latest release from this location
https://github.com/radixdlt/radixdlt/releases/

-t or --trustednode option requires a node from radix network. You can get an ip from  list  in this location
https://docs.radixdlt.com/documentation-component/betanet/radix-nodes/running-a-full-node.html#_setting_up_your_environment
 
```shell script
python3 nodecli.py start-docker  \
 -f https://github.com/radixdlt/radixdlt/releases/download/1.0-beta.32/radix-fullnode-compose.yml \
 -t 52.48.95.182
```

### To stop the node in Docker mode
```shell script
python3 nodecli.py stop-docker
```

## SystemD mode
### To install all necessary packages and configure user for SystemD mode

```shell script
python3 nodecli.py configure-systemd
```

### Setup nginx password if node is run on Docker
```shell script
python3 nodecli.py admin-password -m SYSTEMD
```

### To bring up the node in systemD mode
Below command is using 1.0-beta.32 release. 

For radix core , pick up the latest radixdlt-dist zip file from latest release from this location
https://github.com/radixdlt/radixdlt/releases/. 

For nginx config, pick up the latest archive node or full node zip files from this location
https://github.com/radixdlt/radixdlt-nginx/releases/

```shell script
python3 nodecli.py start-systemd \
 -b https://github.com/radixdlt/radixdlt/releases/download/1.0-beta.32/radixdlt-dist-1.0-beta.32.zip \
 -c https://github.com/radixdlt/node-runner/releases/download/v1.4.0/radixdlt-nginx-archive-conf.zip \
 -t 52.48.95.182 \
 -n archive \
 -i 18.132.198.185
```



## Interact with node API

### To fetch the node address 
```shell script
python3 nodecli.py nodeaddress
```

### To register your node as validator
```shell script
python3 nodecli.py registervalidator
```

### To show your validator info
```shell script
python3 nodecli.py showvalidator
```


