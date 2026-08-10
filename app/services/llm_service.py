import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Inisialisasi Gemini API
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite", 
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0 # Temperature 0 agar hasilnya konsisten/tidak halusinasi
)