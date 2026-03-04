from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes.scorecard_form import router as scorecard_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://central.myamazonguy.com"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scorecard_router)

#uvicorn main:app --reload