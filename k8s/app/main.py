"""k8s-tutorial app tier — FastAPI middleware between the nginx web tier and Postgres.

Simulates the MkDocs tutorial itself: serves the curriculum as JSON and tracks
per-step completion in the `progress` table (created in step 1.3):

    step INT PRIMARY KEY, done BOOLEAN DEFAULT false, ts TIMESTAMPTZ

Config comes entirely from env vars — DB_HOST/DB_NAME/DB_USER arrive via the
ConfigMap, DB_PASSWORD via the postgres-creds Secret (secretKeyRef).
"""

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Env-driven config — pydantic-settings maps DB_HOST -> db_host, etc."""

    db_host: str = "pg-postgresql"
    db_name: str = "tutorial"
    db_user: str = "app_user"
    db_password: str = ""


class ProgressUpdate(BaseModel):
    step: int
    done: bool = True


class Step(BaseModel):
    step: int
    ref: str
    phase: int
    title: str
    done: bool = False


settings = Settings()

# The tutorial curriculum, mirroring the mkdocs pages — the web tier renders
# this list and flips `done` via POST /api/progress.
STEPS = [
    Step(step=1, ref="0.1", phase=0, title="Scaffold the project directory"),
    Step(step=2, ref="0.2", phase=0, title="Verify cluster access"),
    Step(step=3, ref="0.3", phase=0, title="Imperative playground"),
    Step(step=4, ref="1.1", phase=1, title="Namespace + Secrets"),
    Step(step=5, ref="1.2", phase=1, title="Deploy PostgreSQL via Helm"),
    Step(step=6, ref="1.3", phase=1, title="DB user & password management"),
    Step(step=7, ref="1.4", phase=1, title="Cluster DNS & Services"),
    Step(step=8, ref="2.1", phase=2, title="Write the app"),
    Step(step=9, ref="2.2", phase=2, title="Build the image"),
    Step(step=10, ref="2.3", phase=2, title="Deployment + ConfigMap + Secret wiring"),
    Step(step=11, ref="2.4", phase=2, title="Probes & self-healing"),
    Step(step=12, ref="2.5", phase=2, title="Resources & metrics"),
]

app = FastAPI(title="k8s-tutorial", version="0.1.0")


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=settings.db_host,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=3,
    )


@app.get("/healthz")
def healthz() -> dict:
    """Liveness: process is up. Never touches the DB."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    """Readiness: the real dependency check — fails when Postgres is unreachable."""
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail={"db": "unreachable"}) from exc
    return {"db": "ok"}


@app.get("/api/steps", response_model=list[Step])
def list_steps() -> list[Step]:
    """Curriculum joined with completion state from the progress table."""
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT step, done FROM progress")
            done = {step: done for step, done in cur.fetchall()}
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail={"db": "unreachable"}) from exc
    return [s.model_copy(update={"done": done.get(s.step, False)}) for s in STEPS]


@app.get("/api/progress")
def get_progress() -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT step, done, ts FROM progress ORDER BY step")
        rows = cur.fetchall()
    return [{"step": s, "done": d, "ts": t.isoformat()} for s, d, t in rows]


@app.post("/api/progress", response_model=Step)
def set_progress(update: ProgressUpdate) -> Step:
    """Upsert one step's completion — INSERT with ON CONFLICT (app_user has
    SELECT/INSERT/UPDATE on progress, deliberately not DDL rights)."""
    try:
        step = next(s for s in STEPS if s.step == update.step)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="unknown step") from exc
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO progress (step, done)
            VALUES (%s, %s)
            ON CONFLICT (step) DO UPDATE SET done = EXCLUDED.done, ts = now()
            """,
            (update.step, update.done),
        )
    return step.model_copy(update={"done": update.done})
