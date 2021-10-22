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

When needed, you can start k3s again by doing `sudo systemctl start k3s`.

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

## Installing container registry

First, let’s create a namespace and a https certificate:

```shell
kubectl create namespace registry

# let's create a SSL certificate for our container registry
cat << END  | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: registry-tls
  namespace: registry
spec:
  secretName: registry-tls
  issuerRef:
    name: selfsigned-ca-issuer
    kind: ClusterIssuer
  commonName: registry.kube-public
  dnsNames:
  - registry.kube-public
END
```

After our certificate is created, we can install a container registry. To do this, we need a hostname and an ip address that will be accessible **both from outside our cluster and from inside our cluster**. This is not so simple: we cannot use localhost or `127.0.0.1` because it doesn’t have the same meaning from outside our cluster (there it will be our pc) and inside our cluster (there it will be the current pod). So we will take the first local LAN ip address of our host. We will use /etc/hosts to make a name alias for this ip address. From then on, the registry will be accessible via `registry.kube-public`.

> **_WARNING:_** On laptops this can be problematic: there, when you connect to another wifi network, you will get another local ip address, and your /etc/hosts file will not be valid anymore. This can make you loose a couple of time since the error message might be cryptic (like “SSL verification error”) as the “old” ip might now be taken by something else.  So whenever you switch networks, check your /etc/hosts! 

<details>
<summary>A solution is writing a script that automates updating /etc/hosts whenever your ip changes</summary>

The following install script installs a systemd service that will auto-update /etc/hosts whenever your ip address changes.
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


cat << END | sudo tee /usr/local/bin/update_hosts_file.sh
#!/bin/bash

export MYIP=\$(/usr/bin/hostname -I | cut -d' ' -f1)
export ALIASES=\$(cat /etc/update_hosts_file/aliases)
sed -i '/UPDATE_HOSTS_FILE/d' /etc/hosts
echo "\$MYIP \$ALIASES ### UPDATE_HOSTS_FILE" | tee -a /etc/hosts

END
chmod u+x /usr/local/bin/update_hosts_file.sh

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
mkdir -p /etc/update_hosts_file

[[ -f /etc/update_hosts_file/aliases ]] ||  echo "registry.kube-public" > /etc/update_hosts_file/aliases

systemctl enable --now ip-change-mon
systemctl enable --now updatehosts

```

Ok, now that this has been taken care of, let's continue to install the container registry.

</details>


```shell
# let's install the registry
### first generate a password
sudo apt-get -f install pwgen apache2-utils
export PASW=$(pwgen -1)
### then install the registry
cd /tmp
git clone https://github.com/Kapernikov/docker-registry.helm.git
helm install --wait -n registry --create-namespace \
        registry ./docker-registry.helm \
        --set ingress.enabled=true \
        --set "ingress.hosts[0]=registry.kube-public" \
        --set "ingress.tls[0].hosts[0]=registry.kube-public" \
        --set ingress.tls[0].secretName="registry-tls" \
        --set persistence.enabled=true --set persistence.size=20Gi \
        --set 'ingress.annotations.nginx\.ingress\.kubernetes\.io/proxy-body-size'="512m" \
        --set 'secrets.htpasswd'="$(htpasswd -Bbn registry $PASW)"
#### lets upload our registry password so that we can retrieve it later to create 
#### ImagePullSecrets or do docker login

kubectl apply -n registry -f - << END
apiVersion: v1
kind: Secret
metadata:
  name: registry-password
type: Opaque
stringData:
  username: registry
  password: $PASW
END


# no need to do this if we installed the auto-update script above
MYIP=$(hostname -I | cut -d' ' -f1)
echo "$MYIP registry.kube-public" | sudo tee -a /etc/hosts
```

When using Skaffold, you will find that quickly, a lot of Docker images will pile up in your container registry, which will eat your disk space. Instead of carefully cleaning them up, we simply uninstall and reinstall the registry every now and then.

If everything worked fine you should be able to login with your docker now:

```shell
PASSWORD=$(kubectl get secret -n registry registry-password -o json | jq -r '.data.password' | base64 --decode)
USERNAME=$(kubectl get secret -n registry registry-password -o json | jq -r '.data.username' | base64 --decode)
REGHOST=$(kubectl get ingress -n registry registry-docker-registry -o json | jq -r '.spec.rules[0].host')
docker login -u $USERNAME -p $PASSWORD $REGHOST
```

if you get “login succeeded” all is fine. if you get certificate error check that:

* your certificate is installed and up to date
* the /etc/hosts entry is correctly pointing to your own pc
* you trusted your CA and restarted docker after trusting your CA (see above)

Now when deploying yamls with your newly defined registry you will need ImagePullSecrets so that kubernetes can also log in. For instance suppose we want to create registry-creds secret in namespace foo:

```shell
PASSWORD=$(kubectl get secret -n registry registry-password -o json | jq -r '.data.password' | base64 --decode)
USERNAME=$(kubectl get secret -n registry registry-password -o json | jq -r '.data.username' | base64 --decode)
REGHOST=$(kubectl get ingress -n registry registry-docker-registry -o json | jq -r '.spec.rules[0].host')
kubectl create secret -n default docker-registry registry-creds \
   --docker-server=$REGHOST --docker-username=$USERNAME --docker-password=$PASSWORD
```

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
