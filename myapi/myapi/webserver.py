import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/time")
async def get_time(request: Request):
    from datetime import datetime
    n = datetime.now()
    return {
        "current": n.strftime("%d/%m/%Y %H:%M:%S")
    }
