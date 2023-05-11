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

API and frontend are stateless applications, meaning they don't retain any data over time. A database is different as per definition it will retain data. If we want to deploy a set of pods in our cluster for a database and provide guarantees about the ordering and uniqueness of these Pods, we have to implement a StatefulSet instead of a deployment

Like a Deployment, a StatefulSet manages Pods that are based on an identical container spec. Unlike a Deployment, a StatefulSet maintains a sticky identity for each of its Pods. These pods are created from the same spec, but are not interchangeable: each has a persistent identifier that it maintains across any rescheduling.

Let's create a database kubernetes StatefulSet
```yaml
# PostgreSQL StatefulSet
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-db
spec:
  serviceName: postgresql-db-service
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
      env:
      - name: POSTGRES_PASSWORD
        value: astrongdatabasepassword
      - name: PGDATA
        value: /data/pgdata
  # Volume Claim
volumeClaimTemplates:
  - metadata:
      name: postgresql-db-disk
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 2Gi
```

## Linking our database to our deployment through a Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-db-svc
spec:
  selector:
    app: postgresql-db
  ports:
  - port: 5432
```

test to query time-from-db. To do so, rebuild your image by adding psycopg2 pip package on the dockerfile.
```dockerfile
RUN pip install psycopg2
```
Questions!

* Can you try to scale our deployment up and down ? Using k9s ? Using kubectl ?
* Can you port-forward our deployment to something on our computer (shift-f in k9s) ?
* Ok, next up is helm. Let's clean up and remove our deployment. We'll recreate it soon using helm. Try cleaning up the deployment using kubectl!


## Wrapping up

So, we now created a **deployment** that in its turn created a **pod**. This pod has one container (because it is created from a pod template that specifies one single container) created from the docker image `registry.kube-public/myfrontend`.

![frontend-deployment](../imgs/frontend-deployment.png)

