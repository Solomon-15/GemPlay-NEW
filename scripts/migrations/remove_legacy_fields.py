#!/usr/bin/env python3
"""
One-time migration script to remove legacy fields from bots collection:
- win_percentage
- creation_mode
- profit_strategy

Usage:
  python scripts/migrations/remove_legacy_fields.py --dry-run
  python scripts/migrations/remove_legacy_fields.py --execute

Reads MongoDB URL and DB name from backend/.env (MONGO_URL, DB_NAME).
"""
import os
import sys
import argparse
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENV_PATH = os.path.join(ROOT_DIR, "backend", ".env")


def load_env():
    if os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH)
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME", "gemplay_db")
    if not mongo_url:
        print("ERROR: MONGO_URL is not set in backend/.env", file=sys.stderr)
        sys.exit(1)
    return mongo_url, db_name


def main():
    parser = argparse.ArgumentParser(description="Remove legacy fields from bots collection")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify data, only show what would change")
    parser.add_argument("--execute", action="store_true", help="Apply changes to the database")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Please specify either --dry-run or --execute")
        sys.exit(2)

    mongo_url, db_name = load_env()
    client = MongoClient(mongo_url)
    db = client[db_name]

    # Find documents containing any legacy fields
    query = {"$or": [
        {"win_percentage": {"$exists": True}},
        {"creation_mode": {"$exists": True}},
        {"profit_strategy": {"$exists": True}},
    ]}

    total_with_legacy = db.bots.count_documents(query)
    print(f"Found {total_with_legacy} bot documents containing legacy fields")

    if args.dry_run:
        # Show a small sample
        sample = list(db.bots.find(query, {"name": 1, "win_percentage": 1, "creation_mode": 1, "profit_strategy": 1}).limit(5))
        for doc in sample:
            print(f" - {doc.get('name', doc.get('id'))}: win_percentage={doc.get('win_percentage')}, creation_mode={doc.get('creation_mode')}, profit_strategy={doc.get('profit_strategy')}")
        print("DRY RUN complete. No changes applied.")
        return

    # Backup collection (simple copy)
    backup_name = f"bots_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup collection: {backup_name}")
    db[backup_name].insert_many(list(db.bots.find({})))

    # Unset legacy fields
    print("Removing legacy fields win_percentage, creation_mode, profit_strategy ...")
    result = db.bots.update_many(query, {"$unset": {
        "win_percentage": "",
        "creation_mode": "",
        "profit_strategy": "",
    }})
    print(f"Modified {result.modified_count} documents")

    # Drop any indexes that reference legacy fields
    try:
        idx_info = db.bots.index_information()
        for name, info in idx_info.items():
            keys = info.get('key') or info.get('key_pattern') or []
            key_fields = [k[0] if isinstance(k, (list, tuple)) else None for k in keys]
            if any(f in ("win_percentage", "creation_mode", "profit_strategy") for f in key_fields):
                print(f"Dropping index {name} ({key_fields})")
                db.bots.drop_index(name)
    except Exception as e:
        print(f"Warning: could not inspect/drop indexes: {e}")

    print("Migration complete.")


if __name__ == "__main__":
    main()