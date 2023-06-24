from typing import Mapping, Tuple
from pandas import DataFrame
import folium

# Center coordinates
LATITUDE = 44.06390660801779
LONGITUDE = 11.453247070312502
# Standard width and height of the map
WIDTH = 1000
HEIGHT = 750
# Zoom level
ZOOM = 8


def __count_total(summary: Mapping[str, Mapping[str, int]]) -> Tuple[int, int]:
    total = dict()
    for _, measure_count in summary.items():
        for outcome, count in measure_count.items():
            outcome_count = total.setdefault(outcome, 0)
            total[outcome] = outcome_count + count
    granted = total.get("Concessa", 0)
    rejected = total.get("Rigettata", 0)
    return granted, rejected


def build_map(
    places: Mapping[str, Tuple[float, float]],
    color: str,
    lat: float = LATITUDE,
    lng: float = LONGITUDE,
    zoom: int = ZOOM,
) -> folium.Map:
    map = folium.Map(
        location=[lat, lng],
        zoom_start=zoom,
        min_zoom=zoom,
        zoom_control=False,
        max_zoom=zoom,
    )
    for place, location in places.items():
        # A marker is red if the rejected are more than the granted, green otherwise
        icon = folium.Icon(color=color)
        folium.Marker(location=location, icon=icon, tooltip=place).add_to(map)
    return map


def get_court_information(
    data: Mapping[str, Mapping[str, Mapping[str, int]]], institution_court: str
) -> DataFrame:
    if institution_court is None:
        return None
    court_data = data.get(institution_court)
    if court_data is None:
        return None
    df = DataFrame.from_dict(court_data).fillna(0).astype(int).T
    return df
