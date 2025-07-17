#app/mistral_utils.py

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

llm = ChatOllama(model="mistral")

prompt = PromptTemplate.from_template("""
You are a Salesforce assistant. Given a user question, extract:
1. The Salesforce object (Case, Account, Contact, Lead)
2. A valid SOQL WHERE clause (exclude SELECT, LIMIT)
3. Optional fields to return (e.g., Name, CreatedDate)

Important:
- If the query involves related objects (e.g., Contacts associated with Prospect Accounts), use a subquery format:
  Example: AccountId IN (SELECT Id FROM Account WHERE Type = 'Prospect')

Reply only in this format:
object: <SalesforceObject>
where: <SOQL WHERE clause>
fields: <comma-separated fields or 'FIELDS(ALL)'>

Q: Find all contacts associated with prospect accounts
A:
object: Contact
where: AccountId IN (SELECT Id FROM Account WHERE Type = 'Prospect')
fields: FirstName, LastName, Email, AccountId

Q: {user_input}
A:
""")

extractor_chain = LLMChain(llm=llm, prompt=prompt)

def extract_soql_components(user_input: str) -> dict:
    output = extractor_chain.run(user_input)
    result = {}
    for line in output.splitlines():
        if "object:" in line:
            result["object_name"] = line.split("object:")[1].strip()
        elif "where:" in line:
            result["where_clause"] = line.split("where:")[1].strip()
        elif "fields:" in line:
            result["fields"] = line.split("fields:")[1].strip()
    return result

