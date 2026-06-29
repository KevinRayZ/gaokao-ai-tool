"""FastAPI 入口"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.config import settings
from app.api.routes import router
from app.api.admin import admin_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件（为 Phase 2 前端预留）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(router)
app.include_router(admin_router)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup_init():
    """启动时确保 data 目录存在"""
    Path("data").mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端页面"""
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return f.read()
