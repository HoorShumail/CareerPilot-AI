from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI) -> None:
    # In production, specify the actual frontend origins
    origins = [
        "http://localhost",
        "http://localhost:8501", # Streamlit
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
