import subprocess

def get_ai_quote(character="Jaxim"):
    prompt = f"You are {character}, a friendly and wise Genie. Give me a short motivational quote."

    # Run Ollama locally with the Mistral model
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Decode and return the model's response
    response = result.stdout.decode().strip()
    return response

# Example usage
if __name__ == "__main__":
    print(get_ai_quote())
