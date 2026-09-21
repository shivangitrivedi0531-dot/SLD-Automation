import os
import sys
import requests
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.api.auth_client import ERPAuthClient


def test_download_sld():
    load_dotenv()
    survey_id = "47"

    auth_client = ERPAuthClient()
    auth_client.login()

    headers = auth_client.get_auth_headers()
    url = f"{auth_client.base_url}/api/geo-survey/surveys/{survey_id}/download-sld"

    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        http_status = response.status_code
        content_type = response.headers.get("Content-Type", "Unknown")

        response.raise_for_status()

        # Output directory
        output_dir = os.path.join(project_root, "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "reference_survey_47_sld.pdf")

        # Save PDF content
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(output_path)

        print(f"HTTP Status: {http_status}")
        print(f"Content-Type: {content_type}")
        print(f"Downloaded File Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        print(f"Output Path: {output_path}")

    except Exception as e:
        http_status = getattr(getattr(e, "response", None), "status_code", "Error")
        c_type = getattr(getattr(e, "response", None), "headers", {}).get("Content-Type", "Unknown")
        print(f"HTTP Status: {http_status}")
        print(f"Content-Type: {c_type}")
        print("Downloaded File Size: 0 bytes")
        print(f"Output Path: Failed ({e})")


if __name__ == "__main__":
    test_download_sld()
