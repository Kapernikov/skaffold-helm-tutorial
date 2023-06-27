# Working with WSL2

You can do this tutorial on WSL2 with some caveats. WSL2 is a fully functional linux environment in windows, but, by default, no systemd is running. This means systemd services are not started up on boot.

For instance, while you can install docker just like on linux, docker won't start up automatically. You'll have to start up docker (every time you reboot).

Here is a list of things you have to do when working on wsl2. The easiest way to accomplish this is to make a set of little scripts you can run every time you need to do one of these actions.


## Make hostnames available in WSL and Windows
This is an adapted version of the explanation given in [chapter 3](chapters/03-install-k3s.md#installing-docker-registry) 
to create a script `update_hosts_file.sh`.

First, give your Windows user explicit writing permissions to the file `C:\Windows\System32\drivers\etc\hosts`. 
By default, this file is read-only and you need privilege elevation to edit it. Elevation doesn't work if you want to 
access this file through WSL, so your Windows user (that runs WSL) needs explicit write access to the file in the normal way.  
Right-click on the file --> Properties --> Security --> Edit... --> Add... --> Select your user and give them Modify and Write access.

Put the hostnames you want in `/etc/update_hosts_file/aliases` (put them all on the same line, separated by spaces). Don't put comments in that file!

```shell
#!/bin/sh

cat << 'END' | sudo tee /usr/local/bin/update_hosts_file.sh
#!/bin/bash

export MYIP=$(/usr/bin/hostname -I | cut -d' ' -f1)
export ALIASES=$(cat /etc/update_hosts_file/aliases)

# Update the hosts file on WSL
export HOSTS_FILE=/etc/hosts
sed -i '/UPDATE_HOSTS_FILE/d' $HOSTS_FILE
echo "$MYIP $ALIASES ### UPDATE_HOSTS_FILE from /etc/update_hosts_file/aliases" | tee -a $HOSTS_FILE

# Update the hosts file on Windows
export HOSTS_FILE=/mnt/c/Windows/System32/drivers/etc/hosts
export TEMP_FILE=mktemp
# We cannot use sed -i because that creates a temp file in the same folder as the file 
# and your WSL doesn't have write access to that folder. We need to pass through a temp file that we creates ourselves.
cat $HOSTS_FILE | sed '/UPDATE_HOSTS_FILE/d' > $TEMP_FILE
cat $TEMP_FILE > $HOSTS_FILE
echo "$MYIP $ALIASES ### UPDATE_HOSTS_FILE from /etc/update_hosts_file/aliases" | tee -a $HOSTS_FILE
rm $TEMP_FILE

END

sudo chmod a+x /usr/local/bin/update_hosts_file.sh

sudo mkdir -p /etc/update_hosts_file

[[ -f /etc/update_hosts_file/aliases ]] || echo "registry.kube-public" | sudo tee /etc/update_hosts_file/aliases
```




## Scripts for starting and stopping docker

If you're not using Docker Desktop for Windows, you need a docker installation inside the WSL distribution you are using. The following scripts can come in handy for starting or stopping the docker daemon.

If you use Docker Desktop, just start it and enable the WSL integration for your WSL distribution. These scripts are not relevant then.


### Starting docker

For starting docker, we create a little script `start-docker.sh` that just starts docker if it isn't running already.
At the same time, we invoke the script `update_hosts_file.sh` we created above, because this doesn't run automatically on WSL2 either as long as we don't have systemd running there.

```shell
#!/bin/bash

sudo update_hosts_file.sh

RUNNING=$(ps ax | grep dockerd | grep sudo)

if [ -z "$RUNNING" ]; then
    sudo dockerd > /dev/null 2>&1 &
    disown
fi
```

### Shutting down docker

If you want to restart docker, you'll need to be able to shut it down. `stop-docker.sh` could look like this:

```shell
#!/bin/bash

RUNNING_PID=$(ps ax | grep dockerd | grep sudo | awk '{print $1;}')

if [ -n "$RUNNING_PID" ]; then
    sudo kill $RUNNING_PID
fi
```

## Starting K3S

For starting k3s, `start-k3s.sh` could look like this:

```shell
#!/bin/bash

RUNNING=$(ps aux | grep "k3s server" | grep -v grep)
if [ -z "$RUNNING" ]; then
    sudo k3s server > /dev/null 2>&1 &
    disown
fi
```

## Stopping K3S

And finally, `stop-k3s.sh`:

```shell
#!/bin/bash

RUNNING_PID=$(ps ax | grep "k3s server" | grep -v grep | awk '{print $1;}')

if [ -n "$RUNNING_PID" ]; then
    sudo kill $RUNNING_PID
fi

sudo k3s-killall.sh
```
