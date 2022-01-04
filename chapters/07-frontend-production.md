# Creating a production dockerfile for our frontend

Up to now we ran the frontend from our nodejs development server. That's nice as it autocompiles stuff, but its also not nice because its not meant for production.
Let's try to fix that. We will create a new dockerfile, this time called just `Dockerfile` in our frontend/docker folder:

```Dockerfile
# stage 1
FROM node:14-alpine as build-stage
LABEL org.opencontainers.image.authors="Frank"
    
RUN npm install -g @vue/cli 
  
ENV NODE_OPTIONS="--max-old-space-size=8192"
ADD package.json package-lock.json* /source/
WORKDIR /source
RUN npm install
ADD . /source
WORKDIR /source
RUN npm install && cp .env.k8s .env && npm run build

# stage 2
FROM nginx:stable-alpine as production-stage
ADD docker/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build-stage /source/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

In our second stage, we use docker/default.conf as nginx configuration. Let's create a very simple one and save the following as frontend/docker/default.conf:

```nginx
server {
    listen       80;
    listen  [::]:80;
    server_name  localhost;

    location / {
        root   /usr/share/nginx/html;
        index  index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
```

Voila! Can you build and run this docker image locally ?

## Introducing skaffold profiles: make skaffold behave differently for dev and prod.

Let's first fix our skaffold yaml so that it uses the Dockerfile instead of Dockerfile.dev for our frontend. Now our skaffold is like a "production" one.
Now we'll introduce a "dev" profile in skaffold. Let's add the following section to the bottom of our skaffold yaml:

```yaml
profiles:
  - name: dev
    patches:
      - op: replace
        path: /build/artifacts/1/docker/dockerfile
        value: docker/Dockerfile.dev
```

So now we added a dev profile that patches the dockerfile from the second (0 is the first) artifact. We can select a profile when starting skaffold:

```shell
skaffold run -d registry.kube-public -p dev
```

