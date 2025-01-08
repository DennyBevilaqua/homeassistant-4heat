"""4Heat API class."""

import logging
from typing import Any

import requests

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class API:
    """Class for 4Heat API."""

    def __init__(self, code: str, pin: str, user: str, pwd: str) -> None:
        """Initialise."""
        self.code = code
        self.user = user
        self.pwd = pwd

    def get_token(self) -> dict[str, Any]:
        """Get api token."""
        try:
            r = requests.post(
                f"{API_BASE_URL}/Token",
                data={
                    "grant_type": "password",
                    "username": self.user,
                    "password": self.pwd,
                },
                timeout=30,
            )
            return r.json()
        except requests.exceptions.ConnectTimeout as err:
            raise APIConnectionError("Timeout connecting to api") from err

    def get_data(self, token: dict[str, Any]) -> dict[str, Any]:
        """Get api data."""
        try:
            r = requests.get(
                f"{API_BASE_URL}/api/devices/Details?id={self.code}",
                headers={"Authorization": f"Bearer {token.get("access_token")}"},
                timeout=30,
            )
            return r.json()
        except requests.exceptions.ConnectTimeout as err:
            raise APIConnectionError("Timeout connecting to api") from err

    def send_command(self, command: str, token: dict[str, Any]) -> bool:
        """Send command to api."""
        try:
            requests.post(
                f"{API_BASE_URL}/api/devices/command?id={self.code}&comando={command}",
                timeout=30,
            )
            return True
        except requests.exceptions.ConnectTimeout as err:
            raise APIConnectionError("Timeout connecting to api") from err
        else:
            return False


class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
