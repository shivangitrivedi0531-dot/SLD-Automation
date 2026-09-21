import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient
from app.api.client import ERPApiClient


def test_get_summary():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()
    api_client = ERPApiClient(auth_client=auth_client)

    try:
        res = api_client.get_summary(survey_id)
        http_status = 200
        success = True

        top_keys = list(res.keys()) if isinstance(res, dict) else []

        data = res.get("data", {}) if isinstance(res, dict) else {}
        if isinstance(data, dict):
            summary_data_keys = list(data.keys())
            safe_numeric_fields = {
                k: v for k, v in data.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
            }
            # Also include dictionary numeric values if nested
            for k, v in data.items():
                if isinstance(v, dict):
                    safe_numeric_fields[k] = {
                        nk: nv for nk, nv in v.items() if isinstance(nv, (int, float)) and not isinstance(nv, bool)
                    }
        elif isinstance(res, dict):
            summary_data_keys = top_keys
            safe_numeric_fields = {
                k: v for k, v in res.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
            }
        else:
            summary_data_keys = []
            safe_numeric_fields = {}

        print(f"HTTP Status: {http_status}")
        print(f"Success/Failure: Success")
        print(f"Top-Level Response Keys: {top_keys}")
        print(f"Summary Data Keys: {summary_data_keys}")
        print(f"Safe Numeric/Count Fields: {safe_numeric_fields}")

    except Exception as e:
        http_status = getattr(getattr(e, "response", None), "status_code", "Error")
        print(f"HTTP Status: {http_status}")
        print("Success/Failure: Failure")
        print("Top-Level Response Keys: None")
        print("Summary Data Keys: None")
        print("Safe Numeric/Count Fields: None")


if __name__ == "__main__":
    test_get_summary()
