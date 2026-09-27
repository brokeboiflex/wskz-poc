"""Atomic pointer to a complete, checksummed checkpoint generation."""

import hashlib
import json
import os
import uuid
from pathlib import Path


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def atomic_json(path, value):
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    # Persist the directory entry as well as the file contents on the Linux trainer.
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def resolve(directory):
    pointer = json.loads((directory / "latest.json").read_text())
    name = pointer["file"]
    if Path(name).name != name or not name.startswith("state-") or not name.endswith(".pt"):
        raise ValueError("Invalid checkpoint pointer")
    path = directory / name
    if digest(path) != pointer["sha256"]:
        raise ValueError("Checkpoint integrity mismatch")
    return path


def save(directory, payload, serializer):
    previous = resolve(directory) if (directory / "latest.json").exists() else None
    name = "state-" + uuid.uuid4().hex + ".pt"
    path = directory / name
    # The pointer still references the last good generation throughout this write.
    with path.open("xb") as handle:
        serializer(payload, handle)
        handle.flush()
        os.fsync(handle.fileno())
    atomic_json(directory / "latest.json", {"file": name, "sha256": digest(path)})
    # Rolling latest semantics: only the previously referenced task checkpoint is retired.
    # Orphans from interrupted writes are deliberately preserved for inspection.
    if previous is not None:
        previous.unlink()
    return path
