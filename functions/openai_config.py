"""
File: openai_config.py
Description: Load OpenAI API key from .env file.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def load_openai_client():
    """
    Load OpenAI API client from environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY in environment variables")
    return OpenAI(api_key=api_key)

client = load_openai_client()
