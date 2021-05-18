## Current State of Node CLI  (  In-progress version for Release 34)



### Docker mode 
#### 1. Configure docker

 ```python3 nodecli.py configure-docker```
##### Description 
   Configures the host to run docker containers. At the end , Instructs user to relogin if they have run this for first time on the host
   
   Command does below on high level
   - Install all dependent packages such as docker.io, unzip, docker-compose, rng-tools and create /dev/random device  
   - Add current user to docker group 
##### OS support  
     - Linux - Ubuntu 20.04 tested
     - Windows - Not supported as package installation and user group setup is linux specific commands


#### 2. Admin password
 ```python3 nodecli.py admin-password -m DOCKER``` 
##### Description 
   Setups nginx password on nginx docker volume. As it uses docker, it supports multi platform.
   
   Prompts user to enter the password during creation and in the end instructs user to set the environment variable so they need not type it everytime
##### OS support   
    - Linux - Instructs to add admin to bashrc file
    - Windows - Instruction needs updated to window plus needs testing


#### 3. Setup docker
 ```
python3 nodecli.py setup-docker  \
      -n <Type of node fullnode or archivenode> \
      -t <IP of trusted node>
 ```

The same command can be run to update the node with `-u` option
  ```python3 nodecli.py setup-docker  \
      -n <Type of node fullnode or archivenode> \
      -t <IP of trusted node>
      -u 
  ```
##### Description 

Pulls down the docker-compose yml for the version hardcoded in the CLI and saves it in directory where command is issued.
  - The version can be overidden for example to `1.0-beta-34` by specifying option `-r 1.0-beta.34`.
  - On update option '-u' , Prompts user asking for backup . If yes, backsup the composefile with current date and time on filename
    
Creates a key file by looking up file named 'validator.ks' in directory where command is issued. 
  - If the file exists, it will ask for the password instead.
  - If the file doesn't exist, it will ask for the password to be used and creates the keystore file
Fetches the universe.json from trusted node and saves it to file in directory where command is issued
Prompts user whether they want to start the docker-compose or not, also prints out the docker-compose file for their inspection
If Yes
  - Brings containers up using  `docker compose up` command with right environment variables.
  - On update option '-u', brings the containers down first and then starts the containers
If No
  exits with the instrutions to start the node using the cli
      
##### OS support
    Linux  
     - Linux - Ubuntu 20.04 tested
     - Windows - Not supported as some steps use linux specific commands


#### 4. Stop Docker 
 ```
python3 nodecli.py stop-docker \
     -f radix-fullnode-compose.yml
``` 
##### Description 
Stops the node using the docker compose file. Volumes can be removed as well by passing option -v

##### OS support   
     Linux  
     - Linux - Ubuntu 20.04 tested
     - Windows - Not supported as some steps use linux specific commands
    
### SystemD mode

#### 1. Configure systemd

 ```python3 nodecli.py configure-systemd```
##### Description 
   Configures the host to run core and nginx as systemd services. At the end , instructs user to update sudoers file and to add  ssh public key
   
   More details are 
   - Install all dependent packages such as docker.io, unzip, docker-compose, rng-tools and create /dev/random device. Docker is still installed so that user can run other containers
   - Installs java
   - Creates unix user named radixdlt and adds it to docker group
   - Creates directories for binaries,config and data 
   - Creates password the unix user `radixdlt` by prompting user to enter.
   - Create the systemd service file  (This needs to be verified if it is idempotent) 

   
  Command is idempotent for most of the things, needs bit more testing
  
##### OS support  
     - Linux - Ubuntu 20.04 tested
     - Windows - Not valid as systemd is in linux setup process only
     
   
#### 2. Admin Password
 ```python3 nodecli.py admin-password -m SYSTEMD``` 
##### Description 
   Installs nginx package and  setups nginx password using htpasswd utility. 
   Prompts user to enter the password during creation and in the end instructs user to set the environment variable so they need not type password everytime
##### OS support   
    - Linux - Instructs to add admin to bashrc file
    - Windows - Not valid as systemd is in linux setup process only


#### 3. Start SystemD

  ```
python3 nodecli.py start-systemd \
  --trustednode <IP of trustednode> \
  --nodetype <fullnode or archivenode> \
  --hostip <hostip>
  ```

The same command can be run to update the node with `-u` option
  ```
python3 nodecli.py start-systemd \
  --trustednode <IP of trustednode> \
  --nodetype <fullnode or archivenode> \
  --hostip <hostip>
  -u
  ```
##### Description 
       

######  Node  
 
Creates a key file by looking up file named 'validator.ks' in directory /etc/radixdlt/node/secrets. 
  - If the file exists, it will ask for the password instead.
  - If the file doesn't exist, it will ask for the password to be used and then only create the keystore file
  
For below files, it creates them if they don't exist or back up them onto a directory with current date and time in the location where the cli in run
  - /etc/radixdlt/node/secrets/environments ( Uses keystore password and hardcoded Java opts)
  - /etc/radixdlt/node/default.config ( Uses hardcoded file content)
  - /etc/systemd/system/radixdlt-node.service (currently not prompted for backup. needs updating)

Pulls down the binaries of node for the version hardcoded in the CLI . Unzip them in the location where cli command is run and moved to /etc/radixdlt/node/<version> folder.
  - The version can be overidden for example to `1.0-beta-34` by specifying option `-r 1.0-beta.34`.
  - On update option '-u', there is nothing specifically done in this step as files are copied into version directory. 
  - Command can be rerun for the same version, but needs bit of testing
 
Fetches the universe.json from trusted node and saves it to file in directory /etc/radixdlt/node.

On Update, it restarts the node service
  
######   Nginx  
    Prompts for nginx back up. If yes, it creates backup direcgtory (again this directory checked before creating) and then backs up /etc/nginx directory.
    Then Prompts asking to continue setup nginx . If Yes, then Pulls down the binaries of nginx for the version hardcoded in the CLI. Unzip them in the location where cli command is run and moved over to "/etc/nginx" directory
    Creates nginx certificates, if exists prompts for recreation Y/N
    
    On Update, it restarts the nginx service

      
##### OS support
    Linux  
     - Linux - Ubuntu 20.04 tested
     - Windows - Not supported as some steps use linux specific commands


### Interaction with node using rest API
 
##### OS support on API interactions
    Supports multiple environments as it uses python packages. For windows we need to install the package named requests separately.
    
##### Nginx authentication
Nginx authentication is automatically added by looking up from environment variable. If the environment variable isn't setup, exits with instruction to setup the variable. Instructions needs to updated for windows


#### 1. Fetch the node address
 ```python3 nodecli.py nodeaddress``` 
##### Description 
   Issues command to /node endpoint. Needs updating when we make changes to rest endpoints and prints out json response


#### 2. Register your node as validator 
 ```python3 nodecli.py registervalidator``` 
##### Description 
Issues command to /node endpoint to register validator. It prompts user for below information and then issues regestration command
- "Name of your validator:"
- "Url of your validator:"
And then prints out json response
  
#### 3. Show peers
 ```python3 nodecli.py peers``` 
##### Description 
   Issues command to /system/peers endpoint and then prints out json response
   
#### 4. Show validator
 ```python3 nodecli.py showvalidator``` 
##### Description 
   Issues command to /node/validator endpoint and then prints out json response
    
#### 4. System info
 ```python3 nodecli.py systeminfo``` 
##### Description 
   Issues command to /system/info endpoint and then prints out json response
    
    

### Monitoring setup
 
Monitoring setup needs metrics exporter to export the metrics from node, prometheus to index the metrics and grafana to display the visualisation.

##### OS support on API interactions
      Tested on ubutnu 20.04, but on windows needs testing. Uses cross platform library to pull down the files/config, but needs to tested for docker compose commands

      
 #### 2. Setup monitoring
 Command
 - ```python3 nodecli.py setup-monitoring``` 
##### Description 
This command fetches files from the release the nodecli is pointing to. It fetches and save below files into directory named monitoring
- node-monitoring.yml for the containers metric exporter, prometheus, grafana
- prometheus.yaml for prometheus config
- grafana dashboard and datasource files

Creates external volumes for prometheus and grafana and then starts the containers for monitoring using the docker-compose file
    
##### OS support   
    - Linux - Instructs to add admin to bashrc file
    - Windows - Instruction needs updated to window plus needs testing

##### Challenges
Current setup assumes only monitoring on system endpoint and uses https 443 port on the node to scrape the metrics. 
Although this option gives one ability to run these containers outside the machine that is running node,
user has to setup montioring for host level metrics and jmx monitoring etc.

With two configuration to support - SystemD and Docker, the above approach works but not ideal.
    
##### Proposed setup
Based on whether user has setup radix node as docker or systemd, the metrics exporter can be run differently
- If docker, then run the metrics exporter container by attaching to existing docker node network
- If systemD, then run the metrics exporter with host level network so that it can scrape endpoint on host level ports

Prometheus can be setup as container by prompting user if we wants to run this on the node. As user is just monitoring one node, there is not much harm in setting this up on same host as radix node. But the process utilisation /capacity needs to revisted
Again based on systemD or docker it needs to be setup like metrics exporter

Grafana we suggest is setup outside the radix node. But this will hinder the user realising benefits from quick setup. 
Again as promethues this can be promted for user if want to setup and set it up as container similar to prometheus

To avoid users to expose more ports and setup protection for them, we can reroute all this through existing nginx.
Nginx config needs to be updated to have
- https://localhost/promethues to <promethues_container_name>:9090/prometheus
- https://localhost/grafana to <grafana_container_name>:3000

These config can be setup by default so that it avoids few environment variables on the docker or systemd config.


 #### 2. Stop monitoring
 Command
 - ```python3 nodecli.py stop-monitoring``` 
##### Description 
    Stops the monitoring using docker-compose file node-monitoring.yml
    
##### OS support   
    - Linux - Instructs to add admin to bashrc file
    - Windows - Instruction needs updated to window plus needs testing

