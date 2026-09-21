import math
from typing import Optional, List, Dict, Any
from app.data.models import (
    Asset,
    RoutePoint,
    CableSegment,
    SurveyMetadata,
    FeederData,
)


def _to_str(val: Any) -> Optional[str]:
    """Safely convert value to string or None."""
    if val is None:
        return None
    return str(val)


def _to_float(val: Any) -> Optional[float]:
    """Safely convert value to float or None."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if not math.isnan(f) else None
    except (ValueError, TypeError):
        return None


def _to_int(val: Any) -> Optional[int]:
    """Safely convert value to int or None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def normalize_asset(raw: Dict[str, Any]) -> Asset:
    """Convert raw API dictionary into a normalized Asset model."""
    if not isinstance(raw, dict):
        return Asset()

    return Asset(
        asset_id=_to_str(raw.get("asset_id")),
        survey_id=_to_str(raw.get("survey_id")),
        asset_category=_to_str(raw.get("asset_category")),
        asset_type=_to_str(raw.get("asset_type")),
        condition_type=_to_str(raw.get("condition_type")),
        cable_spec=_to_str(raw.get("cable_spec")),
        label=_to_str(raw.get("label")),
        latitude=_to_float(raw.get("latitude")),
        longitude=_to_float(raw.get("longitude")),
        photo_url=_to_str(raw.get("photo_url")),
        remarks=_to_str(raw.get("remarks")),
        tagged_at=_to_str(raw.get("tagged_at")),
    )


def normalize_route_point(raw: Dict[str, Any]) -> RoutePoint:
    """Convert raw API dictionary into a normalized RoutePoint model."""
    if not isinstance(raw, dict):
        return RoutePoint()

    return RoutePoint(
        point_id=_to_int(raw.get("point_id")),
        sequence_no=_to_int(raw.get("sequence_no")),
        latitude=_to_float(raw.get("latitude")),
        longitude=_to_float(raw.get("longitude")),
        recorded_at=_to_str(raw.get("recorded_at")),
    )


def normalize_cable_segment(raw: Dict[str, Any]) -> CableSegment:
    """Convert raw API dictionary into a normalized CableSegment model."""
    if not isinstance(raw, dict):
        return CableSegment()

    return CableSegment(
        from_asset=_to_str(raw.get("from_asset") or raw.get("from_asset_id")),
        to_asset=_to_str(raw.get("to_asset") or raw.get("to_asset_id")),
        cable_type=_to_str(raw.get("cable_type")),
        cable_size=_to_str(raw.get("cable_size")),
        length_m=_to_float(raw.get("length_m") or raw.get("length") or raw.get("distance_m")),
    )


def normalize_survey_metadata(raw: Dict[str, Any]) -> SurveyMetadata:
    """Convert raw API survey metadata dictionary into a SurveyMetadata model."""
    if not isinstance(raw, dict):
        return SurveyMetadata()

    # Unwrap 'data' envelope if present
    data = raw.get("data", raw) if isinstance(raw.get("data"), dict) else raw

    surveyed_by = data.get("surveyed_by_names", [])
    if isinstance(surveyed_by, list):
        surveyed_by_names = [str(n) for n in surveyed_by if n is not None]
    else:
        surveyed_by_names = []

    return SurveyMetadata(
        survey_id=_to_str(data.get("survey_id")),
        project_name=_to_str(data.get("project_name")),
        feeder_name=_to_str(data.get("feeder_name")),
        from_ss_name=_to_str(data.get("from_ss_name")),
        to_ss_name=_to_str(data.get("to_ss_name")),
        circle_name=_to_str(data.get("circle_name")),
        division_name=_to_str(data.get("division_name")),
        sub_division_name=_to_str(data.get("sub_division_name")),
        location_name=_to_str(data.get("location_name")),
        loa_number=_to_str(data.get("loa_number")),
        drawing_number=_to_str(data.get("drawing_number")),
        at_number=_to_str(data.get("at_number")),
        page_size=_to_str(data.get("page_size")),
        status=_to_str(data.get("status")),
        surveyed_by_names=surveyed_by_names,
        drawn_by=_to_str(data.get("drawn_by")),
        checked_by=_to_str(data.get("checked_by")),
        verified_by_pm=_to_str(data.get("verified_by_pm")),
        submission_date=_to_str(data.get("submission_date")),
        cable_name=_to_str(data.get("cable_name")),
        total_route_distance_meters=_to_float(data.get("total_route_distance_meters")),
        total_route_points_count=_to_int(data.get("total_route_points_count")),
        total_assets_count=_to_int(data.get("total_assets_count")),
        sld_pdf_url=_to_str(data.get("sld_pdf_url")),
    )


def normalize_feeder_data(
    raw_survey: Dict[str, Any],
    raw_assets: Optional[List[Dict[str, Any]]] = None,
    raw_route_points: Optional[List[Dict[str, Any]]] = None,
    raw_cable_segments: Optional[List[Dict[str, Any]]] = None,
    raw_summary: Optional[Dict[str, Any]] = None,
) -> FeederData:
    """Normalize raw survey data and optional explicit sub-resource lists into FeederData."""
    metadata = normalize_survey_metadata(raw_survey)

    data = raw_survey.get("data", raw_survey) if isinstance(raw_survey, dict) and isinstance(raw_survey.get("data"), dict) else (raw_survey if isinstance(raw_survey, dict) else {})

    # Assets
    assets_source = raw_assets if raw_assets is not None else data.get("assets", [])
    if isinstance(assets_source, dict):
        assets_source = assets_source.get("assets", [])
    assets = [normalize_asset(a) for a in assets_source if isinstance(a, dict)]

    # Route points
    rp_source = raw_route_points if raw_route_points is not None else data.get("route_points", [])
    if isinstance(rp_source, dict):
        rp_source = rp_source.get("points", [])
    route_points = [normalize_route_point(rp) for rp in rp_source if isinstance(rp, dict)]

    # Cable segments
    cs_source = raw_cable_segments if raw_cable_segments is not None else data.get("cable_segments", [])
    if isinstance(cs_source, dict):
        cs_source = cs_source.get("cable_segments", [])
    cable_segments = [normalize_cable_segment(cs) for cs in cs_source if isinstance(cs, dict)]

    # Summary
    if raw_summary is not None:
        summary_dict = raw_summary.get("data", raw_summary) if isinstance(raw_summary, dict) else {}
    else:
        summary_dict = data.get("summary", {}) if isinstance(data, dict) else {}

    if not isinstance(summary_dict, dict):
        summary_dict = {}

    return FeederData(
        metadata=metadata,
        assets=assets,
        route_points=route_points,
        cable_segments=cable_segments,
        summary=summary_dict,
    )
