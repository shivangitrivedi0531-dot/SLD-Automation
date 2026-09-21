import os
import sys
from dotenv import load_dotenv

# Ensure project root is in sys.path when running script directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient


def test_authentication():
    load_dotenv()

    emp_code = os.getenv("ERP_EMPLOYEE_CODE")
    pin = os.getenv("ERP_PIN")

    print("=== ERP API Authentication Test ===")
    print(f"Base URL: {os.getenv('ERP_BASE_URL', 'https://erp.iedinfra.com')}")
    print(f"Employee Code provided: {'YES' if emp_code else 'NO (Missing from .env)'}")
    print(f"PIN provided: {'YES' if pin else 'NO (Missing from .env)'}")
    print("-----------------------------------")

    if not emp_code or not pin:
        print("[WARNING] Missing ERP_EMPLOYEE_CODE or ERP_PIN in .env file.")
        print("Please configure your credentials in .env before running login.")
        return

    client = ERPAuthClient()

    try:
        result = client.login()
        print("Login request completed")
        print(f"HTTP Status Code: {result['status_code']}")
        print(f"Success: {result['success']}")
        print(f"Response keys: {result['response_keys']}")
        print(f"Token received: {'YES' if result['token_received'] else 'NO'}")
        print(f"Detected token field: '{result['token_field_found']}'")

        if client.is_authenticated:
            headers = client.get_auth_headers()
            has_auth = "Authorization" in headers
            has_content_type = headers.get("Content-Type") == "application/json"
            has_accept = headers.get("Accept") == "application/json"
            bearer_valid = headers.get("Authorization", "").startswith("Bearer ")
            
            headers_valid = has_auth and bearer_valid and has_content_type and has_accept
            print(f"Auth headers ready: {'YES' if headers_valid else 'NO'}")

    except Exception as e:
        print(f"[ERROR] Authentication failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_authentication()
