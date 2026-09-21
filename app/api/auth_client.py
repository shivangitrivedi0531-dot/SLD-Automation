import os
import logging
from typing import Optional, Dict, Any, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ERPAuthClient:
    """Authentication client for the ERP API (https://erp.iedinfra.com)."""

    def __init__(self, base_url: Optional[str] = None):
        env_base = os.getenv("ERP_BASE_URL", "https://erp.iedinfra.com")
        self.base_url = (base_url or env_base).rstrip("/")
        self._token: Optional[str] = None  # Stores only the accessToken
        self._refresh_token: Optional[str] = None  # Stored separately, never used as Authorization header
        self._token_field: Optional[str] = None

    def login(
        self,
        employee_code: Optional[str] = None,
        pin: Optional[str] = None,
        timeout: int = 15,
    ) -> Dict[str, Any]:
        """Authenticate against /api/auth/login endpoint.

        Reads employee_code and pin from arguments or environment variables
        (ERP_EMPLOYEE_CODE, ERP_PIN). Never logs or prints raw credentials.
        """
        code = employee_code or os.getenv("ERP_EMPLOYEE_CODE")
        user_pin = pin or os.getenv("ERP_PIN")

        if not code or not user_pin:
            raise ValueError(
                "Missing credentials. Please set ERP_EMPLOYEE_CODE and ERP_PIN in environment or pass to login()."
            )

        url = f"{self.base_url}/api/auth/login"
        payload = {
            "employee_code": code,
            "pin": user_pin,
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Authentication request failed: %s", str(e))
            raise

        access_token, refresh_token, token_key = self._extract_tokens(data)
        if access_token:
            self._token = access_token
            self._refresh_token = refresh_token
            self._token_field = token_key
        else:
            self._token = None
            self._refresh_token = None
            self._token_field = None

        top_keys = list(data.keys()) if isinstance(data, dict) else []

        return {
            "status_code": response.status_code,
            "success": bool(data.get("success", False)) if isinstance(data, dict) else False,
            "response_keys": top_keys,
            "token_field_found": self._token_field,
            "token_received": bool(self._token),
        }

    def _extract_tokens(self, data: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract access token specifically from response['data']['accessToken']."""
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            payload = data["data"]
            access_token = payload.get("accessToken")
            refresh_token = payload.get("refreshToken")
            if isinstance(access_token, str) and access_token.strip():
                ref_str = refresh_token if isinstance(refresh_token, str) and refresh_token.strip() else None
                return access_token, ref_str, "data.accessToken"

        return None, None, None

    def get_auth_headers(self) -> Dict[str, str]:
        """Return headers required for authenticated requests using accessToken."""
        if not self._token:
            raise RuntimeError(
                "Client is not authenticated. Call login() successfully first."
            )
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @property
    def is_authenticated(self) -> bool:
        return bool(self._token)
