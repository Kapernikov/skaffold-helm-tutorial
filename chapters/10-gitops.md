# Managing production clusters with gitops and CI/CD

While skaffold is a very attractive way to deploy quickly on development environments, on production clusters requirements are a bit different:

* We don't care so much about quick deployment cycles. We don't deploy a new production release every few seconds.
* We want to avoid messing production up as much as possible, and reduce the chances for human error.
* We often manage multiple production environments, maybe even each having a different versoin of the software we are building.

There are multiple strategies for tackling this:

1. We create a CI/CD pipeline for our project, and this CI/CD pipeline also includes a step for deploying the software.
2. We create a CI/CD pipeline that builds a release for our software, and then use another gitops tool to actually deploy this release on a cluster.

We think option 2 is far superior here, because it gives you the flexibility to run multiple versions of your software on multiple clusters, and have multiple clusters having slightly different settings (eg a different size for a volume).
Let's see how to do that.

## CI/CD for a kubernetes application

Our first component is a CI/CD pipeline. The pipeline will be responsible for:

* running all tests
* building the application artifacts. Because we're talking about a kubernetes application, the artifacts are wrapped in docker images here.
* releasing a helm chart to a helm repository that refers to the docker images that have just been built.

How we will set up this CI/CD pipeline depends on which git platform we use or which CI/CD tool we use:

* For github, we can use a `github action` that releases a helm chart to a git repository (which would just be a github pages repo) after building and testing.
* Gitlab has its own CI/CD system, and, in addition to this, has a built in secure docker registry and helm package registry. Gitlab also has the notion of a "release", and our CI/CD pipeline can autofill a release with release notes based on git commits whenever its time to release.
* Azure devops has runners, and there is an azure container image registry for storing docker images.
* Other tools (like jenkins or travis) have their own configuration. For some projects the official docker hub is the best docker registry option.

We will not go too deep into this during this tutorial, since every option would require a completely different setup. Instead, let's just skip to the gitops part: we assume that this part is already done and we just need to do the deployment.

## Flux: a gitops tool

A gitops tool will take care of taking a software release and actually deploying it on a cluster. We call it gitops because the description of what software should exactly be installed on the cluster is also stored in a git repo. If we want to change settings or the software version, we just make a change to the gitrepo and commit the change (maybe merging it to the right branch after a review). Then the gitops tool will do the rest.

We will use flux for this tutorial. Flux has the advantage of having a simple architecture and being very flexible. It also works with any git provider (github, gitlab, azure devops, bitbucket, etc), and it is not picky on which kubernetes version you run. Actually flux has some "quick start" processes if you work with github or gitlab, but if you work with something else you can still use flux, you just need to do the initial setup (creating the git repo, managing credentials) yourself. In this tutorial we will try to skip the quick start stuff, so you can use any git platform you like. Actually, we will roughly the steps detailed [here](https://fluxcd.io/docs/use-cases/azure/) which are the steps for azure devops, but since they don't involve the quick start, they work everywhere.

To start this tutorial please do the following:

* Uninstall the cvat helm release from last chapter, we will now install it using gitops (or choose a different namespace).
* Go to your favorite git platform and create a repo, maybe call it "cvat-gitops" since we're going to use it to deploy cvat. Or maybe that name is already taken, be creative.
* Clone your git repo locally, for the sake of this excercise, let's put it in `~/projects/cvat-gitops`

Now we will use the flux commmand line tool to set up flux. We need the command line tool for initial setup, after that, you can keep it (it has some useful features) but you don't strictly need it anymore.

```shell
curl -s https://fluxcd.io/install.sh | sudo bash
cd ~/projects/cvat-gitops # or the folder you chose
```

Now we will organise our git repo a bit, first we will do this as simple as possible, and then we will align with flux best practises.

### Flux bootstrap

First, in our git repo, we will create one directory that is **specific** for our cluster and that contains the installation of flux itself. This will also be the starting point for flux when it reads our git repository.
Let's call our cluster **tutorial**.

```shell
mkdir -p clusters/tutorial/flux-system
flux install --export > clusters/tutorial/flux-system/gotk-components.yaml
```

Now the only thing that our `flux install` command did was generating a yaml file that contains the kubernetes resources for installing flux itself. We can already commit this file and push it!.
Off course, we have a little chicken-and-egg problem here: there is no flux yet on our cluster that could take this yaml file and install it.

Since flux cannot yet do this, we'll have to do it ourselves. Fortunately, that's not too difficult:

```shell
kubectl apply -f clusters/tutorial/flux-system/gotk-components.yaml
```

If you look at what we actually deployed, you will find that flux basically consists of:

* a *git controller* that can fetch remote git repo's based on a GitRepository custom resource.
* a *helm controller* that can install helm charts and helm releases based on a HelmRepository and HelmRelease custom resources.
* a *kustomize controller* that can deploy kustomisations (that could be described in git repo's, see above)
* a *notification controller* dealing with both incoming notifications (from other CI systems) and outgoing notifications (to slack ? teams ?)

Now, we have flux up and running, but flux doesn't do anything yet, since flux is not yet connected to a gitops repo.
In order to connect flux to a gitops repo, we need to create a gitops repo. The most difficult part is creating a ssh keypair. Flux has some tools to do this for you, but we don't have to use them, we can just create a keypair like we would in any other case:

```shell
ssh-keygen -N "" -f identity
ssh-keyscan gitlab.com > known_hosts ### TODO replace this by the git host of your git platform (github.com , gitlab.com, bitbucket.com). we need the fingerprint here.
kubectl create secret -n flux-system generic  flux-ado-identity --from-file=identity=identity --from-file=identity.pub=identity.pub --from-file=known_hosts=known_hosts -o yaml --dry-run=client  > clusters/tutorial/flux-system/flux-git-identity.yaml
echo "public key follows. add it as ssh key to your git platform"
cat identity.pub

rm identity.pub
rm identity
rm known_hosts

```

Now, the public key you will have to register with your git platform. Gitlab allows you to do this as a deploy key, but azure devops won't, so for azure devops you'll have to add the ssh key to your own user, or to a user you create especially for flux. After that, we can already create the secret on our kubernetes cluster (remember the chicken and egg problem, its still not solved):

```shell
kubectl apply -f clusters/tutorial/flux-system/flux-git-identity.yaml
```

Also commit everything and push. Now it's time to really solve the chicken and egg problem.
First let's create a kustomization file that will describe the entry point for flux:

```yaml
# save this as clusters/tutorial/flux-system/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- gotk-components.yaml
- gotk-sync.yaml
```

Ok, this kustomization refers to the `gotk-components.yaml` we just created. This means that once we solved the chicken-and-egg problem, we will be able to update flux itself by just updating the gotk-components.yaml!
But it also refers to the `gotk-sync.yaml` file which is supposed to be the pointer to our git repo. Let's create this:

```yaml
# save this as clusters/tutorial/flux-system/gotk-sync.yaml
---
apiVersion: source.toolkit.fluxcd.io/v1beta1
kind: GitRepository
metadata:
  name: flux-system
  namespace: flux-system
spec:
  gitImplementation: libgit2
  interval: 1m0s
  ref:
    branch: master
  secretRef:
    name: flux-ado-identity
  timeout: 20s
  url: CHANGE_THIS_TO_THE_SSH_URL
---
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 10m0s
  path: ./clusters/tutorial
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
```

Now we need to change the CHANGE_THIS_TO_THE_SSH_URL url to the ssh url of our git repo. Note that flux does not support new style url syntax. That means we need to change the urls we get from gitlab/github/... a bit, by prefixing with `ssh://` and not using `:` but `/` as separator between host and path. So:

* don't write git@github.com:Kapernikov/skaffold-helm-tutorial.git but write ssh://git@github.com/Kapernikov/skaffold-helm-tutorial.git
* don't write git@gitlab.com:frank5/testgitops.git but write ssh://git@gitlab.com/frank5/testgitops.git

Now, before going to the next step, commit and push everything, because next time, flux will access the files, not we. Let's fill the last piece of the puzzle:

```shell
kubectl apply -f clusters/tutorial/flux-system/gotk-sync.yaml
## now wait a bit, and let's check if flux got our git repo!
kubectl get gitrepo --all-namespaces
## lets see if flux also got our kustomization
kubectl get kustomization --all-namespaces
```

If you see two success messages in the output, then flux is ready to go and connected to our gitrepo. Note that now we have one folder under "clusters", but in the end you will have more clusters that will be managed from the same git repo (could be more customers, or dev/acc versions)

Let's also get something very confusing out of the way: in the above you see that we created two different `kustomizations`. But they were actually not the same type of object! (check the API group and version). One is a kubernetes resource, while the other one is a file:

* the kustomize.toolkit.fluxcd.io/v1beta2 one is read by the kustomization controller. This resource tells the controller it needs to manage a kustomization, and that the source code for this kustomization is in a git repo, and that it is in a certain path.
* the other one (kustomize.config.k8s.io/v1beta1) is the file that is actually in that path. When you tell the controller to manage a kustomization, it will look for folders containing a file named kustomization.yaml in the path specified, which should contain ... a kustomization.

This means that now, we can add more folders under `clusters/tutorial` and they will all be picked up by the kustomization we just created!...

### Installing a helm chart (cvat)

... We could for instance create a new folder 'cvat' in it and put a cvat installation in it like so:

```yaml
# save this under clusters/tutorial/cvat/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - cvat-released.yaml
```

```yaml
# save this under clusters/tutorial/cvat/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cvat
```

```yaml
# save this under clusters/tutorial/cvat/cvat-released.yaml
apiVersion: source.toolkit.fluxcd.io/v1beta1
kind: HelmRepository
metadata:
  name: cvat
  namespace: cvat
spec:
  interval: 362m
  url: https://kapernikov.github.io/cvat-helm/
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: cvat
  namespace: cvat
spec:
  install:
    timeout: 25m
    remediation:
      retries: -1
  upgrade:
    remediation:
      retries: -1
  interval: 361m
  chart:
    spec:
      chart: cvat-helm
      version: 0.1.6
      sourceRef:
        kind: HelmRepository
        name: cvat
      interval: 360m
  values:
    ingress:
      host: cvat.kube-public
      clusterIssuer: letsencrypt-prod
    superUser:
      create: true
      username: admin
      initialPassword: tutorial
    volume:
      data:
        size: 40Gi
```

Now commit all these files and push them. Now wait and see your cluster installing cvat:

```shell
kubectl get helmrelease
```
### Giving some structure to the repository

With the current structure, we have to duplicate our cvat folder for every cluster. That is not really optimal if we manage multiple clusters. We'd rather have a common cvat folder and then have only the cluster-specific stuff in a separate folder.

This is why flux best practises organise the gitops repo in a different way than we did so far. Let's try to move our structure to the flux best practises and see if, this way, we can achieve the flexibility we want.

First, move cvat to another directory `apps/base/cvat`. This will be our base directory for cvat.

```shell
mkdir apps
## move the 'cvat' folder to apps/base
git mv clusters/tutorial/cvat apps/base
```

Now let's make an apps/ directory with the cvat configuration that would be specific for our cluster (for instance the hostname):

```shell
mkdir apps/tutorial-cluster
cat << END > apps/tutorial-cluster/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../base/cvat
patchesStrategicMerge:
  - patch-tutorialcluster.yaml
END

cat << END > apps/tutorial-cluster/patch-tutorialcluster.yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: cvat
  namespace: cvat
spec:
  values:
    ingress:
      host: cvat-tutorial.kube-public
END
```

And finally, let's make sure that flux actually finds those new folders!

```shell
mkdir -p clusters/tutorial/apps
cat << END > clusters/tutorial/apps/apps.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta1
kind: Kustomization
metadata:
  name: apps
  namespace: flux-system
spec:
  interval: 10m0s
#  dependsOn:
#    - name: infrastructure
  sourceRef:
    kind: GitRepository
    name: flux-system
  path: ./apps/tutorial-cluster
  prune: true
  validation: client
END
```

Now commit and push everything. After a while, flux should pick up your changes.

We now made things a bit more complicated: the description in  `clusters/tutorial` now delegates to `apps/tutorial-cluster`, which in turn refers to `apps/base/cvat`.
Let's see what role every level of indirection has:

* `clusters/tutorial` is the main entry point containing the flux bootstrap and the primary git repo and nothing else.
* `apps/tutorial-cluster` is the directory that contains the cvat configuration **specific** for the tutorial cluster.
* `apps/base/cvat` is the folder that contains common stuff for cvat.

This is a common way of doing things in flux, but it doesn't stop here: you can combine all the resources at will, and you can even refer other git repositories from the main gitrepo and delegate parts to separate teams!.

### A review process for production deployment

To avoid human mistakes, we might want to make sure that every upgrade gets a proper review before being applied. Flux doesn't have any specific functionality for this, but that's not needed, as our configuration is now managed in git, and we can use the features offered by our git platform to achieve this.

In order to impose a review process, carry out the following steps:

* Create a new branch (eg `production`) on your gitops repository
* Make this branch protected so that direct push to this branch is not allowed anymore. The only way to change the branch is to make a merge request to this branch.
* Change the `GitRepository` in the `gotk-sync.yaml` file to point to the `production` branch.

Now, whenever you want to make changes in production, first create a merge request (or pull request) with the necessary changes, and let somebody review the pull request. When reviewed, it can be marked as ready, and finally merged when the production release needs to happen.

In addition to this, you could have another branch for the `staging` cluster, and have every release first go to staging before going to production.
