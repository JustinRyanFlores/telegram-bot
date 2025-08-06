import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def get_ai_quote(character="Jeanie"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # ✅ Use one of the working models
    model = genai.GenerativeModel("models/gemini-1.5-flash")

    prompt = f"Give me a short, magical motivational quote from a genie named {character}."
    response = model.generate_content(prompt)
    return response.text.strip()

if __name__ == "__main__":
    quote = get_ai_quote()
    print("Generated quote:", quote)
