"""Result cache + session store (DynamoDB or local file).

Keyed by ``repo_id`` + a normalized ``change_request`` (§6). The local file cache
lives alongside the KB output (``<kb_dir>/<repo_id>/results.json``); the AWS cache
is a single DynamoDB table shared with chat sessions.
"""

from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


def cache_key(repo_id: str, change_request: str) -> str:
    norm = re.sub(r"\s+", " ", change_request.strip().lower())
    digest = hashlib.sha256(f"{repo_id}\n{norm}".encode("utf-8")).hexdigest()[:32]
    return f"{repo_id}#{digest}"


class Cache(ABC):
    @abstractmethod
    def get(self, repo_id: str, change_request: str) -> Optional[dict]: ...

    @abstractmethod
    def put(self, repo_id: str, change_request: str, result: dict) -> None: ...


class FileCache(Cache):
    def __init__(self, kb_dir: Path) -> None:
        self.kb_dir = Path(kb_dir)

    def _path(self, repo_id: str) -> Path:
        return self.kb_dir / repo_id / "results.json"

    def _load(self, repo_id: str) -> dict:
        p = self._path(repo_id)
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def get(self, repo_id: str, change_request: str) -> Optional[dict]:
        return self._load(repo_id).get(cache_key(repo_id, change_request))

    def put(self, repo_id: str, change_request: str, result: dict) -> None:
        data = self._load(repo_id)
        data[cache_key(repo_id, change_request)] = result
        p = self._path(repo_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")


class DdbCache(Cache):
    def __init__(self, table: str, region: Optional[str] = None) -> None:
        import boto3  # lazy

        self._table = boto3.resource("dynamodb", region_name=region).Table(table)

    def get(self, repo_id: str, change_request: str) -> Optional[dict]:
        item = self._table.get_item(
            Key={"result_id": cache_key(repo_id, change_request)}
        ).get("Item")
        if not item or "result" not in item:
            return None
        return json.loads(item["result"])

    def put(self, repo_id: str, change_request: str, result: dict) -> None:
        # Store as a JSON string to sidestep DynamoDB's float/Decimal handling.
        self._table.put_item(
            Item={
                "result_id": cache_key(repo_id, change_request),
                "repo_id": repo_id,
                "change_request": change_request,
                "result": json.dumps(result),
            }
        )
