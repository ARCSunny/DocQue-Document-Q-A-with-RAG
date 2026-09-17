import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").strip().lower()

def get_llm_client():
    if LLM_PROVIDER == "gemini":
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key.startswith("..."):
            raise ValueError("GEMINI_API_KEY is not properly set in your .env or Streamlit secrets.")
        genai.configure(api_key=api_key)
        return genai

    elif LLM_PROVIDER == "ollama":
        import ollama
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return ollama.Client(host=host)

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: '{LLM_PROVIDER}'. Choose from 'gemini' or 'ollama'.")

# Client instance ready to be imported across your project
client = get_llm_client()


def complete(prompt: str, model: str = None, system: str = None, max_tokens: int = 1024, temperature: float = 0.1) -> str:
    if LLM_PROVIDER == "gemini":
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        gemini_model = client.GenerativeModel(model_name, system_instruction=system)
        response = gemini_model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": temperature}
        )
        return response.text
        
    elif LLM_PROVIDER == "ollama":
        model_name = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat(
            model=model_name, 
            messages=messages,
            options={"temperature": temperature}
        )
        return response['message']['content']
        
    else:
        raise ValueError(f"Provider {LLM_PROVIDER} does not support complete()")


def describe_image(image_path: str, model: str = None, prompt: str = "Describe this image.") -> str:
    if LLM_PROVIDER == "gemini":
        import PIL.Image
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        img = PIL.Image.open(image_path)
        gemini_model = client.GenerativeModel(model_name)
        response = gemini_model.generate_content([img, prompt])
        return response.text

    elif LLM_PROVIDER == "ollama":
        vision_model = model or os.getenv("OLLAMA_VISION_MODEL", "llava")
        response = client.chat(
            model=vision_model,
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [image_path]
            }]
        )
        return response['message']['content']

    else:
        raise ValueError(f"Provider {LLM_PROVIDER} does not support describe_image()")