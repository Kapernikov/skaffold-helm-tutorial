# Creating ingress for our application

Up to now, we did all development using forwarded ports. Let's make ingress rules for production.
First, head over to https://www.duckdns.org/ to get yourself a free domain name for your current ip (if you don't know your ip, its likely shown when you do `hostname -I`)

Suppose our domain name is now frank-test.duckdns.org. Let's now create an ingress yaml (we are not using https for now):

```yaml
apiVersion: networking.k8s.io/v1beta1
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
        backend:
          serviceName: api
          servicePort: 80
      - path: "/(.*)"
        backend:
          serviceName: frontend
          servicePort: 80
```

Questions:
* This won't work yet because the frontend won't find the backend (it tries localhost:8888 as url)
* can you try to fix it in helloworld.vue ?
* Can you make the host configurable in the helm chart ?
* Does this work with your helloworld.vue fix ?

For the hellowrold.vue fix, we need to use .env files.

