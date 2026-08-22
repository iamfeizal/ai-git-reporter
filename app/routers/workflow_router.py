"""
Workflow Router — API endpoints for managing the LangGraph pipeline.

Endpoints:
  POST /api/workflow/start       — Start a new report pipeline (returns thread_id)
  GET  /api/workflow/{id}/status — Check pipeline status (which node, is paused)
  GET  /api/workflow/{id}/state  — Get current graph state (for HITL review)
  POST /api/workflow/{id}/resume — Resume from HITL interrupt with user corrections
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command

from app.core.database import get_db, DATABASE_URL
from app.core.state import NormalizedCommit
from app.core.workflow import compile_workflow
from app.models.config_models import GitLabInstance
from app.services.gitlab_service import GitLabService

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])

gitlab_service = GitLabService()

# --- PostgresSaver singleton ---
_pool: Optional[ConnectionPool] = None
_checkpointer: Optional[PostgresSaver] = None
_compiled_workflow = None


def get_checkpointer():
    """Get or create the PostgresSaver checkpointer (singleton)."""
    global _pool, _checkpointer, _compiled_workflow

    if _checkpointer is None:
        db_url = DATABASE_URL
        if not db_url or db_url.startswith("sqlite"):
            raise HTTPException(
                status_code=500,
                detail="PostgreSQL DATABASE_URL diperlukan untuk workflow HITL. SQLite tidak didukung."
            )
        # Convert SQLAlchemy URL to psycopg format if needed
        # psycopg uses postgresql:// (not postgresql+psycopg2://)
        conninfo = db_url.replace("postgresql+psycopg2://", "postgresql://")

        _pool = ConnectionPool(conninfo=conninfo, kwargs={"autocommit": True})
        _checkpointer = PostgresSaver(_pool)
        _checkpointer.setup()
        _compiled_workflow = compile_workflow(checkpointer=_checkpointer)

    return _checkpointer, _compiled_workflow


# --- Request/Response Schemas ---
class StartWorkflowRequest(BaseModel):
    instance_id: int
    project_id: str
    start_date: str
    end_date: str
    month_year: str = ""  # e.g., "Agustus 2026"
    gdocs_mode: str = "direct"
    gdocs_document_id: str = ""


class ResumeWorkflowRequest(BaseModel):
    """User corrections for HITL resume."""
    corrected_commits: Optional[list] = None    # For HITL-1
    corrected_clusters: Optional[list] = None   # For HITL-2


# --- Endpoints ---

@router.post("/start")
def start_workflow(req: StartWorkflowRequest, db: Session = Depends(get_db)):
    """
    Start a new report generation pipeline.
    
    Returns a thread_id that can be used to track progress and resume from HITL pauses.
    """
    # Validate GitLab instance
    instance = db.query(GitLabInstance).filter(GitLabInstance.id == req.instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="GitLab instance not found")

    # Fetch and normalize commits
    try:
        normalized_commits = gitlab_service.get_normalized_commits(
            url=instance.gitlab_url,
            token=instance.token,
            project_id=req.project_id,
            start_date=req.start_date,
            end_date=req.end_date,
            filter_noise=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GitLab fetch error: {str(e)}")

    if not normalized_commits:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada commit ditemukan setelah filtering pada rentang tanggal tersebut."
        )

    # Generate thread ID
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state
    initial_state = {
        "month_year": req.month_year or "",
        "gdocs_mode": req.gdocs_mode,
        "gdocs_document_id": req.gdocs_document_id,
        "raw_commits": normalized_commits,
        "classified_commits": [],
        "hitl_1_approved": False,
        "l2_classified": [],
        "clusters": [],
        "hitl_2_approved": False,
        "executive_summary": "",
        "final_clusters": [],
        "document_url": "",
    }

    # Get checkpointer and compiled workflow
    _, workflow = get_checkpointer()

    # Run the graph — it will pause at the first HITL interrupt
    try:
        result = workflow.invoke(initial_state, config=config)
    except Exception as e:
        # Graph pausing via interrupt is normal — it raises an interrupt
        # Actually, with invoke(), the interrupt returns the state up to that point
        pass

    return {
        "status": "started",
        "thread_id": thread_id,
        "total_commits": len(normalized_commits),
        "message": f"Pipeline dimulai dengan {len(normalized_commits)} commit. Cek status untuk review.",
    }


@router.get("/{thread_id}/status")
def get_workflow_status(thread_id: str):
    """
    Check the current status of a workflow thread.
    
    Returns which node the graph is at, whether it's paused for HITL, etc.
    """
    checkpointer, workflow = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = workflow.get_state(config)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread not found: {str(e)}")

    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Determine status
    next_nodes = state.next if state.next else []
    is_paused = len(next_nodes) > 0
    
    # Check if there are pending interrupts
    has_interrupt = False
    interrupt_data = None
    if state.tasks:
        for task in state.tasks:
            if hasattr(task, 'interrupts') and task.interrupts:
                has_interrupt = True
                interrupt_data = task.interrupts[0].value if task.interrupts else None
                break

    return {
        "thread_id": thread_id,
        "status": "paused" if is_paused else "completed",
        "next_nodes": list(next_nodes),
        "is_paused": is_paused,
        "has_interrupt": has_interrupt,
        "interrupt_data": interrupt_data,
    }


@router.get("/{thread_id}/state")
def get_workflow_state(thread_id: str):
    """
    Get the full current state of a workflow thread.
    Used by the frontend to display HITL review data.
    """
    checkpointer, workflow = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state_snapshot = workflow.get_state(config)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Thread not found: {str(e)}")

    if state_snapshot is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    values = state_snapshot.values
    next_nodes = list(state_snapshot.next) if state_snapshot.next else []

    # Serialize state values (Pydantic models → dicts)
    serialized = {}
    for key, val in values.items():
        if isinstance(val, list) and val and hasattr(val[0], 'model_dump'):
            serialized[key] = [item.model_dump() for item in val]
        elif hasattr(val, 'model_dump'):
            serialized[key] = val.model_dump()
        else:
            serialized[key] = val

    # Check for interrupt data
    interrupt_data = None
    if state_snapshot.tasks:
        for task in state_snapshot.tasks:
            if hasattr(task, 'interrupts') and task.interrupts:
                interrupt_data = task.interrupts[0].value if task.interrupts else None
                break

    return {
        "thread_id": thread_id,
        "next_nodes": next_nodes,
        "is_paused": len(next_nodes) > 0,
        "interrupt_data": interrupt_data,
        "state": serialized,
    }


@router.post("/{thread_id}/resume")
def resume_workflow(thread_id: str, req: ResumeWorkflowRequest):
    """
    Resume a paused workflow with user corrections.
    
    For HITL-1: send corrected_commits (re-classified L1 categories)
    For HITL-2: send corrected_clusters (renamed/merged/split clusters)
    
    If no corrections provided, the graph resumes with the existing state (approved as-is).
    """
    _, workflow = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}

    # Build the resume payload
    resume_data = {}
    if req.corrected_commits is not None:
        resume_data["corrected_commits"] = req.corrected_commits
    if req.corrected_clusters is not None:
        resume_data["corrected_clusters"] = req.corrected_clusters

    # Resume with Command
    try:
        result = workflow.invoke(
            Command(resume=resume_data if resume_data else "approved"),
            config=config
        )
    except Exception as e:
        # May pause at the next HITL interrupt — that's normal
        pass

    # Check the new status after resume
    try:
        state = workflow.get_state(config)
        next_nodes = list(state.next) if state.next else []
        is_completed = len(next_nodes) == 0

        # If completed, extract final results
        if is_completed and state.values:
            final_clusters = state.values.get("final_clusters", [])
            executive_summary = state.values.get("executive_summary", "")
            document_url = state.values.get("document_url", "")
            return {
                "status": "completed",
                "thread_id": thread_id,
                "message": "Pipeline selesai!",
                "total_clusters": len(final_clusters) if isinstance(final_clusters, list) else 0,
                "executive_summary": executive_summary,
                "document_url": document_url,
            }
        
        # Check for new interrupt
        interrupt_data = None
        if state.tasks:
            for task in state.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    interrupt_data = task.interrupts[0].value if task.interrupts else None
                    break

        return {
            "status": "paused",
            "thread_id": thread_id,
            "next_nodes": next_nodes,
            "interrupt_data": interrupt_data,
            "message": "Pipeline dilanjutkan dan berhenti di checkpoint berikutnya.",
        }
    except Exception:
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "message": "Pipeline dilanjutkan.",
        }
