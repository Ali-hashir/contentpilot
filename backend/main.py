from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os, re, datetime, requests, textwrap

app = FastAPI(title="ContentPilot Backend", version="0.3.0")

# --------- Models ---------
class Health(BaseModel):
    status: str = "ok"

class WriteReq(BaseModel):
    keyword: str = Field(..., description="Primary topic or search intent")
    serp_context: Optional[str] = ""
    tone: str = Field("neutral", description="friendly | expert | casual | formal")
    words: int = Field(800, ge=200, le=3000)
    outline: Optional[List[str]] = None

class WriteResp(BaseModel):
    title: str
    filename: str
    word_count: int
    content: str

class ImgReq(BaseModel):
    title: str
    style: Optional[str] = "photo-realistic"

class ImgResp(BaseModel):
    prompt: str

# --------- Config ---------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b-instruct-q5_K_M")
TIMEOUT = 120

# --------- Helpers ---------
def slugify(text: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9\- ]+", "", text)
    t = re.sub(r"\s+", "-", t.strip())
    return t.lower()

def build_prompt(req: WriteReq) -> str:
    outline = req.outline or [
        f"What is {req.keyword}?",
        "Key Benefits",
        "How It Works (Step by Step)",
        "Practical Tips & Pitfalls",
        "Examples & Use Cases",
        "Conclusion"
    ]
    serp = req.serp_context or "No SERP context provided."
    outline_str = "\n".join([f"- {h}" for h in outline])
    return f"""You are an expert technical writer.

Write a {req.words}-word blog post in MARKDOWN about: "{req.keyword}"
Tone: {req.tone}.
Use H2 for each section.

SERP context (what competitors cover):
{serp}

Required outline (each item must be an H2):
{outline_str}

Constraints:
- Be original; do NOT copy source phrasing.
- Use short paragraphs.
- Include a brief intro before the first H2.
- Finish with a clear 'Conclusion' section.
Return only Markdown."""
    
def call_ollama(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    # payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 2048,     # reduce memory use
            "num_predict": 600   # keep outputs reasonable
        }
    }
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        # Response shape: {"model": "...", "created_at": "...", "response": "...", ...}
        return data.get("response", "").strip()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

# --------- Endpoints ---------
@app.get("/ping", response_model=Health)
def ping():
    return {"status": "ok"}

@app.post("/agents/write", response_model=WriteResp)
def write_article(req: WriteReq):
    prompt = build_prompt(req)
    md = call_ollama(prompt)
    if not md:
        raise HTTPException(500, "Empty response from model")

    title = (req.keyword or "Article").strip().capitalize()
    date_prefix = datetime.date.today().isoformat()
    filename = f"{date_prefix}-{slugify(req.keyword or 'article')}.md"
    wc = len(re.findall(r"\w+", md))
    return WriteResp(title=title, filename=filename, word_count=wc, content=md)

@app.post("/agents/imagist", response_model=ImgResp)
def imagist(req: ImgReq):
    style_map = {
        "photo-realistic": "high dynamic range, studio lighting, 35mm lens",
        "illustration": "flat vector, minimal, bold shapes, clean background",
        "cinematic": "cinematic lighting, shallow depth of field, 4k detail, dramatic",
        "isometric": "isometric, pastel palette, sharp edges, subtle shadows",
    }
    style = style_map.get((req.style or "photo-realistic").lower(), style_map["photo-realistic"])
    prompt = f"{req.title}, ultra-detailed, {style}"
    return ImgResp(prompt=prompt)
