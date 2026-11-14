"""
MotherlyPulse Interactive Testing CLI
Allows immediate interactive testing of the MotherlyPulse Assistant:
- Submit messages
- See urgency category (EMERGENCY / PRIORITY / ROUTINE)
- See whether medication safety was triggered
- See triage action and structured response
"""

import sys
from .assistant import MotherlyPulseAssistant

def run_cli():
    assistant = MotherlyPulseAssistant()
    print("=" * 65)
    print("MOTHERLYPULSE MATERNAL & INFANT HEALTH ASSISTANT — LOCAL CLI")
    print("Type a health inquiry and press Enter.")
    print("Type 'exit' or 'quit' to terminate.")
    print("=" * 65)

    history = []
    while True:
        try:
            user_input = input("\nUser > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting MotherlyPulse CLI. Goodbye!")
                break

            response = assistant.respond(user_input, conversation_history=history)
            history.append(user_input)

            cat = response["urgency_category"].upper()
            action = response["action"]
            med_flag = response.get("medication_safety_triggered", False)

            print("-" * 65)
            print(f"Urgency Category:   [{cat}]")
            print(f"Action:             {action}")
            print(f"Medication Safety:  {'TRIGGERED' if med_flag else 'None'}")
            print("-" * 65)
            print(f"Response:\n{response['response']}")
            print("-" * 65)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting MotherlyPulse CLI. Goodbye!")
            break

if __name__ == "__main__":
    run_cli()

