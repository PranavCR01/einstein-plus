# agents/salesforce_data_agent.py



from langchain_community.chat_models import ChatOllama
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from connectors.salesforce_connector import get_salesforce_connection
from app.mistral_utils import extract_soql_components
import json
import re

sf = get_salesforce_connection()
last_query_results = {}

def redact_sensitive_fields(record: dict) -> dict:
    sensitive_keys = {"SSN", "Password", "Email", "Phone"}
    return {
        k: ("[REDACTED]" if any(key in k for key in sensitive_keys) else v)
        for k, v in record.items()
    }

def query_salesforce_from_prompt(prompt: str) -> str:
    global last_query_results

    clean_input = prompt.strip("`").strip('"').strip("'")

    try:
        parts = {
            k.strip(): clean_part(v)
            for part in clean_input.split("|")
            for k, v in [part.split(":", 1)]
        }
        object_name = parts.get("object", "Case")
        where_clause = parts.get("where", "Status != 'Closed'")
        fields = parts.get("fields", "FIELDS(ALL)")
    except Exception as e:
        return f"❌ Error parsing input. Format: `object: ObjectName | where: condition | fields: field1, field2`. Error: {str(e)}"

    # Only try resolving subquery if 'IN (SELECT' is explicitly present
    if re.search(r'IN\s*\(\s*SELECT\s+', where_clause, re.IGNORECASE):
        try:
            subquery_match = re.search(r'IN\s*\(\s*SELECT\s+(.*?)\s+FROM\s+(\w+)\s+WHERE\s+(.*?)\)', where_clause, re.IGNORECASE)
            if subquery_match:
                select_field, sub_obj, sub_where = subquery_match.groups()
                subquery = f"SELECT {select_field.strip()} FROM {sub_obj.strip()} WHERE {sub_where.strip()} LIMIT 100"
                print("[DEBUG] Resolving subquery:", subquery)
                sub_result = sf.query(subquery)
                ids = [f"'{r[select_field.strip()]}'" for r in sub_result["records"] if select_field.strip() in r]
                if not ids:
                    return "⚠️ Subquery returned no matching records."
                where_clause = re.sub(r'IN\s*\(.*?\)', f"IN ({', '.join(ids)})", where_clause)
                print("[DEBUG] Updated where_clause:", where_clause)
        except Exception as e:
            return f"❌ Failed to resolve subquery: {str(e)}"

    query = f"SELECT {fields} FROM {object_name} WHERE {where_clause} LIMIT 5"
    print("[DEBUG] Final query:", query)

    try:
        results = sf.query(query)
        last_query_results = results
    except Exception as e:
        if "INVALID_FIELD" in str(e):
            try:
                fallback_query = f"SELECT Name FROM {object_name} WHERE {where_clause} LIMIT 5"
                fallback_results = sf.query(fallback_query)
                last_query_results = fallback_results
                redacted = [redact_sensitive_fields(r) for r in fallback_results["records"]]
                return f"⚠️ Invalid fields detected. Fallback query used:\n\n{json.dumps(redacted, indent=2)}"
            except Exception as fallback_e:
                return f"❌ Fallback also failed: {str(fallback_e)}"
        return f"❌ SOQL Query Failed: {str(e)}"

    redacted = [redact_sensitive_fields(r) for r in results["records"]]
    return f"🔍 Query executed successfully.\n\n{json.dumps(redacted, indent=2)}"

tools = [
    Tool(
        name="SalesforceQueryTool",
        func=query_salesforce_from_prompt,
        description=(
            "Use this to query Salesforce CRM data. You can ask questions like "
            "'Show me all open cases' or 'Find contacts from prospect accounts'."
        ),
        return_direct=True
    )
]

llm = ChatOllama(model="mistral")

sf_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=False
)

