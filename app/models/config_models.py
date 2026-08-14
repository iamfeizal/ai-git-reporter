from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="gemini") # "gemini", "openai", "anthropic", "custom"
    model_name = Column(String, default="gemini-3.5-flash-lite")
    api_key = Column(String, nullable=True)
    base_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)

class GitLabInstance(Base):
    __tablename__ = "gitlab_instances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    gitlab_url = Column(String)
    token = Column(String)
