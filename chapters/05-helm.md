# Creating a helm chart

## Getting started.

Let's get started. Make sure you are in the root directory of this project (should be "skaffold-helm-tutorial") and do:

```shell
helm create myapp
```

Now we have some work to do:
* helm creates a lot of stuff to explain helm, we don't need it! make the file `values.yaml` empty, and remove all files and directory under the `templates` folder, but keep the templates folder!
* now move our deployment yaml from last excercise to the templates folder and .. voila we have a working helm chart (albeit not a very useful one)

We can try to install it:
```shell
helm install myapp-deployment-1 myapp
```

Did it work ? Let's quickly remove it and make it more useful:

```shell
# let's look at which helm packages we installed. note that helm packages are namespaced, so you will only see the helm packages installed in current namespace.
helm list
# if you want to list/install/uninstall in another namespace, use the `-n [namespace]` option. 
helm uninstall myapp-deployment-1
```

## Introduce stuff that's configurable.

Let's put the following in values.yaml:

```yaml
frontend: 
  image: trow.kube-public/myfrontend
```
Note that our values.yaml is a free form yaml. as long as its valid yaml you can put anything there.

Let's now adapt our deployment yaml for the frontend so it uses the value from values.yaml instead of the hardcoded one:

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
      containers:
      - name: frontend
        image: {{ .Values.frontend.image }}
```

Now we can actually vary our image using this syntax:

```shell
helm install myapp-deployment-1 myapp --set frontend.image=some.invalid/image
```

Questions:
* How does kubernetes react to our invalid image ?
* Can you clean up our helm chart again ?
* Can you also make the number of replicas configurable and try setting them using helm ?
* Do you think it is really needed to completely uninstall/reinstall a helm chart after making changes ?

## Introducing a service for the frontend

You can now append the following section to our deployment yaml we created earlier. Note that the `---` separates multiple objects in one yaml file. You could also just have started a new file. personal preference.

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  ports:
  - port: 80
    targetPort: 80
    name: frontend
  selector:
    app: frontend
```