## Installing a more capable storage backend

The default hostpath provisioner (also in use by the other solutions) doesn’t support ReadWriteMany volumes. As a solution, we’ll install one that does. 

[NFS Ganesha](https://nfs-ganesha.github.io/) allows for RWX volumes by taking a system-provided volume and launching a userspace NFS server on it. It won’t be the fastest performance, but it's lightweight (only 1 pod, rather than tens of pods for Longhorn).

```shell
# need nfs utilities on the host. that's the only dependency!
sudo apt -y install nfs-common
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

If you are running a small multi-node cluster, [longhorn](https://longhorn.io/) is worth giving a try. In our experience, it tends to become unstable when your cluster is heavily loaded.