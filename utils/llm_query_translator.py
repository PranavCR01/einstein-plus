# utils/llm_query_translator.py

from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="mistral")

prompt_template = PromptTemplate(
    input_variables=["query"],
    template="""
You are a Salesforce assistant. Based on the user's natural language input, extract:
1. The Salesforce object they are referring to (must be one of: Case, Account, Contact, Lead)
2. A valid SOQL WHERE clause (exclude SELECT, LIMIT)

Important:
- If referring to relationships (e.g., Contacts from Prospect Accounts), use a subquery:
  Example: AccountId IN (SELECT Id FROM Account WHERE Type = 'Prospect')

Q: Show me all open cases with high priority
A:
Object: Case
Where: Status != 'Closed' AND Priority = 'High'

Q: Find contacts in California
A:
Object: Contact
Where: MailingState = 'California'

Q: {query}
A:"""
)

def translate_query(natural_language_query: str) -> dict:
    prompt = prompt_template.format(query=natural_language_query)
    output = llm.invoke(prompt).content.strip()

    try:
        lines = output.splitlines()
        object_name = next(l for l in lines if l.lower().startswith("object")).split(":")[1].strip()
        where_clause = next(l for l in lines if l.lower().startswith("where")).split(":")[1].strip()
        return {"object_name": object_name, "where_clause": where_clause}
    except Exception:
        raise ValueError("❌ Failed to parse LLM output.")

