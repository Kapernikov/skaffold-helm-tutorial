## Installing a more capable storage backend (optional)

The default hostpath provisioner (also in use by the other solutions) will, whenever a storage volume is needed, just take a folder on the machine you are running on. That's fine for experimenting, but will fail quickly in multi-node clusters: because these folders are not shared amongst the nodes, once created, a pod will never be able to move to another node, and you will not be able to share data between pods running on different nodes.

[NFS Ganesha](https://nfs-ganesha.github.io/) allows for shared (RWX) volumes by taking a system-provided volume and launching a userspace NFS server on it. Not really suitable for running production loads, but it's lightweight (only 1 pod), so ideal for the tutorial.

```shell
# need nfs utilities on the host. that's the only dependency!
sudo apt -y install nfs-common
sudo systemctl stop  portmap.service rpcbind.socket rpcbind.service
sudo systemctl disable  portmap.service rpcbind.socket rpcbind.service
cd /tmp
git clone https://github.com/kubernetes-sigs/nfs-ganesha-server-and-external-provisioner
cd nfs-ganesha-server-and-external-provisioner/charts
helm install nfs-server-provisioner nfs-server-provisioner  \
  --namespace nfs-server-provisioner --create-namespace \
  --set persistence.storageClass="local-path" \
  --set persistence.size="200Gi" \
  --set persistence.enabled=true \
  --set 'storageClass.mountOptions[0]=tcp' --set 'storageClass.mountOptions[1]=nfsvers=4.1'
```

> **Warning** installing nfs-common starts two services that we don't need, and that can be a security risk when you are on an internet connected machine. So don't forget to run the following commands to disable them again:

```shell
sudo systemctl stop  portmap.service rpcbind.socket rpcbind.service
sudo systemctl disable  portmap.service rpcbind.socket rpcbind.service
```

If you are running a small multi-node cluster, [longhorn](https://longhorn.io/) is worth giving a try, but mind that maintaining a storage backend is a tedious task (no matter how easy the installation procedure makes it look). On a real project, you will probably use some vendor-supplied storage solution, like the one from AWS or Azure or other cloud providers. Some cloud providers that don't have a kubernetes offering, but, for instance [on hetzner](https://github.com/hetznercloud/csi-driver/blob/main/docs/kubernetes/README.md#getting-started) you can still use their volume storage with your kubernetes installation.

For an on premise solution, an easier to maintain option could be buying a (hardware) NAS that supports NFS (which is pretty much any brand nowadays) and then using a volume provider like [this one](https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/) to provision storage volumes from the NAS.



## <a name="refresh-hosts"></a> Automate the refresh of /etc/hosts

The following install script installs a systemd service that will auto-update /etc/hosts whenever your ip address changes.  
If you use WSL, rather follow the instructions in [the WSL README](../README-WSL2.md#make-hostnames-available-in-wsl-and-windows).

You can put the aliases you want in `/etc/update_hosts_file/aliases` (put them all on the same line, separated by spaces). Don't put comments in that file!

```shell
#!/bin/sh


cat << END | sudo tee /etc/systemd/system/ip-change-mon.service
# /etc/systemd/system/ip-change-mon.service

[Unit]
Description=IP Change Monitor
Wants=network.target
After=network-online.target

[Service]
ExecStart=:/bin/bash -c "ip mon addr | sed -nu -r \'s/.*[[:digit:]]+:[[:space:]]+([^[:space:]]+).*/\\1/p\' | while read iface; do systemctl restart ip-changed.target; done"

[Install]
WantedBy=multi-user.target default.target
END


cat << 'END' | sudo tee /usr/local/bin/update_hosts_file.sh
#!/bin/bash

export MYIP=$(/usr/bin/hostname -I | cut -d' ' -f1)
export ALIASES=$(cat /etc/update_hosts_file/aliases)
sed -i '/UPDATE_HOSTS_FILE/d' /etc/hosts
echo "$MYIP $ALIASES ### UPDATE_HOSTS_FILE" | tee -a /etc/hosts

END

sudo chmod u+x /usr/local/bin/update_hosts_file.sh

cat << END | sudo tee /etc/systemd/system/ip-changed.target
# /etc/systemd/system/ip-changed.target 

[Unit]
Description=IP Address changed
END

cat << END | sudo tee /etc/systemd/system/updatehosts.service
[Unit]
Description=Updates the host file to fake DNS entries.
PartOf=ip-changed.target
Before=ip-changed.target
StartLimitBurst=20
StartLimitIntervalSec=5

[Service]
Type=oneshot
ExecStart=/usr/local/bin/update_hosts_file.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
END

sudo mkdir -p /etc/update_hosts_file

[[ -f /etc/update_hosts_file/aliases ]] || echo "registry.kube-public" | sudo tee /etc/update_hosts_file/aliases

sudo systemctl enable --now ip-change-mon
sudo systemctl enable --now updatehosts
```


