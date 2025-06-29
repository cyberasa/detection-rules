from pathlib import Path
from tomlkit import parse, dumps
import re

rules_path = Path("rules")  # Top-level folder

for rule_file in rules_path.rglob("*.toml"):
    try:
        with open(rule_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
            data = parse(raw_content)

        rule = data.get('rule')
        if not rule:
            print(f"⏭️ Skipped (no [rule] block): {rule_file.relative_to(rules_path)}")
            continue

        updated = False

        # --- Modify 'index' field ---
        if 'index' in rule:
            index = rule['index']
            if isinstance(index, list):
                rule['index'] = [i.replace('*', '*tmp*') for i in index]
            elif isinstance(index, str):
                rule['index'] = index.replace('*', '*tmp*')
            updated = True

        # --- Modify 'machine_learning_job_id' field ---
        if 'machine_learning_job_id' in rule:
            ml_ids = rule['machine_learning_job_id']
            if isinstance(ml_ids, list):
                rule['machine_learning_job_id'] = [
                    i if i.startswith("tmp_") else f"tmp_{i}" for i in ml_ids
                ]
            elif isinstance(ml_ids, str):
                if not ml_ids.startswith("tmp_"):
                    rule['machine_learning_job_id'] = f"tmp_{ml_ids}"
            updated = True

        # # --- Modify 'query' field if language is 'esql' ---
        if rule.get('language') == 'esql' and 'query' in rule and isinstance(rule['query'], str):
            original_query = rule['query']

            def replace_from_clause(match):
                from_clause = match.group(1)
                indices = [i.strip() for i in from_clause.split(',')]
                modified = [i.replace('*', '*tmp*') for i in indices]
                return f"FROM {', '.join(modified)}"

            updated_query = re.sub(
                r'(?i)FROM\s+([^\n]+)',
                replace_from_clause,
                original_query,
                count=1
            )

            if updated_query != original_query:
                updated = True

        # --- Save file if modified ---
        if updated:
            with open(rule_file, "w", encoding="utf-8") as f:
                f.write(dumps(data))
            print(f"✅ Updated: {rule_file.relative_to(rules_path)}")
        else:
            print(f"⏭️ No changes: {rule_file.relative_to(rules_path)}")

    except Exception as e:
        print(f"❌ Error processing {rule_file.relative_to(rules_path)}: {e}")
