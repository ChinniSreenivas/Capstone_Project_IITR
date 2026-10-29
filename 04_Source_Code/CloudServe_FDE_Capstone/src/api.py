"""FastAPI service for CloudServe Support Automation."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .pipeline import load_json, process_ticket
from .retrieve import Retriever


# Project paths and documentation
ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_PATH = ROOT / "data" / "documentation.json"
DECISIONS_PATH = ROOT / "storage" / "decisions.jsonl"

docs = load_json(DOCUMENTATION_PATH)
retriever = Retriever(docs)


# Create FastAPI application
app = FastAPI(
    title="CloudServe Support Automation",
    description="AI-assisted customer support ticket classification and routing.",
    version="1.0.0",
)


# Allow the local frontend to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Ticket request schema
class Ticket(BaseModel):
    ticket_id: str | None = None
    channel: str = "chat"
    subject: str = ""
    body: str = ""
    received_at: str | None = None
    customer_id: str | None = None
    customer_tier: str | None = None
    customer_region: str | None = None
    language_fluency: str | None = None


# Health check
@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
    }


# Process a submitted support ticket
@app.post("/tickets")
def create_ticket(ticket: Ticket):
    try:
        result = process_ticket(
            ticket.model_dump(),
            retriever,
            str(DECISIONS_PATH),
        )
        return result

    except Exception as exc:
        # Keep internal exception details out of the API response.
        raise HTTPException(
            status_code=500,
            detail=(
                "Ticket processing failed safely. "
                "Please submit the request for manual review."
            ),
        ) from exc