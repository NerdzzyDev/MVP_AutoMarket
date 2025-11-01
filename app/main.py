from fastapi import FastAPI

from app.routers import cart_router, favorites_router, search_router, user_router, vehicle_router

app = FastAPI(title="Fix Autoteile API")

app.include_router(search_router.router)
app.include_router(user_router.router)
app.include_router(vehicle_router.router)
app.include_router(favorites_router.router)
app.include_router(cart_router.router)
