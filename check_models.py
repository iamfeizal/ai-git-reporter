import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Ambil API Key dari .env
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API Key tidak ditemukan! Pastikan GEMINI_API_KEY ada di .env")
    exit()

# Konfigurasi library
genai.configure(api_key=api_key)

print("Mencari model Gemini yang tersedia untuk API Key Anda...\n")

# Looping untuk mencari model yang mendukung 'generateContent'
try:
    available_models = []
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            available_models.append(m.name)
            print(f"- {m.name}")
            
    print("\n✅ SELESAI! Silakan pilih salah satu model berawalan 'models/gemini...' di atas.")
except Exception as e:
    print(f"Gagal mengakses API Google: {e}")