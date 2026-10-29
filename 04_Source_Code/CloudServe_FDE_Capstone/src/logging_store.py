"""Append-only JSON Lines decision store."""
import json, os
from datetime import datetime, timezone
def append_decision(path, record):
    os.makedirs(os.path.dirname(os.path.abspath(path)),exist_ok=True)
    with open(path,"a",encoding="utf-8") as f:
        f.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+"\n")
