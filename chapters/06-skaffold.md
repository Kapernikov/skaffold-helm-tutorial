# Introducing skaffold

So far we had:

* **docker** for building container images (and running them locally but we typically only do that for testing)
* **a docker registry** for storing the container images and making them accessible for kubernetes to use
* **yaml files** to describe what containers / pods / ... we actually want to run in kubernetes. These yaml files could refer to docker images we created ourselves.
* **kubectl** as a tool to make requests to the kubernetes API (and create objects based on yaml files).
* **helm** for packaging yaml files together and making stuff configurable.

Let's add something new now. Suppose we are now working on a real app, and we want to make some code changes and deploy them. What we would need to do:

* first make the code changes.
* then build new docker images. Better give them a different tag than the old docker images so we can tell them apart.
* then push the new docker images to the docker registry.
* then re-deploying the yaml files to kubernetes.  Probably using helm: the container images we want to use will be settings in helm. So we change the settings before deploying.

That's a lot of steps. So kubernetes is cool but it slows down our development 😔.

This is where skaffold comes in the picture. Skaffold is a little glue layer (it is more than that, but we use it as that for now) that:

* builds the docker images
* pushes them
* then deploys your kubernetes resources (optionally using helm) with the docker images it just built

And it does everything with one single command.

Let's try this:

Create a `skaffold.yaml` file **in the root of this project** and put the following in:

```yaml
apiVersion: skaffold/v2beta10
kind: Config
metadata:
    name: myapp
build:
    local:
      concurrency: 0
    artifacts:
      - image: api
        context: myapi
        docker:
          dockerfile: docker/Dockerfile
        sync:
          infer:
            - "*.py"
            - "**/*.py"
            - "**/*.html"
      - image: frontend
        context: frontend
        docker:
          dockerfile: docker/Dockerfile.dev
        sync:
          infer:
            - "*.js"
            - "*.html"
            - "*.vue"
            - "**/*.vue"
            - "**/*.js"

deploy:
  helm:
    releases:
      - name: myapp
        chartPath: myapp
        artifactOverrides: 
          frontend.image: frontend
          api.image: api

portForward:
  - resourceType: service
    resourceName: frontend
    port: 80
    localPort: 8080
  - resourceType: service
    resourceName: api
    port: 80
    localPort: 9999
```

Question

* Try to understand the skaffold "build" section.
* Try to understand the skaffold "deploy" section (especially "artifactOverrides")
* Can you try to make one of the templates invalid (eg just put some gibberish invalid yaml). Just like in last chapter. What error do you get now ? Is it a skaffold error or a helm error ? What happens if you introduce a syntax error in the skaffold.yaml ?


Ok let's build and push the images!

```shell
skaffold build -d registry.kube-public
```

We can also deploy them:

```shell
skaffold run -d registry.kube-public
```

Question:

* try "skaffold dev" instead of "skaffold run". What happens.
* While skaffold dev is running, change (and save) HelloWorld.vue from frontend/src/components. What happens ?
* now try skaffold dev with some extra arguments: `--auto-build=false` `--auto-deploy=false` and `--cleanup=false`. Now try the above experiment again.
* we're done now with this chapter. can you clean up (using skaffold off course) ?

## Wrapping up

We added one more thing to the equation: skaffold. It is important to note that **skaffold does not replace any of the components we used so far**, it just glues them together to speed up the development experience.

![skaffold-stages](../imgs/skaffold-stages.png)

In addition to this, it has a live syncing feature to have even faster development cycles, but they only work for certain technologies: basically, skaffold needs to be able to update a project by just writing a file to the source code. For python this works (if the server does autoreloading), but for compiled languages like C++ this won't work since just putting a C++ file will not do anything: you need to recompile and restart the software.

Skaffold also has built in facilities for setting up remote debugging of certain technologies.

