import kubernetes as k8s
from kubernetes import config, utils as k8s_utils, client
import jose
import logging
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict
import os

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://192.168.0.195:9000",
    "http://192.168.0.195",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





#app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/time")
async def get_time(request: Request):
    from datetime import datetime
    n = datetime.now()
    return {
        "current": n.strftime("%d/%m/%Y %H:%M:%S")
    }
