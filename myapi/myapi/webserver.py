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

# Keycloak setup
from keycloak import KeycloakOpenID

server_url = os.getenv("KEYCLOAK_SERVER_URL", "https://blah.blah/auth/")
client_id = os.getenv("KEYCLOAK_CLIENT_ID", "blah")
realm_name=  os.getenv("KEYCLOAK_REALM_NAME", "blah")
client_secret =  os.getenv("KEYCLOAK_CLIENT_SECRET", "")
server_internal_url = os.getenv("KEYCLOAK_SERVER_INTERNAL_URL",server_url)
keycloak_openid = KeycloakOpenID(
    server_url=server_internal_url,
    client_id=client_id,
    realm_name=realm_name,
    verify=False
)

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

oauth2_scheme = OAuth2AuthorizationCodeBearer(authorizationUrl="", tokenUrl="")

#app.mount("/static", StaticFiles(directory="static"), name="static")

kc_pubkey_cache = {}
async def kc_get_current_user(request: Request):
    token = None
    try:
        token = await oauth2_scheme(request)
    except:
        pass
    if token is None:
        return None
    if not "key" in kc_pubkey_cache:
        pubkey = keycloak_openid.public_key()
        kc_pubkey_cache["key"] = pubkey
    KEYCLOAK_PUBLIC_KEY = (
        "-----BEGIN PUBLIC KEY-----\n"
        + kc_pubkey_cache["key"]
        + "\n-----END PUBLIC KEY-----"
    )
    tk = None
    try:
        tk =  keycloak_openid.decode_token(
            token,
            key=KEYCLOAK_PUBLIC_KEY,
            options={"verify_signature": True, "verify_aud": False, "exp": True},
        )
    except jose.exceptions.ExpiredSignatureError:
        logging.info(f"token has expired, treating as not logged in")
        return None

    logging.info(f"got jwt token {str(tk)}")
    if tk is None:
        return None
    return tk








@app.get("/time")
async def clientsettings(request: Request):
    from datetime import datetime
    n = datetime.now()
    return {
        "current": n.strftime("%d/%m/%Y %H:%M:%S")
    }
