from excel_manager import get_next_pending_lead, update_lead_record
from call_simulator import run_simulated_call
from summarizer import summarize_call


def main():
    result = get_next_pending_lead()
    if result is None:
        print("No pending leads found. All leads are Completed or Opted-out.")
        return

    row, lead = result
    with open("data/knowledge_base.md") as f:
        knowledge_base = f.read()

    transcript = run_simulated_call(lead, knowledge_base)

    print("\n--- Call ended. Summarizing and updating CRM... ---\n")
    summary = summarize_call(transcript)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    update_lead_record(row, summary)
    print(f"\nLead '{lead['Name']}' updated in data/leads_crm.xlsx (row {row}).")


if __name__ == "__main__":
    main()
