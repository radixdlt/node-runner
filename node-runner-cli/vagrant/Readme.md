Purpose of using Vagrant is to bring up the machine quickly on the local machine for quick testing.

Prerequisites
####
You will need to [install VirtualBox](https://www.virtualbox.org/wiki/Downloads) before you can use the Vagrant VM setup.

Usage
#### 
Run below command to bring the up the VM described in vagarantfile

```
vagrant up
```

Once machine is up, user can ssh into machine using

```
vagrant ssh
```

Then change the directory to where the cli is synced from host. It would something along the lines
`/home/vagrant/node-runner/out/ubuntu/focal`

Run the command to test cli 

```
radixnode -h
```

To stop the VM

```shell script
vagrant halt

```

To destroy the VM

```shell script
vagrant destroy
```
