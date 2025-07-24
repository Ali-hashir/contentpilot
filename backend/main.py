from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="ContentPilot Backend", version="0.1.0")

# Health Check Endpoint
class Health(BaseModel):
    status: str = "ok"

@app.get("/ping", response_model=Health)
def ping():
    """Simple health-check endpoint."""
    return {"status": "ok"}

# Write Endpoint
# This endpoint simulates writing a markdown document based on a keyword.
# It is intended to be used with n8n for testing purposes.
class WriteReq(BaseModel):
    keyword: str
    words: int = 250

@app.post("/agents/write")
def write(req: WriteReq):
    """Return dummy markdown so n8n→GitHub wiring can be tested."""
    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    md = f"""# {req.keyword.title()}

_This draft was auto-generated at **{timestamp}Z**._

Lorem ipsum dolor sit amet … (replace with AI text later)."""
    return {"content": md}