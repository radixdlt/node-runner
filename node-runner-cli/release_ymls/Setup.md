Below are steps on a Ubuntu 20.04 machine with a user having sudo access


```bash
#Create a directory named where the files related containers are stored 
mkdir radixdlt
# Change to this new directory
cd  radixdlt
```
```bash
#Install necessary tool to run docker containers
sudo apt  install docker.io
sudo apt  install docker-compose
sudo apt install rng-tools
sudo rngd -r /dev/random
```

```bash
# Add user to docker group
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```
```bash
# Download universe.json file from the nodes that are listed for the network
curl -k https://<network node>/universe.json > universe.json
```

```bash
Using docker container 'radixdlt/keygen:1.0-beta.31'  create node key as below
docker run --rm -v ${PWD}:/keygen/key radixdlt/keygen:1.0-beta.31 --keystore=/keygen/key/validator.ks --password=password --keypair-name=node 
sudo chmod 644 validator.ks
```


Download yml as file name - radix-fullnode-compose.yml into radixdlt director

```bash
Bring up the node by running this command
RADIXDLT_NETWORK_NODE=54.82.244.245 RADIXDLT_NODE_KEY_PASSWORD=<password> docker-compose -f radix-fullnode-compose.yml up -d
docker logs -f radixdlt_core_1
```


Mounting radix ledger to external directory

```bash
This is required if you want to map radix ledger to external directory

sudo mkdir /data
sudo chmod 647 /data
```

Add below line under volumes section for docker service core
```bash
        - "core_ledger:/home/radixdlt/RADIXDB"
```

Add below lines under volumes section for the main file
```bash
 core_ledger:
      driver: local
      driver_opts:
        o: bind
        type: none
        device: /data
```



