from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ContentPilot Backend", version="0.1.0")

class Health(BaseModel):
    status: str = "ok"

@app.get("/ping", response_model=Health)
def ping():
    """Simple health-check endpoint."""
    return {"status": "ok"}
