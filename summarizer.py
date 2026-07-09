import json
from llm_client import chat
from prompts import SUMMARIZER_SYSTEM_PROMPT, build_summarizer_user_prompt


def summarize_call(transcript: str) -> dict:
    if not transcript.strip():
        return {
            "call_status": "No Answer",
            "lead_qualification": "Unclear",
            "conversation_summary": "",
            "customer_requirements": "",
            "objections_raised": "",
            "follow_up_date": "",
            "meeting_datetime": "",
        }

    messages = [
        {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
        {"role": "user", "content": build_summarizer_user_prompt(transcript)},
    ]
    raw = chat(messages, json_mode=True)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "call_status": "Completed",
            "lead_qualification": "Unclear",
            "conversation_summary": "Could not auto-parse summary. Raw: " + raw[:300],
            "customer_requirements": "",
            "objections_raised": "",
            "follow_up_date": "",
            "meeting_datetime": "",
        }
