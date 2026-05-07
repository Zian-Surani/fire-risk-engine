from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import Settings
from app.models.contracts import QueryResult


@dataclass(slots=True)
class TokenCache:
    access_token: str
    expires_at: float


class DatabricksClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            base_url=(settings.databricks_host or "").rstrip("/"),
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        self._token_cache: TokenCache | None = None
        self._warehouse_id: str | None = settings.databricks_warehouse_id
        self._warehouse_cache_until = 0.0
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        await self._client.aclose()

    async def is_available(self) -> bool:
        try:
            await self._get_auth_headers()
            await self._get_warehouse_id()
            return True
        except Exception:
            return False

    async def fetch_rows(self, statement: str) -> QueryResult:
        started = time.perf_counter()
        payload = {
            "statement": statement,
            "warehouse_id": await self._get_warehouse_id(),
            "wait_timeout": "20s",
            "disposition": "INLINE",
        }
        response = await self._client.post(
            "/api/2.0/sql/statements/",
            json=payload,
            headers=await self._get_auth_headers(),
        )
        response.raise_for_status()
        statement_payload = response.json()
        statement_id = statement_payload["statement_id"]
        terminal_payload = await self._poll_statement(statement_id)
        manifest = terminal_payload.get("manifest", {})
        schema = manifest.get("schema", {})
        columns = [column["name"] for column in schema.get("columns", [])]
        rows = []
        for record in terminal_payload.get("result", {}).get("data_array", []):
            rows.append(dict(zip(columns, record, strict=False)))
        return QueryResult(
            rows=rows,
            columns=columns,
            duration_ms=(time.perf_counter() - started) * 1000,
        )

    async def _poll_statement(self, statement_id: str) -> dict[str, Any]:
        for _ in range(30):
            response = await self._client.get(
                f"/api/2.0/sql/statements/{statement_id}",
                headers=await self._get_auth_headers(),
            )
            response.raise_for_status()
            payload = response.json()
            state = payload.get("status", {}).get("state")
            if state == "SUCCEEDED":
                return payload
            if state in {"FAILED", "CANCELED", "CLOSED"}:
                message = payload.get("status", {}).get("error", {}).get("message", "Databricks statement failed")
                raise RuntimeError(message)
            await asyncio.sleep(2)
        raise TimeoutError(f"Databricks statement {statement_id} timed out")

    async def _get_auth_headers(self) -> dict[str, str]:
        token = await self._get_access_token()
        return {"Authorization": f"Bearer {token}"}

    async def _get_access_token(self) -> str:
        if self.settings.databricks_token:
            return self.settings.databricks_token

        async with self._lock:
            now = time.time()
            if self._token_cache and self._token_cache.expires_at - 30 > now:
                return self._token_cache.access_token

            if self.settings.databricks_auth_type != "metadata-service" or not self.settings.databricks_metadata_service_url:
                raise RuntimeError("Databricks credentials are not configured")

            response = await self._client.get(
                self.settings.databricks_metadata_service_url,
                headers={
                    "x-databricks-metadata-version": "1",
                    "x-databricks-host": (self.settings.databricks_host or "").rstrip("/"),
                },
            )
            if response.status_code == 404:
                raise RuntimeError("Local Databricks metadata service was not found")
            response.raise_for_status()
            payload = response.json()
            token = payload.get("access_token")
            expires_on = float(payload.get("expires_on", now + 300))
            if not token:
                raise RuntimeError("Databricks metadata service returned no access token")
            self._token_cache = TokenCache(access_token=token, expires_at=expires_on)
            return token

    async def _get_warehouse_id(self) -> str:
        now = time.time()
        if self._warehouse_id and self._warehouse_cache_until > now:
            return self._warehouse_id

        response = await self._client.get(
            "/api/2.0/sql/warehouses",
            headers=await self._get_auth_headers(),
        )
        response.raise_for_status()
        warehouses = response.json().get("warehouses", [])
        if not warehouses:
            raise RuntimeError("No Databricks SQL warehouses are available for this workspace")

        preferred = next(
            (
                warehouse
                for warehouse in warehouses
                if warehouse.get("state") in {"RUNNING", "STARTING"}
            ),
            warehouses[0],
        )
        self._warehouse_id = preferred["id"]
        self._warehouse_cache_until = now + 600
        return self._warehouse_id
