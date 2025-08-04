"""
FastAPI webhook listener server for SBDK.dev
Handles GitHub webhooks and project tracking
"""

import asyncio
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="SBDK.dev Webhook Server",
    description="Webhook listener and tracking server for SBDK projects",
    version="1.0.1",
)


# Pydantic models for request/response
class ProjectRegistration(BaseModel):
    project_name: str
    email: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class UsageTracking(BaseModel):
    project_uuid: str
    command: str
    duration_seconds: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class WebhookEvent(BaseModel):
    event_type: str
    payload: dict[str, Any]
    timestamp: Optional[datetime] = None


# In-memory storage (replace with database in production)
REGISTERED_PROJECTS = {}
USAGE_LOGS = []


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "SBDK.dev Webhook Server",
        "status": "running",
        "version": "1.0.1",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "uptime": "running",
        "registered_projects": len(REGISTERED_PROJECTS),
        "usage_events": len(USAGE_LOGS),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/register")
async def register_project(registration: ProjectRegistration):
    """Register a new project and get tracking UUID"""
    project_uuid = str(uuid.uuid4())

    REGISTERED_PROJECTS[project_uuid] = {
        "uuid": project_uuid,
        "project_name": registration.project_name,
        "email": registration.email,
        "metadata": registration.metadata or {},
        "created_at": datetime.utcnow().isoformat(),
        "last_seen": datetime.utcnow().isoformat(),
    }

    return {
        "uuid": project_uuid,
        "project_name": registration.project_name,
        "status": "registered",
        "message": "Project registered successfully for tracking (optional)",
    }


@app.post("/track/usage")
async def track_usage(usage: UsageTracking):
    """Track CLI usage (opt-in telemetry)"""
    if usage.project_uuid not in REGISTERED_PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update last seen
    REGISTERED_PROJECTS[usage.project_uuid]["last_seen"] = datetime.utcnow().isoformat()

    # Log usage event
    usage_event = {
        "id": str(uuid.uuid4()),
        "project_uuid": usage.project_uuid,
        "command": usage.command,
        "duration_seconds": usage.duration_seconds,
        "metadata": usage.metadata or {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    USAGE_LOGS.append(usage_event)

    return {
        "status": "tracked",
        "event_id": usage_event["id"],
        "message": "Usage tracked successfully",
    }


@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    try:
        payload = await request.json()
        headers = dict(request.headers)

        # Get event type from headers
        event_type = headers.get("x-github-event", "unknown")

        # Log the webhook event
        webhook_event = {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "payload": payload,
            "headers": {k: v for k, v in headers.items() if k.startswith("x-github")},
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Handle push events to main branch
        if event_type == "push" and payload.get("ref") == "refs/heads/main":
            background_tasks.add_task(handle_main_branch_push, payload)

        # Handle pull request events
        elif event_type == "pull_request":
            background_tasks.add_task(handle_pull_request, payload)

        return {
            "status": "received",
            "event_type": event_type,
            "event_id": webhook_event["id"],
            "message": f"Webhook {event_type} event processed",
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid webhook payload: {str(e)}"
        ) from e


async def handle_main_branch_push(payload: dict[str, Any]):
    """Handle push to main branch - trigger rebuild"""
    try:
        repo_name = payload.get("repository", {}).get("name", "unknown")
        commit_sha = payload.get("head_commit", {}).get("id", "unknown")

        print(
            f"🔄 Main branch push detected for {repo_name} (commit: {commit_sha[:8]})"
        )

        # Check if we're in a SBDK project directory
        if Path("sbdk_config.json").exists():
            print("📦 Running SBDK development pipeline...")

            # Run the development pipeline
            result = await run_async_command([sys.executable, "-m", "main", "dev"])

            if result.returncode == 0:
                print("✅ Pipeline rebuild completed successfully")
            else:
                print(f"❌ Pipeline rebuild failed: {result.stderr}")
        else:
            print("⚠️  Not in a SBDK project directory, skipping pipeline run")

    except Exception as e:
        print(f"❌ Error handling main branch push: {e}")


async def handle_pull_request(payload: dict[str, Any]):
    """Handle pull request events"""
    try:
        action = payload.get("action", "unknown")
        pr_number = payload.get("number", 0)
        repo_name = payload.get("repository", {}).get("name", "unknown")

        print(f"🔀 Pull request {action} for {repo_name} #{pr_number}")

        # For opened/synchronize, we might want to run tests
        if action in ["opened", "synchronize"]:
            print("🧪 Running tests for pull request...")

            # Could trigger test runs here
            # await run_async_command(["python", "-m", "pytest", "tests/"])

    except Exception as e:
        print(f"❌ Error handling pull request: {e}")


async def run_async_command(command: list) -> subprocess.CompletedProcess:
    """Run a command asynchronously"""
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    return subprocess.CompletedProcess(
        args=command,
        returncode=process.returncode,
        stdout=stdout.decode() if stdout else "",
        stderr=stderr.decode() if stderr else "",
    )


@app.get("/projects")
async def list_projects():
    """List registered projects (for debugging)"""
    return {
        "projects": list(REGISTERED_PROJECTS.values()),
        "total": len(REGISTERED_PROJECTS),
    }


@app.get("/usage/{project_uuid}")
async def get_project_usage(project_uuid: str):
    """Get usage statistics for a project"""
    if project_uuid not in REGISTERED_PROJECTS:
        raise HTTPException(status_code=404, detail="Project not found")

    project_logs = [log for log in USAGE_LOGS if log["project_uuid"] == project_uuid]

    return {
        "project": REGISTERED_PROJECTS[project_uuid],
        "usage_events": project_logs,
        "total_events": len(project_logs),
    }


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.getenv("SBDK_WEBHOOK_PORT", "8000"))
    host = os.getenv("SBDK_WEBHOOK_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
