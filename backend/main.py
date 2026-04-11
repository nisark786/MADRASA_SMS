from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import init_redis, close_redis
from app.core.seed import seed_database

from app.api.v1 import auth, users, roles, permissions, widgets, students, forms


def setup_tracing():
    """Initialize OpenTelemetry tracing — called inside lifespan so Jaeger has time to start."""
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    resource = Resource.create({"service.name": "students-backend"})
    provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)
    return FastAPIInstrumentor


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    print("🚀 Starting up...")

    # Connect Redis first
    await init_redis()
    print("✅ Redis connected")

    # Initialize tracing (safely inside lifespan — Jaeger may not be ready at import time)
    try:
        instrumentor = setup_tracing()
        instrumentor.instrument_app(app)
        print("✅ Tracing initialized")
    except Exception as e:
        print(f"⚠️ Tracing setup failed (non-fatal): {e}")

    # Wait for PostgreSQL to be ready (retry up to 30s)
    for attempt in range(15):
        try:
            # We no longer auto-create tables via SQLAlchemy. 
            # Alembic will handle this going forward via CI/CD.
            async with engine.begin() as conn:
                # await conn.run_sync(Base.metadata.create_all)
                pass
            print("✅ Database connection ready (Auto-create disabled)")
            break
        except Exception as e:
            if attempt == 14:
                raise RuntimeError(f"Could not connect to PostgreSQL after 15 attempts: {e}")
            print(f"⏳ Waiting for database... attempt {attempt + 1}/15")
            await asyncio.sleep(2)

    # Seed default data
    async with AsyncSessionLocal() as db:
        await seed_database(db)

    yield  # App is running

    # Shutdown
    await close_redis()
    print("👋 Shutting down...")


app = FastAPI(
    title="Students Data Store API",
    description="Dynamic RBAC + Widget Dashboard Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[url.strip() for url in settings.FRONTEND_URL.split(",") if url.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,        prefix="/api/v1")
app.include_router(users.router,       prefix="/api/v1")
app.include_router(roles.router,       prefix="/api/v1")
app.include_router(permissions.router, prefix="/api/v1")
app.include_router(students.router,    prefix="/api/v1")
app.include_router(widgets.router,     prefix="/api/v1")
app.include_router(forms.router,       prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Students Data Store API 🚀", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
