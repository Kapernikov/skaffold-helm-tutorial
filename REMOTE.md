# Working on this tutorial remotely

There are two options for working remotely:

* install all client tools locally and then copy the .kube/config from the remote host to your local filesystem. Then you can do kubernetes-related stuff locally.
* work remotely complete using visual studio code.

This document describes the second option.

## Installing visual studio code

* Install visual studio code from microsoft website. its not too big so it should be quick.
* install the "remote ssh" plugin

Then make your own life comfortable and set up passwordless ssh (no idea if this works on windows):

```shell
[ -f ~/.ssh/id_rsa.pub ] || ssh-keygen
ssh-copy-id [USER]@[ip-of-remote]
```

## Connecting to the remote host

Either use the remote explorer (sidebar icon: ![sidebar icon](imgs/vscode-remote-explorer.png "screenshot")) or use the only shortcut you have to remember in VScode: bring the quick menu (`Ctrl-shift-P`) and:

![connect to ssh](imgs/vscode-quickmenu.png "screenshot of quick menu")

Now just do [USER]@[ip-of-remote]

## Forwarding necessary ports

In the bottom bar, there should be a way to open terminals on the remote host now. There should be a tab "ports" where you can forward ports:

![Port forwarding in VS code](imgs/port-forward-vscode.png "screenshot")

For this excercise, forward the following ports:
* 8888
* 9999
