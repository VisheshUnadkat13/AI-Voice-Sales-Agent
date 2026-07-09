import os
import json

PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "ollama"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def chat(messages: list[dict], json_mode: bool = False) -> str:
    """messages: list of {"role": "system"|"user"|"assistant", "content": str}"""
    if PROVIDER == "openai":
        return _chat_openai(messages, json_mode)
    elif PROVIDER == "ollama":
        return _chat_ollama(messages, json_mode)
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}")


def _chat_openai(messages, json_mode):
    from openai import OpenAI
    client = OpenAI()  # reads OPENAI_API_KEY from env
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.7,
        **kwargs,
    )
    return resp.choices[0].message.content


def _chat_ollama(messages, json_mode):
    import requests
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]
