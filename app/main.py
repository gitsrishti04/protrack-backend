from fastapi import FastAPI
from app.database import engine, Base
from app.models import user
from app.routes import auth
from app.routes import test
from fastapi.middleware.cors import CORSMiddleware
from app.routes import projects
from app.routes import dashboard
from app.routes import predictions
from app.routes import chat
from app.models import project
from app.models import progress_history




app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(projects.router)
app.include_router(auth.router)
app.include_router(test.router)
app.include_router(dashboard.router)
app.include_router(predictions.router)
app.include_router(chat.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:4173",
        "http://localhost:8080",   # Current dev server
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "ProTrack AI Backend Running "}