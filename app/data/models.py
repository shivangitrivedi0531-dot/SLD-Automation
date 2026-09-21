from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Asset:
    """Normalized asset record."""
    asset_id: Optional[str] = None
    survey_id: Optional[str] = None
    asset_category: Optional[str] = None
    asset_type: Optional[str] = None
    condition_type: Optional[str] = None
    cable_spec: Optional[str] = None
    label: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_url: Optional[str] = None
    remarks: Optional[str] = None
    tagged_at: Optional[str] = None


@dataclass
class RoutePoint:
    """Normalized route point record."""
    point_id: Optional[int] = None
    sequence_no: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    recorded_at: Optional[str] = None


@dataclass
class CableSegment:
    """Normalized cable segment record."""
    from_asset: Optional[str] = None
    to_asset: Optional[str] = None
    cable_type: Optional[str] = None
    cable_size: Optional[str] = None
    length_m: Optional[float] = None


@dataclass
class SurveyMetadata:
    """Normalized survey-level metadata."""
    survey_id: Optional[str] = None
    project_name: Optional[str] = None
    feeder_name: Optional[str] = None
    from_ss_name: Optional[str] = None
    to_ss_name: Optional[str] = None
    circle_name: Optional[str] = None
    division_name: Optional[str] = None
    sub_division_name: Optional[str] = None
    location_name: Optional[str] = None
    loa_number: Optional[str] = None
    drawing_number: Optional[str] = None
    at_number: Optional[str] = None
    page_size: Optional[str] = None
    status: Optional[str] = None
    surveyed_by_names: List[str] = field(default_factory=list)
    drawn_by: Optional[str] = None
    checked_by: Optional[str] = None
    verified_by_pm: Optional[str] = None
    submission_date: Optional[str] = None
    cable_name: Optional[str] = None
    total_route_distance_meters: Optional[float] = None
    total_route_points_count: Optional[int] = None
    total_assets_count: Optional[int] = None
    sld_pdf_url: Optional[str] = None


@dataclass
class FeederData:
    """Main normalized feeder dataset containing survey metadata, assets, route points, cable segments, and summary."""
    metadata: SurveyMetadata = field(default_factory=SurveyMetadata)
    assets: List[Asset] = field(default_factory=list)
    route_points: List[RoutePoint] = field(default_factory=list)
    cable_segments: List[CableSegment] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
