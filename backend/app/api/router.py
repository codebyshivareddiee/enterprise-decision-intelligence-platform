"""Main API router."""

from fastapi import APIRouter

from app.api.v1 import auth, business_rules, decisions, health, knowledge, organizations, workspaces

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(workspaces.router)
api_router.include_router(knowledge.router)
api_router.include_router(decisions.router)
api_router.include_router(decisions.ws_router)
api_router.include_router(business_rules.router)
