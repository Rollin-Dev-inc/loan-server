from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.items import router as items_router
from app.api.v1.loans import router as loans_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(items_router)
api_v1_router.include_router(loans_router)
