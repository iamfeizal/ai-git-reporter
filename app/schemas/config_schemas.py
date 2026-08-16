from pydantic import BaseModel
from typing import Optional

class LLMConfigBase(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = False

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigResponse(LLMConfigBase):
    id: int
    class Config:
        from_attributes = True

class GitLabInstanceBase(BaseModel):
    name: str
    gitlab_url: str
    token: str

class GitLabInstanceCreate(GitLabInstanceBase):
    pass

class GitLabInstanceResponse(GitLabInstanceBase):
    id: int
    class Config:
        from_attributes = True

class GenerateReportRequest(BaseModel):
    instance_id: int
    project_id: str
    start_date: str
    end_date: str
    target_doc_id: str
