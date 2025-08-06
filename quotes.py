import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

load_dotenv()

USED_QUOTES_FILE = "used_quotes.txt"

def load_used_quotes():
    if not os.path.exists(USED_QUOTES_FILE):
        return set()
    with open(USED_QUOTES_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_quote(quote):
    with open(USED_QUOTES_FILE, "a", encoding="utf-8") as f:
        f.write(quote + "\n")

def get_ai_quote(character="Jaxim", max_attempts=5):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel(
        "models/gemini-1.5-flash",
        generation_config=GenerationConfig(
            temperature=0.9,
            top_k=40,
            top_p=0.95,
        )
    )

    used_quotes = load_used_quotes()

    for attempt in range(max_attempts):
        prompt = f"Give me a two sentence, magical motivational quote from a genie named {character}. Only reply with one unique line."
        response = model.generate_content(prompt)

        quote = next((line.strip() for line in response.text.strip().splitlines() if line.strip()), None)

        if quote and quote not in used_quotes:
            save_quote(quote)
            return quote

    return "✨ All possible quotes are exhausted for now. Try again later!"


if __name__ == "__main__":
    quote = get_ai_quote()
    print("Generated quote:", quote)
