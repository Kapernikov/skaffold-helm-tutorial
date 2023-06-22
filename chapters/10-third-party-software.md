# Working with third party software

So far we used helm and skaffold, but we used it with our own helm chart. However, in many cases, you won't have to do that as a helm chart for the software you want to use is already out there.

## Choosing your helm chart

Often, for some software there are multiple helm charts available. You will need to choose which one. Choose wisely:

* Take one that is still maintained (recent versions, activity on github)
* If possible take one from the authors of the software. If not, take one from a reputable organisation.
* When taking a helm chart from github, don't just take master branch, but take a released version.
* Have a look at the open issues. The helm chart might have a security issue or might be incompatible with your version of kubernetes.

## Installing a helm chart from git

Helm charts can be published in git repo's. To install them, clone the git repo, go to the right folder, look at the values you want to override and install away. This is actually the same process we used for our own helm chart.

## Installing a helm chart from a helm repository

There is actually another way to install helm charts: using helm repositories. A helm repository is just a collection of zipped up helm charts somewhere on the web. A helm repository has one file that should always be present: `index.yaml`. This file contains the list of all helm charts on that repository.

Excercise: head over to https://github.com/Kapernikov/cvat-helm and try to install CVAT from the helm chart. Follow the instructions on the website.

Some small tasks:

* cvat is a web application, just like the one from our previous excercise. A web application needs a public facing url, and since our cluster is running locally, we need to fake this using the `/etc/hosts` trick we did before. Can you set up CVAT in a way that you can access it from your browser ?
* The cvat helm chart has some configuration options. Can you change them after already having installed CVAT?
* We don't need CVAT anymore, can you cleanly uninstall it ?

## Operators

Helm charts are nice, but they have some caveats:

* The helm installer runs once to install everything, and then it stops. If you want to change values after installation, you need to perform an upgrade.
* Not everything in kubernetes is modifiable. For instance, some storage providers do not support resizing of volumes. Some fields of pods/jobs/deployments are immutable after installation, in order to change them you have to recreate. Helm has no solution for this.

So while helm is very simple, for complicated stuff, sometimes you want more. And this "more" is called kubernetes operators. Let's break down what an operator is:

### Custom resource definitions

The kubernetes API is extensible, and a custom resource definition is the way to do this. Let's try to create a simple one. Suppose we want to create a new object type `AppUser`. An app user would have a lastName, firstName and emailAddress.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: appusers.kapernikov.com
spec:
  group: kapernikov.com
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                lastName:
                  type: string
                firstName:
                  type: string
                emailAddress:
                  type: string
  scope: Namespaced
  names:
    plural: appusers
    singular: appuser
    kind: AppUser
    shortNames:
    - au
```

now we have this definition we can create an `AppUser` like so:

```yaml
apiVersion: kapernikov.com/v1
kind: AppUser
metadata:
    name: john
spec:
    lastName: Doe
    firstName: John
    emailAddress: john.doe@kapernikov.com
```

When we create an appuser, kubernetes reacts as we expect: it stores the appuser (in etcd), and you can access it using the `kubectl` command or with k9s, just like you would with any other kubernetes command.
But for the rest, kubernetes does exactly nothing. It doesn't create a real user in your application, it doesn't launch a job or anything else. It just sits there.


### Controllers

Probably, when creating a real application, we would want to do something usefull with an `AppUser`, for instance doing something whenever a user is created, updated or deleted.
Kubernetes makes it easy, by providing an API that does not only expose REST endpoints but also events. We can access this API using any programming language that has kubernetes bindings, or simply using `kubectl`:

```shell
kubectl get appuser --watch
```

The `--watch` flag will make kubectl wait for events and print them to the screen. Now imagine a program listening for `AppUser` events and doing something useful. This program would be called a controller.
And, unlike our kubectl example, this program could just run in a kubernetes pod (why not). Off course, this pod would need special permissions to access AppUser objects in kubernetes (by default a pod cannot).

Creating these permissions would involve creating a `Role`, a `RoleBinding` and a `ServiceAccount`, but we're not going to deal with this here.

Controllers typically use a reconcile loop. The reconcile loop will compare the current state of the cluster with the desired state of the cluster, and will create, update or delete resources as needed. They will do this every time an event comes in (this event could be a change to a custom resource, but it could also be a change of state in the cluster, eg a pod terminating). While being very resilient, reconcile loops typically are not very efficient. This is one of the reasons why an idle kubernetes cluster already uses quite a lot of resources.

### The operator pattern

Now that we have seen both controllers and custom resource definitions, we can dive into the [operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/).
An operator is basically:

* one or more custom resource definition
* some piece of software that reacts to these custom resource definitions by creating, updating or deleting resources
* this software itself is containerized and deployable to kubernetes (installing an operator could be installing the helm chart of a certain operator)

You will find lots of operators, both commercial and open source.

## Hands-on: installing the Crunchy Data postgres operator

Let's now experiment with PGO, the Crunchy Data postgres operator. The crunchydb postgres operator can be installed as a helm chart. Since we already know this, let's do that:

let's create a namespace crunchy-pgo

```shell
kubectl create namespace crunchy-pgo
helm install -n crunchy-pgo pgo oci://registry.developers.crunchydata.com/crunchydata/pgo
```

Now the operator is installed.

## Deploying a highly available postgres cluster

Now that the crunchy data postgres operator is running, we can use it to make a postgres cluster

```yaml
apiVersion: postgres-operator.crunchydata.com/v1beta1
kind: PostgresCluster
metadata:
  name: my-postgres
spec:
  image: registry.developers.crunchydata.com/crunchydata/crunchy-postgres:ubi8-14.5-1
  postgresVersion: 14
  instances:
    - name: instance1
      replicas: 1
      dataVolumeClaimSpec:
        accessModes:
        - "ReadWriteOnce"
        resources:
          requests:
            storage: 1Gi
  backups:
    pgbackrest:
      image: registry.developers.crunchydata.com/crunchydata/crunchy-pgbackrest:ubi8-2.40-1
      repos:
      - name: repo1
        volume:
          volumeClaimSpec:
            accessModes:
            - "ReadWriteOnce"
            resources:
              requests:
                storage: 1Gi
  patroni:
    dynamicConfiguration:
      postgresql:
        parameters:
          max_parallel_workers: 2
          max_worker_processes: 2
          shared_buffers: 20MB
          work_mem: 2MB
```

Deploy this yaml file and see what happens. Note that the cluster is not really highly available, as there is only one postgres (replica) pod running! Update the above yaml file to have 2 replica's and deploy again (without first removing the `PostgresCluster`). What happens ? Can you check the logs of the newly started postgres pod ? What does it do ?

See [here](https://access.crunchydata.com/documentation/postgres-operator/v5/tutorial/high-availability/) for the full documentation.

## A small final note: should you actually do this ?

It might now sound tempting to actually do this for production workloads. Why go through the trouble of procuring a SAAS SQL database like RDS or Azure PostgreSQL, which often requires extra configuration and might have a very hard to predict cost ? With some extra configuration (out of scope for this tutorial) you can even set up streaming WAL backups to amazon S3 or Azure blob storage!

However, there are still quite some reasons to not do it. The most important one is that the maintenance burden is on you. There might be a bug in the opensource crunchydb operator which one day (maybe due to an unrelated upgrade of say, the kubernetes version) causes an outage. Then it will be you or your collegues searching for a solution. One day, you will have to upgrade the operator and the version of postgreSQL. Most probably this will be documented extensively, but you will probably want to try it out first on a test environment before doing the upgrade in production.

For a smaller project (or a big project that only has a small relational DB), most probably, it will be not worth the trouble, and a SAAS will be a better option. Only when you have the scale (and hence the team capacity), deploying your own solution will give you an advantage.

This was already true before the advent of Kubernetes, but with the higher level of automation that kubernetes operators offer compared to installing postgreSQL on a bare-metal linux machine, it becomes much less obvious, but still true.


