# utils/gemini_client.py

import google.generativeai as genai
from PIL import Image

# Load your key from env/secure storage
genai.configure(api_key="AIzaSyAe8rheF4wv2ZHJB2YboUhyyVlM2y0vmlk")  # You can switch this to use os.environ

# Initialize models
text_model = genai.GenerativeModel("gemini-2.0-flash")
vision_model = genai.GenerativeModel("gemini-2.0-flash-001")

# --- Text prompt only ---
def gemini_chat(prompt: str) -> str:
    try:
        response = text_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Text Error: {e}"

# --- Text + Image (Vision) ---
def gemini_vision_chat(prompt: str, image: Image.Image) -> str:
    try:
        response = vision_model.generate_content([
            prompt,
            image
        ])
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini Vision Error: {e}"