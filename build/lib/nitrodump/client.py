"""Codeium language server client for querying user status."""

import subprocess
import json
import warnings
from typing import Optional
from pathlib import Path

import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning

from nitrodump.models import GetUserStatusResponse

# Suppress SSL warnings for localhost (self-signed cert)
warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class CodeiumServerError(Exception):
    """Raised when the Codeium server cannot be found or contacted."""

    pass


class CodeiumClient:
    """Client for interacting with the local Codeium language server."""

    PROCESS_NAME = "language_server_macos_arm"
    ENDPOINT = "exa.language_server_pb.LanguageServerService/GetUserStatus"
    DEFAULT_IDE = "antigravity"

    def __init__(self, ide_name: str = DEFAULT_IDE):
        """Initialize the Codeium client.

        Args:
            ide_name: The IDE name to report to the server (default: antigravity).
        """
        self.ide_name = ide_name
        self._pid: Optional[int] = None
        self._port: Optional[int] = None
        self._token: Optional[str] = None

    def _find_server_process(self) -> Optional[int]:
        """Find the Codeium language server process ID.

        Returns:
            The process ID if found, None otherwise.
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", self.PROCESS_NAME],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            pass
        return None

    def _extract_csrf_token(self, pid: int) -> Optional[str]:
        """Extract the CSRF token from the server process command line.

        Args:
            pid: The process ID of the Codeium server.

        Returns:
            The CSRF token if found, None otherwise.
        """
        try:
            result = subprocess.run(
                ["ps", "-ww", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return None

            # Parse command line for --csrf_token argument
            args = result.stdout.strip().split()
            for i, arg in enumerate(args):
                if arg == "--csrf_token" and i + 1 < len(args):
                    return args[i + 1]
        except (subprocess.SubprocessError, IndexError):
            pass
        return None

    def _find_server_port(self, pid: int) -> Optional[int]:
        """Find the port the Codeium server is listening on.

        Args:
            pid: The process ID of the Codeium server.

        Returns:
            The port number if found, None otherwise.
        """
        try:
            result = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return None

            # Look for our process listening on localhost
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and "language_" in parts[0]:
                    for part in parts:
                        if part.startswith("127.0.0.1:"):
                            return int(part.split(":")[1])
        except (subprocess.SubprocessError, ValueError, IndexError):
            pass
        return None

    def _ensure_server_info(self) -> None:
        """Ensure server PID, port, and token are discovered.

        Raises:
            CodeiumServerError: If the server is not running or info cannot be extracted.
        """
        if self._pid is None:
            self._pid = self._find_server_process()
            if self._pid is None:
                raise CodeiumServerError(
                    f"Codeium language server ({self.PROCESS_NAME}) is not running"
                )

        if self._token is None:
            self._token = self._extract_csrf_token(self._pid)
            if self._token is None:
                raise CodeiumServerError("Could not extract CSRF token from server process")

        if self._port is None:
            self._port = self._find_server_port(self._pid)
            if self._port is None:
                raise CodeiumServerError("Could not find server listening port")

    def get_user_status(self, return_raw: bool = False):
        """Get the current user status from the Codeium server.

        Args:
            return_raw: If True, returns raw dict and response object. If False,
                        returns validated GetUserStatusResponse model.

        Returns:
            If return_raw=False: GetUserStatusResponse with plan info, credits, and model quotas.
            If return_raw=True: Tuple of (raw dict, requests.Response object).

        Raises:
            CodeiumServerError: If the server cannot be contacted.
        """
        self._ensure_server_info()

        url = f"https://127.0.0.1:{self._port}/{self.ENDPOINT}"
        headers = {
            "X-Codeium-Csrf-Token": self._token,
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
        }
        payload = {
            "metadata": {
                "ideName": self.ide_name,
                "extensionName": self.ide_name,
                "locale": "en",
            }
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                verify=False,  # Self-signed cert
                timeout=10,
            )
            response.raise_for_status()
        except RequestException as e:
            raise CodeiumServerError(f"Failed to contact server: {e}") from e

        try:
            data = response.json()
            if return_raw:
                return data, response
            return GetUserStatusResponse.model_validate(data)
        except Exception as e:
            raise CodeiumServerError(f"Failed to parse response: {e}") from e

    @property
    def pid(self) -> Optional[int]:
        """The server process ID (discovered lazily)."""
        if self._pid is None:
            self._pid = self._find_server_process()
        return self._pid

    @property
    def port(self) -> Optional[int]:
        """The server port (discovered lazily)."""
        self._ensure_server_info()
        return self._port

    @property
    def token(self) -> Optional[str]:
        """The CSRF token (discovered lazily)."""
        self._ensure_server_info()
        return self._token
