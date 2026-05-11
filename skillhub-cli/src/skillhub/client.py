from __future__ import annotations

from typing import Any

import httpx


class SkillHubClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError("服务端返回了无效 JSON 响应") from exc

        if not isinstance(payload, dict):
            raise ValueError("服务端返回的数据格式不正确")

        return payload

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            response = await client.get(path, headers=self.headers, **kwargs)
            response.raise_for_status()
            return self._parse_json(response)

    async def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            response = await client.post(path, headers=self.headers, **kwargs)
            response.raise_for_status()
            return self._parse_json(response)

    async def download(self, url: str) -> bytes:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
