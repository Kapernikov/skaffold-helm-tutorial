# Installing K3S


## Installing client tools

When not working on a pre-configured cloud machine, we need to install some client tools. let's not waste too much time for these, just copypaste the commands below! We will also increase some fs inotify limits so we don't run into trouble with skaffold dev

```shell
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
sudo install kubectl /usr/local/bin

curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

curl -Lo skaffold https://github.com/GoogleContainerTools/skaffold/releases/download/v1.26.1/skaffold-linux-amd64 && \
sudo install skaffold /usr/local/bin/

curl -Lo k9s.tgz https://github.com/derailed/k9s/releases/download/v0.24.10/k9s_v0.24.10_Linux_x86_64.tar.gz && \
tar -xf k9s.tgz  && sudo install k9s /usr/local/bin/

curl -Lo kubectx https://github.com/ahmetb/kubectx/releases/download/v0.9.3/kubectx && \
sudo install kubectx /usr/local/bin/

cat << END | sudo tee -a /etc/sysctl.conf
fs.inotify.max_user_watches=1048576
fs.inotify.max_user_instances=1000000

END

sudo sysctl --system
```

## Installing k3s

k3s comes with traefik ingress controller by default. We will not use this (instead we will use nginx because it’s more widely used), so we disable traefik.

```shell
## write a configfile to disable traefik
sudo mkdir -p /etc/rancher/k3s
cat << EOF | sudo tee /etc/rancher/k3s/config.yaml
disable:
    - traefik

#### DISABLE LEADER ELECTION : reduces CPU usage, but DO NOT DO THIS if you are going to run
#### a multi-node cluster!!!!
kube-controller-manager-arg:
    - "leader-elect=false"
    - "node-monitor-period=60s"

EOF
## "normal" installation
sudo bash -c "curl -sfL https://get.k3s.io | sh -"
```

K3s can be started and stopped with systemd, so systemctl stop k3s will stop K3s and systemctl start k3s will start it. However, **stopping K3s will leave all containers running**. To kill all containers, run `sudo k3s-killall.sh`.

Once K3s has finished startup, you will find a kubeconfig in `/etc/rancher/k3s/k3s.yaml`. This configfile can be copied to your .kube/config. When you want to merge multiple kubeconfigs in one, use [this guide](https://stackoverflow.com/questions/46184125/how-to-merge-kubectl-config-file-with-kube-config).

```shell
mkdir -p $HOME/.kube
sudo cat /etc/rancher/k3s/k3s.yaml > $HOME/.kube/config
```

## Installing nginx ingress controller

```shell
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.44.0/deploy/static/provider/baremetal/deploy.yaml
```

Now, this creates the Ingress service as a NodePort, which means it will be accessible to the outside world, but **on a random port, not port 80/443**. This is a nuisance, because this would require us to set up additional portforwarding or iptables rules. Fortunately, K3s has a built-in loadbalancer. We can just patch the service to make it of type LoadBalancer to make use of it:

```shell
kubectl patch -n ingress-nginx service ingress-nginx-controller -p '{"spec": {"type": "LoadBalancer"}}'
```

## Installing a local certificate auth on our system so we can issue certificates

```shell
# install cert-manager 1.2.0
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.2.0/cert-manager.yaml

# creating a local CA (letsencrypt won't work for localhost)
mkdir -p $HOME/kubeca && cd $HOME/kubeca
[[ -f ca.key ]] || openssl genrsa -out ca.key 2048
[[ -f ca.crt ]] || openssl req -x509 -new -nodes -key ca.key -subj "/CN=local_k3s" -days 3650 \
  -reqexts v3_req -extensions v3_ca -out ca.crt
kubectl create secret tls ca-key-pair \
   --cert=ca.crt \
   --key=ca.key \
   --namespace=cert-manager
```
Wait 3 seconds for startup
```
# lets create a cluster issuer that will issue certificates using our newly created CA
cat << END | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned-ca-issuer
  namespace: cert-manager
spec:
  ca:
    secretName: ca-key-pair
END
```
Now we have our CA up and running, but we also need to make sure our system trusts this CA. We do this as follows:

```shell
# lets make sure our computer trusts this CA!
sudo cp ca.crt /usr/local/share/ca-certificates/selfsigned-k3s.crt && sudo update-ca-certificates
# now restart docker or docker login won't work!
sudo systemctl restart docker
sudo systemctl restart k3s
```

Note that both Firefox and Google Chrome don’t look at the CA certificates data. If you want the certificate to be valid in Firefox/Chrome, you will need to take extra steps that are dependent on the browser you are using. For instance, for Firefox, instructions are here.

```shell
dirname $(grep -IrL 'p11-kit-trust.so' ~/.mozilla/firefox/*/pkcs11.txt) | xargs -t -d '\n' -I {} modutil -dbdir sql:{} -force -add 'PKCS #11 Trust Storage Module' -libfile /usr/lib/x86_64-linux-gnu/pkcs11/p11-kit-trust.so
```

After doing this, restart Firefox.

## Installing Trow container registry

First, let’s create a Trow namespace and a https certificate:

```shell
kubectl create namespace trow

# let's create a SSL certificate for our container registry
cat << END  | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: trow-kube-public
  namespace: trow
spec:
  secretName: trow-kube-public
  issuerRef:
    name: selfsigned-ca-issuer
    kind: ClusterIssuer
  commonName: trow.kube-public
  dnsNames:
  - trow.kube-public
END
```

After our certificate is created, we can install Trow. To do this, we need a hostname and an ip address that will be accessible **both from outside our cluster and from inside our cluster**. This is not so simple: we cannot use localhost or `127.0.0.1` because it doesn’t have the same meaning from outside our cluster (there it will be our pc) and inside our cluster (there it will be the current pod). So we will take the first local LAN ip address of our host. We will use /etc/hosts to make a name alias for this ip address. From then on, trow will be accessible via `trow.kube-public`.

> **_WARNING:_** On laptops this can be problematic: there, when you connect to another wifi network, you will get another local ip address, and your /etc/hosts file will not be valid anymore. This can make you loose a couple of time since the error message might be cryptic (like “SSL verification error”) as the “old” ip might now be taken by something else.  So whenever you switch networks, check your /etc/hosts! 

```shell
# let's install trow
helm repo add trow https://trow.io
helm install trow trow/trow \
         --namespace trow \
         --create-namespace \
         --set 'trow.domain=trow.kube-public' \
         --set 'ingress.enabled=true' \
         --set 'ingress.hosts[0].host=trow.kube-public,ingress.hosts[0].paths={"/"}' \
         --set 'ingress.tls[0].hosts[0]=trow.kube-public' \
         --set 'ingress.tls[0].secretName=trow-kube-public' \
         --set trow.user="" --set trow.password="" \
         --set 'ingress.annotations.nginx\.ingress\.kubernetes\.io/proxy-body-size'="512m"

# let's fake a DNS entry!
MYIP=$(hostname -I | cut -d' ' -f1)
echo "$MYIP trow.kube-public" | sudo tee -a /etc/hosts
```

When using Skaffold on Trow, you will find that quickly, a lot of Docker images will pile up in your container registry, which will eat your disk space. Instead of carefully cleaning them up, we simplu uninstall and reinstall Trow every now and then.

## Installing a more capable storage backend

The default hostpath provisioner (also in use by the other solutions) doesn’t support ReadWriteMany volumes. As a solution, we’ll install one that does. 

[NFS Ganesha](https://nfs-ganesha.github.io/) allows for RWX volumes by taking a system-provided volume and launching a userspace NFS server on it. It won’t be the fastest performance, but it's lightweight (only 1 pod, rather than tens of pods for Longhorn).

```shell
# need nfs utilities on the host. that's the only dependency!
sudo apt install nfs-common
cd /tmp
git clone https://github.com/kubernetes-sigs/nfs-ganesha-server-and-external-provisioner
cd nfs-ganesha-server-and-external-provisioner/deploy/helm
helm install nfs-server-provisioner .  \
  --namespace nfs-server-provisioner --create-namespace \
  --set persistence.storageClass="local-path" \
  --set persistence.size="200Gi" \
  --set persistence.enabled=true
```

