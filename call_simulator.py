from llm_client import chat
from prompts import build_agent_system_prompt


def run_simulated_call(lead: dict, knowledge_base: str) -> str:
    """Runs an interactive text-based call. Returns the full transcript as a string.
    Type 'hangup' as the lead to end the call at any point."""
    system_prompt = build_agent_system_prompt(
        lead_name=lead["Name"], company=lead["Company"], knowledge_base=knowledge_base
    )
    messages = [{"role": "system", "content": system_prompt}]
    transcript_lines = []

    print(f"\n--- Simulated call with {lead['Name']} ({lead['Company']}) ---")
    print("(You are playing the lead. Type 'hangup' to end the call.)\n")

    # Agent opens the call
    opening = chat(messages + [{"role": "user", "content": "[Call connected. Begin the call.]"}])
    messages.append({"role": "assistant", "content": opening})
    print(f"Agent: {opening}\n")
    transcript_lines.append(f"Agent: {opening}")

    while True:
        lead_input = input("You (as lead): ").strip()
        if not lead_input:
            continue
        transcript_lines.append(f"Lead: {lead_input}")
        if lead_input.lower() in ("hangup", "/hangup"):
            transcript_lines.append("[Call ended by lead]")
            break

        messages.append({"role": "user", "content": lead_input})
        reply = chat(messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"\nAgent: {reply}\n")
        transcript_lines.append(f"Agent: {reply}")

        if any(p in reply.lower() for p in ["have a great day", "thanks again for your time", "goodbye"]):
            break

    return "\n".join(transcript_lines)
