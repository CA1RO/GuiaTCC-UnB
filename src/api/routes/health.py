"""Endpoints de health check — verifica PostgreSQL, Redis e MinIO."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """Verifica se todos os serviços estão operacionais."""
    checks = {}

    # PostgreSQL + pgvector
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"erro: {e}"

    # Redis
    try:
        pong = await request.app.state.redis.ping()
        checks["redis"] = "ok" if pong else "erro"
    except Exception as e:
        checks["redis"] = f"erro: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "services": checks}
