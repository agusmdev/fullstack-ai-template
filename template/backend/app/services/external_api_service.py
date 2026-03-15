from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from app.services.exceptions import ExternalApiException


class ExternalApiService(BaseModel):
    headers: dict[str, str] = {}
    base_url: str
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    return_json: bool = True

    async def post(self, endpoint: str, **kwargs: Any) -> Any:
        return await self._send_request(endpoint, method="POST", **kwargs)

    async def get(self, endpoint: str, **kwargs: Any) -> Any:
        return await self._send_request(endpoint, method="GET", **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> Any:
        return await self._send_request(endpoint, method="PUT", **kwargs)

    async def patch(self, endpoint: str, **kwargs: Any) -> Any:
        return await self._send_request(endpoint, method="PATCH", **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> Any:
        return await self._send_request(endpoint, method="DELETE", **kwargs)

    async def _send_request(
        self,
        endpoint: str,
        method: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        url = self.base_url + endpoint
        merged_headers = {**self.headers, **(headers or {})}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method, url=url, headers=merged_headers, **kwargs
                )
                response.raise_for_status()
                if self.return_json:
                    return response.json()
                return response
        except httpx.HTTPStatusError as err:
            raise ExternalApiException(
                status_code=err.response.status_code, detail=err.response.text
            ) from err
