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

@app.get("/counter")
def get_counter_from_db(request: Request):
    try:
        conn = psycopg2.connect(
            host="postgres-db",
            database="postgres",
            user="postgres",
            password="astrongdatabasepassword"
        )
        cur = conn.cursor()
        cur.execute("UPDATE counter SET counter = counter + 1 WHERE api = 'myapi'")
        conn.commit()
        cur.execute("SELECT counter FROM counter WHERE api = 'myapi'")
        n = cur.fetchone()[0]
        cur.close()
        conn.close()
    except:
        print("ERROR:    Cannot reach the database")
        n = -1
    finally:
        return {
            "counter": n
        }
