from datetime import date
import streamlit as st
from streamlit_folium import st_folium
from auth import check_authentication
from services.search_engine import (
    get_count,
    perform_query,
)
from services.visualization import (
    HEIGHT,
    WIDTH,
    build_map,
    get_court_information,
)
from constants import (
    COURT_MEASURE_TYPES,
    COURT_PLACES,
    COURTS,
    INSTITUTIONS,
    OFFICE_MEASURE_TYPES,
    OFFICE_PLACES,
    OFFICES,
    OUTCOME_TYPES,
)


def __dashboard():
    # Downloads summary of court data
    col_courts, col_offices = st.columns(2)
    with col_courts:
        st.subheader("Tribunali di Sorveglianza")
        map = build_map(COURT_PLACES, "green")
        st_folium(map, width=WIDTH, height=HEIGHT)
    with col_offices:
        st.subheader("Uffici di Sorveglianza")
        map = build_map(OFFICE_PLACES, "blue")
        st_folium(map, width=WIDTH, height=HEIGHT)


def __search_engine() -> None:
    # Search bar and filters
    (
        col_search,
        col_daterange,
        col_institution,
        col_court,
        col_measures,
        col_outcome,
    ) = st.columns(6)
    with col_search:
        text = st.text_input(label="Termini della Ricerca")
    with col_daterange:
        start_date, end_date = st.date_input(
            label="Intervallo temporale",
            value=(date(year=1900, month=1, day=1), date.today()),
        )
    with col_institution:
        institution = st.selectbox(label="Istituzione", options=INSTITUTIONS)
    is_court = institution == "Tribunale di Sorveglianza"
    with col_court:
        courts = st.multiselect(
            label="Luogo",
            options=COURTS if is_court else OFFICES,
        )
    with col_measures:
        measures = st.multiselect(
            label="Provvedimento",
            options=COURT_MEASURE_TYPES if is_court else OFFICE_MEASURE_TYPES,
        )
    with col_outcome:
        outcomes = st.multiselect(
            label="Esito",
            options=OUTCOME_TYPES,
            default=OUTCOME_TYPES,
        )
    # Performs the query to the search engine
    try:
        hits = perform_query(
            text, institution, courts, measures, outcomes, start_date, end_date
        )
    except ValueError as e:
        st.error("Impossibile eseguire la query.")
        st.error(str(e))
        return
    st.markdown(
        "<style> .stMarkdown>* {white-space: pre-wrap; font-family: monospace;} </style>",
        unsafe_allow_html=True,
    )
    for hit in hits:
        dictionary_keywords = ", ".join(hit["dictionary_keywords"])
        pos_keywords = ", ".join(hit["pos_keywords"])
        ner_keywords = ", ".join(hit["ner_keywords"])
        with st.container():
            st.header(f"📃 {hit['institution']} di {hit['court']}")
            col_preview, col_stats = st.columns([2, 1])
            with col_preview:
                st.write(hit["highlight"], unsafe_allow_html=True)
            with col_stats:
                if hit["publication_date"]:
                    st.write(f"🕑 **Data di Pubblicazione**: {hit['publication_date']}")
                for measure in hit["measures"]:
                    st.write(f"🧭 **{measure['measure']}** - *{measure['outcome']}*")
            st.markdown(f"📌 **Riferimenti Normativi**: {ner_keywords}")
            st.markdown(f"📌 **Parole chiave giuridiche**: {dictionary_keywords}")
            st.markdown(f"📌 **Parole chiave**: {pos_keywords}")
            with st.expander(
                label="Clicca qui per leggere il testo completo dell'ordinanza"
            ):
                st.write(hit["content"], unsafe_allow_html=True)
        st.divider()


def main() -> None:
    st.set_page_config(
        page_title="Database della Giurisprudenza di Merito",
        page_icon="⚖️",
        layout="wide",
    )
    if not check_authentication():
        st.error("Questa pagina è accedibile solo dagli utenti registrati")
        return
    st.title("Database della Giurisprudenza di Merito")
    # Search engine number of documents
    try:
        num_docs = get_count()
    except ValueError as e:
        st.error("Impossibile scaricare le statistiche sulla piattaforma.")
        st.error(str(e))
        return
    # Number of courts
    num_courts = len(COURT_PLACES.keys())
    # Number of offices
    num_offices = len(OFFICE_PLACES.keys())
    col_count, col_courts, col_offices = st.columns(3)
    with col_count:
        st.metric("Documenti indicizzati", num_docs)
    with col_courts:
        st.metric("Tribunali di Sorveglianza", num_courts)
    with col_offices:
        st.metric("Uffici di sorveglianza", num_offices)
    # Displays two tabs, one for dashboard and one for search engine
    tab_dashboard, tab_search_engine = st.tabs(
        ["🗺️ Statistiche", "🔍 Ricerca Ordinanze"]
    )
    with tab_dashboard:
        __dashboard()
    with tab_search_engine:
        __search_engine()


if __name__ == "__main__":
    main()
