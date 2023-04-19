import os
import openai
import sqlite3
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ['OPENAI_API_KEY']

def generate_summary(transcript):
    # Summarize the transcript using OpenAI's GPT-3 API
    max_token_limit = 2000
    chunk_size = max_token_limit - 200
    transcript_chunks = [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]
    summary = ''
    prev_summary = ''
    for i, chunk in enumerate(transcript_chunks):
        text = prev_summary + chunk
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Please summarize the following text:\n{text}",
            temperature=0.5,
            max_tokens=200,
            n = 1,
            stop=None,
            timeout=60,
        )
        summary += response.choices[0].text
        prev_summary = summary

    return summary

