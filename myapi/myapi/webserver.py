import logging
import psycopg2
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

@app.get("/time-from-db")
async def get_time_from_db(request: Request):
    try:
        conn = psycopg2.connect(
            host="postgres",
            database="public",
            user="postgres",
            password="astrongdatabasepassword"
        )
        cur = conn.cursor()
        cur.execute('SELECT NOW()')
        n = cur.fetchone()
        cur.close()
    except:
        n = "Error while trying to reach the database"
    return {
        "current": n
    }
