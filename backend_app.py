import sys
sys.path.insert(0, ".")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from retrieval.retriever import Retriever

app = FastAPI(title="Healthcare Knowledge Navigator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_retriever = None
def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever

class QueryRequest(BaseModel):
    question: str
    source_filter: list[str] | None = None
    min_year: int | None = None

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/query")
def query(req: QueryRequest):
    if not req.question or len(req.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question too short.")
    try:
        r = get_retriever()
        ans = r.query(
            question=req.question,
            source_filter=req.source_filter,
            min_year=req.min_year,
        )
        return {
            "question": ans.question,
            "answer": ans.text,
            "citations": ans.citations,
            "confidence_score": ans.conf_score,
            "confidence_label": ans.conf_label,
            "sources_used": ans.sources_used,
            "disclaimer": ans.disclaimer,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def stats():
    from embeddings.pinecone_store import PineconeStore
    return PineconeStore().stats()
