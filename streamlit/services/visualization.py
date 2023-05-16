from typing import List, Mapping, Tuple
from pandas import DataFrame
import folium
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st

from constants import COURTS

# Center coordinates
LONGITUDE = 42.114523952464275
LATITUDE = 15.974121093750002
# Standard width and height of the map
WIDTH = 1000
HEIGHT = 650
# Zoom level
ZOOM = 6


def __count_total(court_data: Mapping[str, Mapping[str, int]]) -> Tuple[int, int]:
    total = dict()
    for _, measure_count in court_data.items():
        for outcome, count in measure_count.items():
            outcome_count = total.setdefault(outcome, 0)
            total[outcome] = outcome_count + count
    granted = total.get("Concessa", 0)
    rejected = total.get("Rigettata", 0)
    return granted, rejected


def build_map(
    data: Mapping[str, Mapping[str, Mapping[str, int]]],
    lon: float = LONGITUDE,
    lat: float = LATITUDE,
    zoom: int = ZOOM,
) -> folium.Map:
    map = folium.Map(location=[lon, lat], zoom_start=zoom, min_zoom=zoom)
    for court, court_data in data.items():
        # Total count of granted and rejected ordinances
        granted, rejected = __count_total(court_data)
        # A marker is red if the rejected are more than the granted, green otherwise
        icon = folium.Icon(color="red" if rejected > granted else "green")
        html = f"<b>Concesse</b>: {granted}<br/>\n<b>Rigettate</b>: {rejected}"
        location = COURTS.get(court)
        if location is not None:
            folium.Marker(
                location=location, popup=html, icon=icon, tooltip=court
            ).add_to(map)
    return map


def get_court_information(
    data: Mapping[str, Mapping[str, Mapping[str, int]]], court: str
) -> DataFrame:
    if court is None:
        return None
    court_data = data.get(court)
    if court_data is None:
        return None
    df = DataFrame.from_dict(court_data).fillna(0).astype(int).T
    return df


def build_wordcloud(
    data: Mapping[str, Mapping[str, float]],
    court: str,
) -> WordCloud:
    if court is None:
        return None
    freq = data.get(court)
    if freq is None:
        return None
    return WordCloud(background_color="white").fit_words(freq)


def draw_wordcloud(wordcloud: WordCloud) -> None:
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    return fig
