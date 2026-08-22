from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
from typing import List

from app.core.database import get_db
from app.models.config_models import LLMConfig, GitLabInstance
from app.schemas.config_schemas import (
    LLMConfigCreate, LLMConfigResponse, 
    GitLabInstanceCreate, GitLabInstanceResponse
)
from app.services.llm_service import test_llm_connection

router = APIRouter(prefix="/api/config", tags=["Configuration"])

# --- LLM Config ---
@router.get("/llm", response_model=List[LLMConfigResponse])
def get_llm_configs(db: Session = Depends(get_db)):
    return db.query(LLMConfig).all()

@router.post("/llm", response_model=LLMConfigResponse)
def create_llm_config(config: LLMConfigCreate, db: Session = Depends(get_db)):
    if config.is_active:
        # deactivate others
        db.query(LLMConfig).update({"is_active": False})
    
    db_config = LLMConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.post("/llm/test")
def test_llm_config_endpoint(config: LLMConfigCreate):
    success, message = test_llm_connection(
        provider=config.provider,
        model_name=config.model_name,
        api_key=config.api_key or "",
        base_url=config.base_url or ""
    )
    if success:
        return {"status": "success", "message": message}
    else:
        raise HTTPException(status_code=400, detail=message)

@router.put("/llm/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(config_id: int, config_data: LLMConfigCreate, db: Session = Depends(get_db)):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    config.provider = config_data.provider
    config.model_name = config_data.model_name
    config.api_key = config_data.api_key
    config.base_url = config_data.base_url
    
    db.commit()
    db.refresh(config)
    return config

@router.put("/llm/{config_id}/activate")
def activate_llm_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    db.query(LLMConfig).update({"is_active": False})
    config.is_active = True
    db.commit()
    return {"status": "success"}

@router.delete("/llm/{config_id}")
def delete_llm_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    db.delete(config)
    db.commit()
    return {"status": "success"}


# --- GitLab Instance ---
@router.get("/gitlab", response_model=List[GitLabInstanceResponse])
def get_gitlab_instances(db: Session = Depends(get_db)):
    return db.query(GitLabInstance).all()

@router.post("/gitlab", response_model=GitLabInstanceResponse)
def create_gitlab_instance(instance: GitLabInstanceCreate, db: Session = Depends(get_db)):
    db_instance = GitLabInstance(**instance.model_dump())
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

@router.delete("/gitlab/{instance_id}")
def delete_gitlab_instance(instance_id: int, db: Session = Depends(get_db)):
    instance = db.query(GitLabInstance).filter(GitLabInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    db.delete(instance)
    db.commit()
    return {"status": "success"}

@router.get("/gitlab/{instance_id}/projects")
def get_gitlab_projects(instance_id: int, db: Session = Depends(get_db)):
    instance = db.query(GitLabInstance).filter(GitLabInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="GitLab instance not found")
    
    url = f"{instance.gitlab_url}/api/v4/projects"
    headers = {"PRIVATE-TOKEN": instance.token}
    params = {"membership": "true", "per_page": 100, "simple": "true"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch projects: {str(e)}")

# --- API Status ---
@router.get("/status")
def get_api_status(instance_id: int = None, db: Session = Depends(get_db)):
    """Check the health of all external APIs."""
    status = {
        "gemini": False,
        "gdocs": False,
        "drive": False,
        "gitlab": False
    }

    # 1. Test Gemini
    active_llm = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
    if active_llm:
        success, _ = test_llm_connection(
            provider=active_llm.provider,
            model_name=active_llm.model_name,
            api_key=active_llm.api_key or "",
            base_url=active_llm.base_url or ""
        )
        status["gemini"] = success

    # 2. Test GDocs & Drive
    try:
        from app.services.gdocs_service import GDocsService
        gdocs = GDocsService()
        if gdocs.docs_service:
            status["gdocs"] = True
        if gdocs.drive_service:
            status["drive"] = True
    except Exception:
        pass

    # 3. Test GitLab
    if instance_id:
        instance = db.query(GitLabInstance).filter(GitLabInstance.id == instance_id).first()
        if instance:
            url = f"{instance.gitlab_url}/api/v4/version"
            headers = {"PRIVATE-TOKEN": instance.token}
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    status["gitlab"] = True
            except Exception:
                pass

    return status
