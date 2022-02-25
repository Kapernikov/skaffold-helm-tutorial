import * as pulumi from "@pulumi/pulumi";
import * as hcloud from "@pulumi/hcloud";
import * as fs from "fs";
import * as path from "path";
import * as process from "process";
import * as cloudinit from "@pulumi/cloudinit";

class Machine {
    name: string;
    userName: string;
    password: string;
    constructor(name: string, userName: string, password: string) {
        this.name = name;
        this.userName = userName;
        this.password = password;
    }
}


const machines = [
    new Machine("machine1", "hola", "pola"),
//    new Machine("machine2", "holapola", "sdoiijoijs"),
];

let homeDir = "";
if (process.env.HOME) {
    homeDir = process.env.HOME;
}

const sshKey = new hcloud.SshKey("creatorkey", {
    publicKey: fs.readFileSync(path.join(homeDir,  ".ssh/id_rsa.pub")).toString()
})


machines.forEach(m => {
    const resourceConf = new cloudinit.Config(`config-${m.name}`, {
        gzip: false,
        base64Encode: false,
        parts: [{
            contentType: "text/x-shellscript",
            content: `#!/bin/bash
            
    function do_user() {
                adduser --gecos "" --disabled-password $1
                chpasswd <<<"$1:$2"
                adduser $1 sudo
    }

    do_user ${m.userName} ${m.password}
    export DEBIAN_FRONTEND=noninteractive
    apt-get -y update
    apt-get -y install apt-transport-https ca-certificates curl vim wget joe gnupg lsb-release git jq tmux python3-pip
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get -y update && apt-get -y install  docker-ce docker-ce-cli containerd.io

    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install kubectl /usr/local/bin

    curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

    curl -Lo skaffold https://storage.googleapis.com/skaffold/releases/latest/skaffold-linux-amd64 && \
    sudo install skaffold /usr/local/bin/

    curl -Lo k9s.tgz https://github.com/derailed/k9s/releases/download/v0.25.18/k9s_Linux_x86_64.tar.gz && \
    tar -xf k9s.tgz  && sudo install k9s /usr/local/bin/
    
    curl -Lo kubectx https://github.com/ahmetb/kubectx/releases/download/v0.9.3/kubectx && \
    sudo install kubectx /usr/local/bin/

    echo >> /etc/sysctl.conf
    echo "fs.inotify.max_user_watches=1048576" >> /etc/sysctl.conf
    echo "fs.inotify.max_user_instances=1000000" >> /etc/sysctl.conf

    sysctl --system

    # enable passwordless sudo
    cat /etc/sudoers | sed -e 's|(ALL\:ALL)|NOPASSWD:|g;' > /etc/sudoers.new && cp /etc/sudoers.new /etc/sudoers

    adduser ${m.userName} docker


            `,
            filename: "initialize.sh",
        }]
    });
    
    const vm = new hcloud.Server(m.name, {
        image: "ubuntu-20.04",
        serverType: "cx41",
        location: "fsn1",
        sshKeys:  [sshKey.id],
        userData: resourceConf.rendered
    } ); 

    exports[m.name] = vm.ipv4Address;
    exports[`${m.name}_user`] = m.userName;
    exports[`${m.name}_password`] = m.password;

});

