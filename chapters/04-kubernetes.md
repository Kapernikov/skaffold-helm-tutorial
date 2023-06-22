# Going to kubernetes with our application!

## Pushing our container images to the registry (in kubernetes)

So... we have a docker registry running on kubernetes, which was called `registry.kube-public`. In docker, if you want to push an image to a container registry, you need to name/tag it so its called `[registry-url]/[image-tag]`. We didn't do this for our frontend nor backend. Let's do it! now!

```shell
## frontend!
docker tag myfrontend registry.kube-public/myfrontend
docker push registry.kube-public/myfrontend

## API!
docker tag myapi registry.kube-public/myapi
docker push registry.kube-public/myapi
```

Ok! so now our docker images are in a docker registry that is accessible by kubernetes. We can now try to run it!

> Note: some dev/test kubernetes distributions (minikube or docker desktop for windows) allow you to work **without** a registry: all images known to the local docker daemon are automatically also known in kubernetes. This only works however if you're not working remotely.


## Creating a deployment for our frontend

Let's create a frontend kubernetes Deployment (doesn't matter where, we will move it later):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      imagePullSecrets:
        - name: registry-creds
      containers:
        - name: frontend
          image: registry.kube-public/myfrontend
```

Now we need to apply it with `kubectl apply -f [thefile.yaml]`. If you get ImagePullBackoff you still need to create your image pull secret (see the first chapter for details).



Let's check if we can see the deployment:

```shell
kubectl get deployment
```

a deployment should create pods, so let's check if they are there:

```shell
kubectl get pod
```

The same should be possible in k9s: you can go to the deployments by typing `:` followed by *deploy*.

## Creating a StatefulSet for a database

We need a database too, so let's set up a simple `postgres` database. We can't just do this the way we did it with the frontend!

* API and frontend are stateless applications, meaning they don't retain any data over time. A database is different as per definition it will retain data. So we will need storage volumes here.
* We need a kubernetes statefulset here. Let's see why.

Like a Deployment, a StatefulSet manages Pods that are based on an identical container spec. Unlike a Deployment, a StatefulSet maintains a sticky identity for each of its Pods. These pods are created from the same spec, but are not interchangeable: each has a persistent identifier that it maintains across any rescheduling.

Statefulsets have another difference with deployment: 
- For a deployment, when a new version is rolled out, old pod is terminated **after** the new one is created
- For a statefulSet, when a new version is rolled out, old pod is terminated **before** the new one is created

Each behaviour as its use case: 
- Deployment's one enable no down time between two versions.
- Statefulset's one doesn't break the state. For databases this means all transactions have to be completed on the old pod before a new one is created.

We also want to initialize our database: we want to create a table. We don't strictly need to do this during deployment (we could also connect to the database and create the table once its running), but the postgresql docker image has a way to do this at launch. We will use it.

For this, we need to have a file present in the container under `/docker-entrypoint-initdb.d`. We will create a `ConfigMap` object and mount it under this path in the container.

A configmap is just a set of key-value pairs stored in the kubernetes database. We can do multiple things with it:

* use them as environment variables in a pod
* mount them as a volume in a pod
* retrieve and update them using the kubernetes API

Let's create a configmap with our init script:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgresql-initdb-config
data:
  init.sql: |
    CREATE TABLE IF NOT EXISTS counter (
      counterId SERIAL PRIMARY KEY ,
      api TEXT NOT NULL,
      counter INTEGER NOT NULL default 0
    );

    INSERT INTO counter (api) VALUES ('myapi');
```

Now we can create the statefulset:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-db
spec:
  selector:
    matchLabels:
      app: postgresql-db
  replicas: 1
  template:
    metadata:
      labels:
        app: postgresql-db
    spec:
      containers:
      - name: postgresql-db
        image: postgres:latest
        volumeMounts:
        - name: postgresql-db-disk
          mountPath: /data
        - name: postgresql-initdb
          mountPath: /docker-entrypoint-initdb.d
        env:
        - name: POSTGRES_PASSWORD
          value: astrongdatabasepassword
        - name: PGDATA
          value: /data/pgdata
      volumes:
      - name: postgresql-initdb
        configMap:
          name: postgresql-initdb-config
  volumeClaimTemplates:
    - metadata:
        name: postgresql-db-disk
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 2Gi
```

As you can see, we don't define a `PersistentVolumeClaim` directly, but we use `volumeClaimTemplates`. This way, if we were to create multiple replica's, each replica would get its own volume. This would still not give us database replication however, as each replica would have its own database. We will fix this in a later chapter.

A lot is happening there, let's point the interesting parts one by one: 
* The pod created from this StatefulSet will be accessed through another component called a service that we will cover in depth on the next chapter. The serviceName key map this.
* For a pod to retain data even with downtime, we need to assign it a volume. There a multiple ways to create and assign volumes. For this use case, we use what is called a volumeClaimTemplates.

Questions!

* Can you try to scale the **deployment** up and down ? Using k9s ? Using kubectl ?
* Can you port-forward our deployment to something on your computer computer (shift-f in k9s, or using `kubectl port-forward`) ?

## Wrapping up

So, we now created a **deployment** and a **statefulset** that in its turn created a **pod**. These pods have one container (because it is created from a pod template that specifies one single container) created from either the docker image `registry.kube-public/myfrontend` or the public image `postgres:latest`.

![frontend-deployment](../imgs/frontend-deployment.png)

