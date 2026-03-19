from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.search import router as search_router
from app.api.routes.sync import router as sync_router
from app.api.routes.vapi_tools import router as vapi_tools_router

router = APIRouter()
router.include_router(health_router)
router.include_router(search_router)
router.include_router(sync_router)
router.include_router(vapi_tools_router)
