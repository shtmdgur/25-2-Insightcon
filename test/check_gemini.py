
import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.config.llm_config import get_flash_model

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API Key found")
    exit(1)

genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")

print(f"Testing generation with {get_flash_model()}...")
try:
    model = genai.GenerativeModel(get_flash_model())
    response = model.generate_content("Hello")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error with {get_flash_model()}: {e}")
