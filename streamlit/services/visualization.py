from collections import defaultdict
from typing import Iterable, Mapping, Tuple
from matplotlib.figure import Figure
import folium
import altair as alt
import pandas as pd

from constants import COURT_PLACES, OFFICE_PLACES

# Center coordinates
LATITUDE = 43.88601647043423
LONGITUDE = 11.645507812500002
# Standard width and height of the map
WIDTH = 1600
HEIGHT = 500
# Zoom level
ZOOM = 8
# Graph font size
FONT_SIZE = 12


def __create_points(
    data: Iterable[str],
    locations: Mapping[str, Tuple[float, float]],
    color: str,
    institution: str,
) -> Iterable[folium.Marker]:
    for place in data:
        location = locations.get(place)
        if location is None:
            continue
        icon = folium.Icon(color=color)
        tooltip = institution + " - " + place
        marker = folium.Marker(location=location, tooltip=tooltip, icon=icon)
        yield marker


def create_map(
    data: Mapping[str, Mapping],
    court_locations: Mapping[str, Tuple[float, float]] = COURT_PLACES,
    office_locations: Mapping[str, Tuple[float, float]] = OFFICE_PLACES,
    lat: float = LATITUDE,
    lng: float = LONGITUDE,
    zoom: int = ZOOM,
) -> folium.Map:
    data_map = folium.Map(
        location=[lat, lng],
        zoom_start=zoom,
        min_zoom=zoom,
        max_zoom=zoom,
        zoom_control=False,
    )
    for institution, places_data in data.items():
        # Institution-specific parameters
        if institution.startswith("Tribunale"):
            color = "green"
            locations = court_locations
        else:
            color = "blue"
            locations = office_locations
        # Adds points to the map
        for marker in __create_points(
            places_data.keys(), locations, color, institution
        ):
            marker.add_to(data_map)
    return data_map


def __to_records(
    dictionary: Mapping[str, Mapping[str, Mapping]], true_label: str
) -> Iterable[Mapping]:
    records = []
    for year, year_data in dictionary.items():
        if year == "1900":
            year = "Senza Data"
        for measure, measure_data in year_data.items():
            records.append(
                {
                    "Anno": year,
                    "Misura": measure,
                    "Esito": true_label,
                    "Quantità": measure_data["true"],
                }
            )
            records.append(
                {
                    "Anno": year,
                    "Misura": measure,
                    "Esito": "Rigettate",
                    "Quantità": measure_data["false"],
                }
            )
    return records


def create_plot(data: Mapping[str, Mapping[str, Mapping]], is_court: bool) -> Figure:
    true_label = "Concesse" if is_court else "Accolte"
    records = __to_records(data, true_label)
    df = pd.DataFrame.from_records(records)
    chart = (
        alt.Chart(df)
        .mark_bar()
        .properties(
            width=180,
            height=180,
        )
        .encode(
            x="Anno:O",
            y=alt.Y("sum(Quantità):Q", title="Numero Ordinanze"),
            color="Esito:N",
            facet=alt.Facet(
                "Misura:N",
                columns=3,
                header=alt.Header(labelFontSize=FONT_SIZE),
            ),
        )
        .configure_axis(labelFontSize=FONT_SIZE, titleFontSize=FONT_SIZE)
    )
    return chart
