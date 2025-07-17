# app/main.py
# app/main.py

from agents.salesforce_data_agent import sf_agent

print("Salesforce CLI Copilot is live! Ask about Cases, Accounts, Leads, Contacts...\n")

while True:
    user_input = input("Ask a question (or type 'exit'): ")
    if user_input.lower() == "exit":
        print("Exiting.")
        break

    try:
        response = sf_agent.invoke({"input": user_input})
        print("\nResults:\n" + response["output"])
    except Exception as e:
        print(f"Error: {str(e)}")

