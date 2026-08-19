import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.core.database import SessionLocal
from app.models.config_models import LLMConfig

def get_llm():
    db = SessionLocal()
    try:
        config = db.query(LLMConfig).filter(LLMConfig.is_active == True).first()
        if not config:
            # Fallback to env or raise
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                return ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", api_key=gemini_key, temperature=0)
            raise Exception("Tidak ada konfigurasi LLM yang aktif di database!")

        if config.provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=config.model_name, 
                api_key=config.api_key,
                temperature=0,
                max_retries=3
            )
        elif config.provider == "openai" or config.provider == "custom":
            # ChatOpenAI can be used for OpenAI or any OpenAI-compatible API (like Ollama, vLLM, LMStudio)
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key or "empty",
                base_url=config.base_url,
                temperature=0,
                max_retries=3
            )
        elif config.provider == "anthropic":
            return ChatAnthropic(
                model_name=config.model_name,
                api_key=config.api_key,
                temperature=0,
                max_retries=3
            )
        else:
            raise Exception(f"Provider LLM tidak didukung: {config.provider}")
    finally:
        db.close()

def test_llm_connection(provider: str, model_name: str, api_key: str, base_url: str):
    try:
        if provider == "gemini":
            llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key, temperature=0)
        elif provider == "openai" or provider == "custom":
            llm = ChatOpenAI(model=model_name, api_key=api_key or "empty", base_url=base_url, temperature=0)
        elif provider == "anthropic":
            llm = ChatAnthropic(model_name=model_name, api_key=api_key, temperature=0)
        else:
            return False, f"Provider LLM tidak didukung: {provider}"
        
        # Test connection with a simple prompt
        res = llm.invoke("Hi")
        return True, "Success"
    except Exception as e:
        return False, str(e)