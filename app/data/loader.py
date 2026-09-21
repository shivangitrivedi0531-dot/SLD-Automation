from typing import Optional, Dict, Any, List
from app.api.client import ERPApiClient
from app.data.models import FeederData
from app.data.normalizer import normalize_feeder_data


def load_feeder_data(
    survey_id: str,
    api_client: Optional[ERPApiClient] = None,
) -> FeederData:
    """Fetch raw survey resources via ERPApiClient and return a normalized FeederData object."""
    client = api_client or ERPApiClient()

    # 1. Fetch complete survey details
    raw_survey = client.get_survey(survey_id, all_points=True)

    # 2. Fetch assets
    raw_assets_res = client.get_assets(survey_id)

    # 3. Fetch cable segments
    raw_cable_segments_res = client.get_cable_segments(survey_id)

    # 4. Fetch ALL paginated route points
    raw_route_points = client.get_all_route_points(survey_id)

    # 5. Fetch summary
    raw_summary_res = client.get_summary(survey_id)

    # Unwrap envelope structures if needed
    if isinstance(raw_assets_res, dict):
        data_field = raw_assets_res.get("data")
        if isinstance(data_field, list):
            raw_assets = data_field
        elif isinstance(data_field, dict):
            raw_assets = data_field.get("assets", [])
        else:
            raw_assets = []
    elif isinstance(raw_assets_res, list):
        raw_assets = raw_assets_res
    else:
        raw_assets = []

    if isinstance(raw_cable_segments_res, dict):
        data_field = raw_cable_segments_res.get("data")
        if isinstance(data_field, list):
            raw_cable_segments = data_field
        elif isinstance(data_field, dict):
            raw_cable_segments = data_field.get("cable_segments", [])
        else:
            raw_cable_segments = []
    elif isinstance(raw_cable_segments_res, list):
        raw_cable_segments = raw_cable_segments_res
    else:
        raw_cable_segments = []

    if isinstance(raw_summary_res, dict):
        raw_summary = raw_summary_res.get("data", raw_summary_res)
    else:
        raw_summary = {}

    # Normalize into FeederData model
    feeder_data = normalize_feeder_data(
        raw_survey=raw_survey,
        raw_assets=raw_assets,
        raw_route_points=raw_route_points,
        raw_cable_segments=raw_cable_segments,
        raw_summary=raw_summary,
    )

    return feeder_data
