#connectors/ salesforce_connector.py

import os
from dotenv import load_dotenv
from simple_salesforce import Salesforce

# Load environment variables
load_dotenv()

def get_salesforce_connection():
    sf = Salesforce(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_SECURITY_TOKEN"),
        domain=os.getenv("SF_DOMAIN")
    )
    return sf
