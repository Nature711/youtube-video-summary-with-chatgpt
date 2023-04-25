import os
import openai
import sqlite3
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ['OPENAI_API_KEY']

def split_string_into_chunks(text, K):
    words = text.split()
    chunks = []
    current_chunk = ""
    for word in words:
        if len(current_chunk.split()) + len(word.split()) <= K:
            current_chunk += " " + word
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word
    if len(current_chunk.split()) > 0:
        chunks.append(current_chunk.strip())
    return chunks

def generate_summary(transcript):

    if (transcript is None): return "No summary available"

    # Summarize the transcript using OpenAI's GPT-3 API
    max_chunk_size = 3500
    transcript_chunks = split_string_into_chunks(transcript, max_chunk_size)
    summary = ''
    for i in range(len(transcript_chunks)): 
        text = summary + transcript_chunks[i]
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

    final_summary = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Please summarize the following text:\n{summary}",
            temperature=0.5,
            max_tokens=200,
            n = 1,
            stop=None,
            timeout=60,
        ).choices[0].text

    return final_summary
    

