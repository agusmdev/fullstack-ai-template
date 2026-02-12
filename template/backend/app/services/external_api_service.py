from typing import Any

import requests
from pydantic import BaseModel, ConfigDict

from app.services.exceptions import ExternalApiException


class ExternalApiService(BaseModel):
    headers: dict[str, str] = {}
    base_url: str
    model_config = ConfigDict(extra="allow", arbitrary_types_allowed=True)
    return_json: bool = True

    def post(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__send_request(endpoint, method="post", **kwargs)

    def get(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__send_request(endpoint, method="get", **kwargs)

    def put(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__send_request(endpoint, method="put", **kwargs)

    def patch(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__send_request(endpoint, method="patch", **kwargs)

    def delete(self, endpoint: str, **kwargs: Any) -> Any:
        return self.__send_request(endpoint, method="delete", **kwargs)

    def __send_request(
        self,
        endpoint: str,
        method: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        url = self.base_url + endpoint
        headers = headers or self.headers
        try:
            response = requests.request(
                method=method, url=url, headers=headers, **kwargs
            )
            response.raise_for_status()
            if self.return_json:
                return response.json()
            return response
        except requests.exceptions.HTTPError as err:
            print(err)  # TODO use logger
            raise ExternalApiException(
                status_code=response.status_code, detail=response.text
            ) from err
