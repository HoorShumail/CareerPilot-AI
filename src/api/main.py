print("===== STARTING main.py =====")

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute          # <-- ADDED for safe route iteration

from src.api.middleware.cors import setup_cors
from src.api.middleware.rate_limit import RateLimitMiddleware

from src.api.routes import auth
from src.api.routes import resume
from src.api.routes import job
from src.api.routes import application
from src.api.routes import career_twin
from src.api.routes import career_intelligence
from src.api.routes import interview
from src.api.routes import matches
from src.api.routes.career_strategy import router as career_strategy_router

from src.config.logging import logger
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up %s", settings.PROJECT_NAME)

    from src.db.engine import async_session_maker
    from src.services.auth_service import AuthService

    async with async_session_maker() as session:
        auth_service = AuthService(session)
        await auth_service.ensure_superuser()

    yield

    logger.info("Shutting down %s", settings.PROJECT_NAME)


# -----------------------------------------------------------------------------
# Create App
# -----------------------------------------------------------------------------

from fastapi.responses import JSONResponse
from src.exceptions.base import CareerPilotException
from src.utils.json_repair import JSONParsingError

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

@app.exception_handler(CareerPilotException)
async def careerpilot_exception_handler(request, exc: CareerPilotException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.exception_handler(JSONParsingError)
async def json_parsing_exception_handler(request, exc: JSONParsingError):
    return JSONResponse(
        status_code=500,
        content={"detail": f"AI service malformed JSON output: {str(exc)}"},
    )

print("✓ FastAPI app created with exception handlers")

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

setup_cors(app)
print("✓ CORS configured")

app.add_middleware(RateLimitMiddleware)
print("✓ RateLimit middleware added")

# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------

print("Registering auth...")
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
print("✓ auth")

print("Registering resume...")
app.include_router(resume.router, prefix=f"{settings.API_V1_STR}/resumes", tags=["resumes"])
print("✓ resume")

print("Registering job...")
app.include_router(job.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["jobs"])
print("✓ job")

print("Registering application...")
app.include_router(application.router, prefix=f"{settings.API_V1_STR}/applications", tags=["applications"])
print("✓ application")

print("Registering matches...")
app.include_router(matches.router, prefix=f"{settings.API_V1_STR}/matches", tags=["matches"])
print("✓ matches")

print("Registering career twin...")
app.include_router(
    career_twin.router,
    prefix=f"{settings.API_V1_STR}/career-twin",
    tags=["career-twin"],
)
print("✓ career twin")

print("Registering career intelligence...")
app.include_router(
    career_intelligence.router,
    prefix=f"{settings.API_V1_STR}/career-coach",
    tags=["career-coach"],
)
print("✓ career intelligence")

print("Registering career strategy...")
app.include_router(
    career_strategy_router,
    prefix=settings.API_V1_STR,
    tags=["Career Strategy"],
)
print("✓ career strategy")

print("Registering interview...")
app.include_router(
    interview.router,
    prefix=f"{settings.API_V1_STR}/interview",
    tags=["interview"],
)
print("✓ interview")

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

print("✓ health endpoint")

# -----------------------------------------------------------------------------
# Print all registered routes (SAFE version)
# -----------------------------------------------------------------------------

print("\n========== REGISTERED ROUTES ==========")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(route.path, route.methods)
    else:
        # Skip internal objects like _IncludedRouter
        print(f"Skipped: {type(route).__name__}")
print("=======================================\n")