from fastapi import FastAPI

from app.routers import cart_router, favorites_router, search_router, support_router, user_router, vehicle_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Fix Autoteile API", root_path="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)


app.include_router(search_router.router)
app.include_router(user_router.router)
app.include_router(vehicle_router.router)
app.include_router(favorites_router.router)
app.include_router(cart_router.router)
app.include_router(support_router.router)
