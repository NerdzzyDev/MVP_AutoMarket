from fastapi import FastAPI, HTTPException

from app.routers import cart_router, favorites_router, search_router, support_router, user_router, vehicle_router

from app.routers.v1 import tests_endpoints

from fastapi.middleware.cors import CORSMiddleware

from app.core.error_handlers import http_exception_handler, unhandled_exception_handler


app = FastAPI(title="Fix Autoteile API", root_path="/api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)


# 👇 Регистрируем глобальные хендлеры
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


app.include_router(search_router.router)
app.include_router(user_router.router)
app.include_router(vehicle_router.router)
app.include_router(favorites_router.router)
app.include_router(cart_router.router)
app.include_router(support_router.router)

# ai
app.include_router(tests_endpoints.router)