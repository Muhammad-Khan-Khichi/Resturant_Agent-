import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.database import init_db
from api.routes import auth, history, menu, search, session, webhook

load_dotenv()
logging.basicConfig(level=logging.INFO)



@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  
    yield


app = FastAPI(
    title="Restaurant Agent API",
    version="1.0.0",
    description="FastAPI backend for the LiveKit multi-agent restaurant system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router)
app.include_router(session.router)
app.include_router(menu.router)
app.include_router(search.router)
app.include_router(webhook.router)
app.include_router(history.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}