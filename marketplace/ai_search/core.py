

from transformers import pipeline
from fastapi import APIRouter

router = APIRouter()
searcher = pipeline(
    "text-classification", 
    model="distilbert-base-uncased",
    tokenizer="distilbert-base-uncased"
)

def expand_query(query: str) -> list[str]:
    """Generate semantic variations of search terms"""
    return [
        query,
        searcher.tokenizer.mask_token.replace("[MASK]", query),
        f"vintage {query}" if "old" in query else query
    ]

@router.post("/search")
async def semantic_search(query: str):
    return {
        "original_query": query,
        "expanded_terms": expand_query(query),
        "matches": searcher(query)
    }

