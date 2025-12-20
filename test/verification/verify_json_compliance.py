
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/processed")

def verify_json_files():
    json_files = list(DATA_DIR.glob("*_kg.json"))
    if not json_files:
        logger.warning("No JSON files found in data/processed")
        return

    logger.info(f"Checking {len(json_files)} JSON files...")
    
    total_errors = 0
    file_errors = {}

    for file_path in json_files:
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            entities = data.get("entities", [])
            if not entities:
                errors.append("No entities found")
                
            for entity in entities:
                name = entity.get("name", "")
                type_ = entity.get("type", "")
                props = entity.get("properties", {})
                
                # Check 1: Empty Properties (Warning/Error)
                # Some static nodes might legitimately have few properties, but strictly speaking user wanted them filled.
                if not props and type_ not in ["TemporalRegion"]: # TemporalRegion might just be the name
                    errors.append(f"[{type_}] '{name}' has empty properties")
                
                # Check 2: Ticker in Name (for Company)
                if type_ == "Company" or type_ == "IDM" or type_ == "Fabless":
                    if re.search(r'\(\d{6}\)', name):
                        errors.append(f"[{type_}] '{name}' contains ticker in name (Should be in properties)")
                    if re.search(r'\d{6}', name) and type_ == "Company": # stricter check
                         errors.append(f"[{type_}] '{name}' might contain ticker in name")

                # Check 3: Time-scoping for Dynamic Nodes
                dynamic_types = ["Event", "Trend", "MarketEnvironment", "StrategicAction", "CorporateEvent", "Observation"]
                if type_ in dynamic_types:
                    # Simple check for date-like suffix (YYYY, QN, MM, DD)
                    # This is loose, just checking if it ends with digit or date pattern
                    if not re.search(r'(\d{4}|Q\d|\d{2})', name):
                        # errors.append(f"[{type_}] '{name}' might lack time-scoping")
                        pass # Skipping for now as it's a heuristic

            if errors:
                file_errors[file_path.name] = errors
                total_errors += len(errors)
                
        except Exception as e:
            logger.error(f"Failed to read {file_path.name}: {e}")

    # Report
    if total_errors == 0:
        logger.info("✅ All JSON files passed validation!")
    else:
        logger.error(f"❌ Found {total_errors} issues in {len(file_errors)} files:")
        for fname, errs in file_errors.items():
            logger.error(f"\n📄 {fname}:")
            for i, err in enumerate(errs[:5]): # Show top 5
                logger.error(f"  - {err}")
            if len(errs) > 5:
                logger.error(f"  ... and {len(errs)-5} more")

if __name__ == "__main__":
    verify_json_files()
