import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def query_openai(prompt, temperature=0.7, max_tokens=1024):
    """
    Sends a query to OpenAI and returns the response.

    Parameters:
        prompt (str): The input text to OpenAI.
        temperature (float): Controls randomness in response generation.
        max_tokens (int): The maximum number of tokens in response.

    Returns:
        str: The OpenAI-generated response.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] OpenAI request failed: {e}")
        return "Error: OpenAI request failed."

