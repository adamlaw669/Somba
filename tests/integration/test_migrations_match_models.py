"""Guards against ORM/migration schema drift.

Found live on the VPS deployment: 0001's customers table still had the old
token_key column and never added mandate_id/bank_account_number/bank_code;
webhook_deliveries was missing outbox_event_id and last_response_status.
Every other test in this suite builds tables straight from Base.metadata
(Base.metadata.create_all), so none of them exercise Alembic at all and this
drift was invisible until a real Postgres deployment hit it in production.

This test actually runs the full migration chain against a throwaway SQLite
file and diffs the resulting columns, table by table, against the live ORM
models -- the only thing in this repo that does.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from somba.db.models import Base

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_migration_chain_produces_schema_matching_orm_models(tmp_path):
    db_path = tmp_path / "migration_check.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}", "PYTHONPATH": str(REPO_ROOT)}

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"

    con = sqlite3.connect(db_path)
    try:
        mismatches: list[str] = []
        for table_name, table in Base.metadata.tables.items():
            model_cols = {c.name for c in table.columns}
            rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
            if not rows:
                mismatches.append(f"{table_name}: no migration creates this table")
                continue
            db_cols = {r[1] for r in rows}
            missing = model_cols - db_cols
            extra = db_cols - model_cols
            if missing or extra:
                mismatches.append(
                    f"{table_name}: model-only={sorted(missing)} migration-only(stale)={sorted(extra)}"
                )

        assert not mismatches, (
            "Migrations don't produce the schema the ORM models expect:\n"
            + "\n".join(mismatches)
            + "\n\nAdd a migration for every model field change -- "
            "Base.metadata.create_all() in the other tests won't catch this."
        )
    finally:
        con.close()
