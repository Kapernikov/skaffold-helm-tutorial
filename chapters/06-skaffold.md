# Introducing skaffold.

Now we pushed the images by hand.  Let's see if we can automate the building and pushing.
Create a `skaffold.yaml` file in the root of this project and put the following in:

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

