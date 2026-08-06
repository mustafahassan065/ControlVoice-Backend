from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine
import models
from routes import auth_routes, audio_routes, exercise_routes, program_routes, email_routes,progress_routes,stripe_routes,report_routes,challenge_routes,coach_routes, email_preference_routes
from scheduler import start_scheduler
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="VoiceControl AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://voicecontrol.tech",
        "https://www.voicecontrol.tech",
        "http://localhost:3000",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

class RawBodyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/stripe/webhook":
            body = await request.body()
            request.state.raw_body = body
        return await call_next(request)

app.add_middleware(RawBodyMiddleware)

app.include_router(auth_routes.router)
app.include_router(audio_routes.router)
app.include_router(exercise_routes.router)
app.include_router(program_routes.router)
app.include_router(email_routes.router)
app.include_router(progress_routes.router)
app.include_router(stripe_routes.router)
app.include_router(report_routes.router)
app.include_router(challenge_routes.router)
app.include_router(coach_routes.router)
app.include_router(email_preference_routes.router)

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/")
def root():
    return {"message": "VoiceControl AI Backend Running"}