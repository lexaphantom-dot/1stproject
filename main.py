
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def read_h():
    return {"Hello": "World"}

@app.get("/")
async def read_root():
    return {"pid": "or"}