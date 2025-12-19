from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

print(f"Checking Neo4j Connection...")
print(f"URI: {uri}")
print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'None'}")

if not all([uri, username, password]):
    print("❌ Missing credentials in .env file")
else:
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("✅ Connection Successful!")
        driver.close()
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
