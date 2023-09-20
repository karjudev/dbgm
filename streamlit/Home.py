from datetime import date
from typing import List, Mapping, Tuple
import streamlit as st
from streamlit_folium import st_folium
from auth import check_authentication
from services.search_engine import (
    get_count,
    list_keywords_concepts,
    perform_query,
)
from services.visualization import HEIGHT, WIDTH, create_map, create_plot
from constants import (
    COURT_MEASURE_TYPES,
    COURT_PLACES,
    COURTS,
    INSTITUTIONS,
    OFFICE_MEASURE_TYPES,
    OFFICE_PLACES,
    OFFICES,
)


def __fetch_keywords_concepts() -> Tuple[List[str], List[str]]:
    # Searches keywords and concepts in session state
    juridic_data = st.session_state.get("juridic_data")
    if juridic_data is None:
        try:
            juridic_data = list_keywords_concepts()
            st.session_state["juridic_data"] = juridic_data
        except ValueError as e:
            st.error("Impossibile scaricare i dati giuridici")
            st.error(str(e))
            return None, None
    return juridic_data["keywords"], juridic_data["concepts"]


def __set_keywords_concepts(keywords: List[str], concepts: List[str]) -> None:
    st.session_state["juridic_data"] = {"keywords": keywords, "concepts": concepts}


def __display_aggregations(aggregations: Mapping, is_court: bool):
    # Creates the map
    data_map = create_map(aggregations)
    data = st_folium(data_map, width=WIDTH, height=HEIGHT)
    selected = data["last_object_clicked_tooltip"]
    if selected is None:
        return
    # Selects data
    institution, place = selected.split(" - ")
    data = aggregations[institution][place]
    chart = create_plot(data, is_court)
    st.altair_chart(chart)


def __display_hits(hits, is_court: bool) -> None:
    st.markdown(
        "<style> .stMarkdown>* {white-space: pre-wrap; font-family: monospace;} </style>",
        unsafe_allow_html=True,
    )
    for hit in hits:
        dictionary_keywords = ", ".join(hit["dictionary_keywords"])
        textrank_keywords = ", ".join(hit["textrank_keywords"])
        juridic_keywords = ", ".join(hit["juridic_keywords"])
        juridic_concepts = ", ".join(hit["juridic_concepts"])
        with st.container():
            st.subheader(f"📃 {hit['institution']} di {hit['court']}")
            st.write(hit["highlight"], unsafe_allow_html=True)
            if hit["publication_date"] != "1900-01-01":
                st.write(f"🕑 **Data di Pubblicazione**: {hit['publication_date']}")
            # Displays measures and outcomes
            for measure in hit["measures"]:
                if is_court:
                    outcome = "Concessa" if measure["outcome"] else "Rigettata"
                else:
                    outcome = "Accolta" if measure["outcome"] else "Rigettata"
                st.write(f"🧭 **{measure['measure']}** - *{outcome}*")
            # Displays keywords
            if len(dictionary_keywords) > 0:
                st.markdown(
                    f"📌 **Parole chiave (dizionario giuridico)**: {dictionary_keywords}"
                )
            if len(textrank_keywords) > 0:
                st.markdown(f"📌 **Parole chiave (TextRank)**: {textrank_keywords}")
            if len(juridic_keywords) > 0:
                st.markdown(
                    f"📌 **Parole chiave (diritto penitenziario)**: {juridic_keywords}"
                )
            if len(juridic_concepts) > 0:
                st.markdown(
                    f"📌 **Concetti giuridici (diritto penitenziario)**: {juridic_concepts}"
                )
            with st.expander("Leggi tutto"):
                st.markdown(hit["content"], unsafe_allow_html=True)
        st.divider()


def __heading(num_hits: int) -> None:
    st.title("Database della Giurisprudenza di Merito")
    st.metric("Documenti trovati", num_hits)


def main() -> None:
    st.set_page_config(
        page_title="Database della Giurisprudenza di Merito",
        page_icon="⚖️",
        layout="wide",
    )
    if not check_authentication():
        st.error("Questa pagina è accedibile solo dagli utenti registrati")
        return
    # Fetches keywords and concepts from the network and/or the net
    keywords, concepts = __fetch_keywords_concepts()
    if keywords is None:
        return
    # Gets selected keywords and concept, if any
    selected_keywords = st.session_state.get("selected_keywords", [])
    selected_keywords = [kw for kw in selected_keywords if kw in keywords]
    selected_concepts = st.session_state.get("selected_concepts", [])
    selected_concepts = [cp for cp in selected_concepts if cp in concepts]
    # Displays search controls on the sidebar
    with st.sidebar:
        text = st.text_input(label="Testo Libero")
        selected_keywords = st.multiselect(
            label="Parole chiave", options=keywords, default=selected_keywords
        )
        selected_concepts = st.multiselect(
            label="Concetti giuridici", options=concepts, default=selected_concepts
        )
        start_date, end_date = st.date_input(
            label="Intervallo temporale",
            value=(date(year=1900, month=1, day=1), date.today()),
        )
        institution = st.selectbox(label="Istituzione", options=INSTITUTIONS)
        is_court = institution == "Tribunale di Sorveglianza"
        courts = st.multiselect(
            label="Luogo",
            options=COURTS if is_court else OFFICES,
        )
        measures = st.multiselect(
            label="Provvedimento",
            options=COURT_MEASURE_TYPES if is_court else OFFICE_MEASURE_TYPES,
        )
        outcome: List[str] = st.multiselect(
            label="Esito",
            options=["Concesse", "Rigettate"],
            default=["Concesse", "Rigettate"],
        )
    st.session_state["selected_keywords"] = selected_keywords
    st.session_state["selected_concepts"] = selected_concepts
    # Performs the query to the search engine
    try:
        aggregations, hits, keywords, concepts, num_hits = perform_query(
            text=text,
            keywords=selected_keywords,
            concepts=selected_concepts,
            institution=institution,
            courts=courts,
            measures=measures,
            outcome=outcome,
            start_date=start_date,
            end_date=end_date,
        )
        # Saves keywords and concepts in the session for later use
        __set_keywords_concepts(keywords, concepts)
    except ValueError as e:
        st.error("Impossibile eseguire la query.")
        st.error(str(e))
        return
    # If there are no results stops
    if len(aggregations) == 0:
        st.info("La ricerca non ha prodotto risultati")
        return
    # Displays the heading
    __heading(num_hits)
    # Displays two tabs, one for dashboard and one for search engine
    tab_maps, tab_hits = st.tabs(["🗺️ Mappa", "🔍 Elenco"])
    with tab_maps:
        __display_aggregations(aggregations, is_court)
    with tab_hits:
        __display_hits(hits, is_court)


if __name__ == "__main__":
    main()
