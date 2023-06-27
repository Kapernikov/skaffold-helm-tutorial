# Dockerizing the frontend application

Let's do the same, doing the same trick as with backend: create
`frontend/docker/Dockerfile.dev`:

```Dockerfile
FROM node:14-alpine

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
  <summary>Click here to see the solution to start a docker container!</summary>
  
This is how!

```shell
docker build -t myfrontend . -f docker/Dockerfile.dev
docker run -p 8888:80 -it --rm myfrontend
```

</details>

Now some more questions!

* Can you run both frontend and backend containers at the same time ?
* If it works the frontend should be able to get the current time from the API.
* Do you know how the frontend "found" the backend ? Where in the source code ?

 # Cleaning up

 Now in the next chapter we will move to kubernetes. Let's make sure there are no more docker containers running that occupy ports or we will get in trouble port forwarding later.

 ```shell
# this command should give nothing
docker ps
 ```

 If you still see docker containers in the above output, then kill them. There is an easy way to kill **all** docker containers:

 ```shell
 docker container kill $(docker ps -q)
 ```
 