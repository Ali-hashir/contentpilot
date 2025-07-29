from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx, os, asyncio, re
from datetime import datetime, timezone
from pathlib import Path

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

app = FastAPI(title="ContentPilot Backend", version="0.2.0")


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
# ---------- article generator ----------
class WriteReq(BaseModel):
    keyword: str
    words: int = 500

ARTICLE_TEMPLATE = """
You are a professional copywriter.
Write an SEO-optimised blog post of {words} words about: "{keyword}".
Use Markdown, include:
- H2 headings
- a short intro
- a conclusion
Do NOT mention AI or that you are an AI.
"""

async def llama_complete(prompt: str) -> str:
    payload = {
        "model": "llama3:8b",
        "prompt": prompt,
        "stream": False
    }
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        if r.status_code != 200:
            raise HTTPException(500, r.text)
        return r.json()["response"]

@app.post("/agents/write")
async def write(req: WriteReq):
    md = await llama_complete(ARTICLE_TEMPLATE.format(**req.dict()))
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # small postfix so you can see content is fresh
    md += f"\n\n*Generated automatically on {timestamp}*"
    return {"content": md}

# ---------- hero image prompt ----------
class ImgReq(BaseModel):
    title: str

@app.post("/agents/imagist")
async def imagist(req: ImgReq):
    prompt = await llama_complete(
        f"Give me a concise Stable Diffusion prompt for a hero image that visualises: {req.title}."
        " Return only the prompt, no extra words."
    )
    # clean any quotes/linebreaks
    prompt = re.sub(r'["\'\n]', '', prompt).strip()
    return {"prompt": prompt}