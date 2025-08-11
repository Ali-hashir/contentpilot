from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import random, textwrap, datetime, re

app = FastAPI(title="ContentPilot Backend", version="0.2.0")

# --------- Models ---------
class Health(BaseModel):
    status: str = "ok"

class WriteReq(BaseModel):
    keyword: str = Field(..., description="Primary topic or search intent")
    serp_context: Optional[str] = Field("", description="Top results/titles you found")
    tone: str = Field("neutral", description="friendly | expert | casual | formal")
    words: int = Field(800, ge=200, le=3000)
    outline: Optional[List[str]] = Field(
        None, description="Optional list of H2 sections to enforce"
    )

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

# --------- Helpers ---------
def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9\- ]+", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text.lower()

def _intro(keyword: str, tone: str) -> str:
    bank = {
        "friendly": f"If you're exploring {keyword}, this guide breaks it down in plain English.",
        "expert": f"This article presents a practitioner’s overview of {keyword}, with tradeoffs and implementation notes.",
        "casual": f"Let’s talk about {keyword}—what it is, why it matters, and how to use it without headaches.",
        "formal": f"This document provides a structured overview of {keyword}, including definitions, benefits, and considerations.",
        "neutral": f"This guide covers the essentials of {keyword}, including key concepts and practical tips.",
    }
    return bank.get(tone, bank["neutral"])

def _paras(topic: str, n: int, tone: str) -> str:
    # Very simple stub paragraphs to simulate structure (we will swap with a real LLM later).
    seeds = [
        f"{topic} can be approached step by step. Start simple, validate early, and iterate.",
        f"Common pitfalls include over-optimisation and skipping measurement. Define what 'good' means first.",
        f"In practice, teams succeed with small proofs of concept that de-risk assumptions.",
        f"A helpful mental model is input → process → output, backed by logging and feedback loops.",
        f"When constraints are tight, reduce scope and protect the critical path.",
    ]
    random.shuffle(seeds)
    paras = []
    for i in range(n):
        base = seeds[i % len(seeds)]
        extras = " " + random.choice(seeds)
        text = base + extras
        paras.append(textwrap.fill(text, width=96))
    return "\n\n".join(paras)

def _default_outline(keyword: str) -> List[str]:
    return [
        f"What is {keyword}?",
        "Key Benefits",
        "How It Works (Step by Step)",
        "Practical Tips & Pitfalls",
        "Examples & Use Cases",
    ]

# --------- Endpoints ---------
@app.get("/ping", response_model=Health)
def ping():
    return {"status": "ok"}

@app.post("/agents/write", response_model=WriteResp)
def write_article(req: WriteReq):
    title = req.keyword.strip().capitalize()
    outline = req.outline or _default_outline(req.keyword)
    date_prefix = datetime.date.today().isoformat()
    filename = f"{date_prefix}-{slugify(req.keyword)}.md"

    sections = []
    # Intro
    sections.append(_intro(req.keyword, req.tone))

    # Sections based on outline
    for h2 in outline:
        body = _paras(h2, n=2, tone=req.tone)
        sections.append(f"## {h2}\n{body}")

    # Light reference to serp_context (if provided)
    if req.serp_context:
        sections.append("## Sources & Further Reading\n" + textwrap.fill(req.serp_context, 96))

    conclusion = _paras("Conclusion", n=1, tone=req.tone)
    sections.append(f"## Conclusion\n{conclusion}")

    md = f"# {title}\n\n" + "\n\n".join(sections).strip()
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
