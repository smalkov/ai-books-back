from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app import opds_search

app = FastAPI(title="Flibusta API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/search")
async def search_books(
    query: str = Query(..., min_length=2),
    limit: int = Query(15, ge=1, le=50)
):
    raw = opds_search(query, limit=limit)
    return JSONResponse(list(raw.values()))


# -------- точка входа при локальном запуске --------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,          # авто‑reload во время разработки
    )
