from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth, conversation, user, message, attachment
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .milvus_db import init_milvus


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting server, initializing resources")
    milvus_client = None
    try:
        milvus_client = init_milvus() 
        logger.info("Milvus done initialized successfully")
    except Exception as e:
        logger.error(f"Error occurred while initializing Milvus: {e}")
        
    yield

    # ---when server shuts down (SHUTDOWN) ---
    logger.info("Shutting down server, cleaning up resources")
    # (Sau này có thể thêm code ngắt kết nối Redis hoặc Milvus ở đây)
    if milvus_client:
        milvus_client.close() 
        logger.info("Closed Milvus connection cleanly.")

# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.project_name or "AI Chat Application",
    description=settings.project_description or "A conversational AI application with knowledge base integration.",
    lifespan=lifespan
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(message.router)
app.include_router(conversation.router)
app.include_router(attachment.router)

@app.get("/")
def test_main():
    return {"message": "Hello World!"}