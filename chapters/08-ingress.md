# Creating ingress for our application

Up to now, we did all development using forwarded ports. Let's make ingress rules for production.
First, head over to https://www.duckdns.org/ to get yourself a free domain name for your current ip (if you don't know your ip, its likely shown when you do `hostname -I`)

Suppose our domain name is now frank-test.duckdns.org. Let's now create an ingress yaml (we are not using https for now):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  rules:
  - host: frank-test.duckdns.org
    http:
      paths:
      - path: "/(time|settings)(.*)"
        pathType: ImplementationSpecific
        backend:
          service:
            name: api
            port:
              number: 80
      - path: "/(.*)"
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend
            port:
              number: 80
```

Questions:

* This won't work yet because the frontend won't find the backend (it tries localhost:8888 as url)
* can you try to fix it in helloworld.vue ?
* Can you make the host configurable in the helm chart ?
* Does this work with your helloworld.vue fix ?

Actually the answer to the last question is no: the helloworld.vue is only read when *building the docker image*. Which is long before it is deployed on kubernetes as part of a helm chart. So the nodeJS environment never actually sees the helm values. It is important that you understand this, fixing this is beyond the scope of this tutorial (unless you make a pull request to add it!).

Some extra's if you found this too easy:

* Try to make the ingress work with https and proper letsencrypt https certificates
* Actually fix the configurable host by using relative urls to the backend.
