# Dockerizing the frontend application

Let's do the same, doing the same trick as with backend: create
`frontend/docker/Dockerfile.dev`:

```Dockerfile
FROM node:14-buster as build-stage
MAINTAINER Frank
RUN apt-get update -y && apt-get install unzip zip git python3-distutils -y && \
    curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py
    
RUN npm install -g @vue/cli 
 
    
ENV NODE_OPTIONS="--max-old-space-size=8192"
ADD package.json package-lock.json* /source/
WORKDIR /source
RUN npm install
ADD . /source
WORKDIR /source
RUN npm install && cp .env.k8s .env
CMD npm run serve -- --port=80 --publicPath=. --disableHostCheck=true
```

Some questions:
* Try to build and run the container image. does it work ?
* Do you see the tricks here that we used to make the dockerfile efficient ?
* What is the startup time of a docker container ?

<details>
  <summary>Click here to see the super secret way to start a docker container!</summary>
  
This is how!

```shell
docker build -t myfrontend . -f docker/Dockerfile.dev
docker run -p 8888:80 -it --rm myfrontend
```

</details>