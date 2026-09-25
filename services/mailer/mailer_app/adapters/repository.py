import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from ..domain import DeliveryError, Receipt, SendCommand


class SqliteDeliveryRepository:
    """Private ledger. Run one mailer process per volume; no shared DB with router."""

    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                request_id TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                recipient TEXT NOT NULL,
                message_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('sending','submitted','failed','unknown')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            # Process died between reservation and durable acknowledgement.
            db.execute(
                "UPDATE deliveries SET status='unknown', updated_at=CURRENT_TIMESTAMP WHERE status='sending'"
            )

    def connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    @staticmethod
    def receipt(row: sqlite3.Row) -> Receipt:
        return Receipt(
            **{key: row[key] for key in ("request_id", "recipient", "status", "message_id")}
        )

    def reserve(self, command: SendCommand) -> tuple[bool, Receipt]:
        digest = sha256(
            json.dumps(asdict(command), sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM deliveries WHERE request_id=?", (command.request_id,)
            ).fetchone()
            if row is not None:
                if row["payload_hash"] != digest:
                    raise DeliveryError("idempotency_conflict")
                return False, self.receipt(row)
            message_id = f"<{command.request_id}@message-router.local>"
            db.execute(
                "INSERT INTO deliveries(request_id,payload_hash,recipient,message_id,status) VALUES(?,?,?,?, 'sending')",
                (command.request_id, digest, command.recipient, message_id),
            )
            return True, Receipt(command.request_id, command.recipient, "sending", message_id)

    def finish(self, request_id: str, status: str) -> Receipt:
        with closing(self.connect()) as db, db:
            db.execute(
                "UPDATE deliveries SET status=?, updated_at=CURRENT_TIMESTAMP WHERE request_id=?",
                (status, request_id),
            )
            row = db.execute(
                "SELECT * FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            if row is None:
                raise RuntimeError("missing delivery reservation")
            return self.receipt(row)

    def get(self, request_id: str) -> Receipt | None:
        with closing(self.connect()) as db:
            row = db.execute(
                "SELECT * FROM deliveries WHERE request_id=?", (request_id,)
            ).fetchone()
            return self.receipt(row) if row is not None else None

    def ready(self) -> bool:
        try:
            with closing(self.connect()) as db:
                db.execute("SELECT 1 FROM deliveries LIMIT 1")
            return True
        except sqlite3.Error:
            return False
