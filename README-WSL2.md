# Working with WSL2

You can do this tutorial on WSL2 with some caveats. WSL2 is a fully functional linux environment in windows, but, by default, no systemd is running. This means systemd services are not started up on boot.

For instance, while you can install docker just like on linux, docker won't start up automatically. You'll have to start up docker (every time you reboot).

Here is a list of things you have to do when working on wsl2. The easiest way to accomplish this is to make a set of little scripts you can run every time you need to do one of these actions.

## Starting docker

For starting docker, we create a little script `start-docker.sh` that just starts docker if it isn't running already.

```shell
#!/bin/bash

RUNNING=$(ps ax | grep dockerd | grep sudo)

if [ -z "$RUNNING" ]; then
    sudo dockerd > /dev/null 2>&1 &
    disown
fi
```

## Shutting down docker

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

RUNNING_PID=$(ps ax | grep "k3s server" | grep sudo | awk '{print $1;}')

if [ -n "$RUNNING_PID" ]; then
    sudo kill $RUNNING_PID
fi

sudo k3s-killall.sh
```
