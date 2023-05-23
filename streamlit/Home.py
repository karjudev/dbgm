import streamlit as st
from streamlit_folium import st_folium
from auth import check_authentication
from services.search_engine import (
    get_summary,
    get_significant_keywords,
    get_stats,
    perform_query,
)
from services.visualization import (
    HEIGHT,
    WIDTH,
    build_map,
    build_wordcloud,
    draw_wordcloud,
    get_court_information,
)
from constants import (
    COURT_MEASURE_TYPES,
    COURTS,
    INSTITUTIONS,
    OFFICE_MEASURE_TYPES,
    OFFICES,
    OUTCOME_TYPES,
)


def __dashboard():
    # Downloads summary of court data
    try:
        summary = get_summary()
    except ValueError as e:
        st.error("Impossibile scaricare i dati della mappa.")
        st.error(str(e))
        return
    # Downloads frequencies of juridic keywords
    try:
        keywords = get_significant_keywords()
    except ValueError as e:
        st.error("Impossibile scaricare le Word Cloud")
        st.error(str(e))
        return
    # Map of Italy
    col_map, col_stats = st.columns(2)
    with col_map:
        map = build_map(summary)
        data = st_folium(map, width=WIDTH, height=HEIGHT)
    # Last clicked tooltip is the one we show on the right-hand panel
    selected_court = data.get("last_object_clicked_tooltip")
    # Fetches the informations for the court
    court_data = get_court_information(summary, selected_court)
    # Creates the word cloud for the court
    court_wordcloud = build_wordcloud(keywords, selected_court)
    with col_stats:
        if court_data is None:
            st.info(
                "Clicca su un tribunale per visualizzare le informazioni associate."
            )
        else:
            st.subheader(selected_court)
            st.dataframe(court_data, use_container_width=True)
        if court_wordcloud is not None:
            st.subheader("Parole chiave significative")
            fig = draw_wordcloud(court_wordcloud)
            st.pyplot(fig)


def __search_engine() -> None:
    # Search bar and filters
    col_search, col_institution, col_court, col_measures, col_outcome = st.columns(5)
    with col_search:
        text = st.text_input(label="Parole chiave")
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
        hits = perform_query(text, institution, courts, measures, outcomes)
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
            st.header(f"📃 {hit['institution']} di {hit['court']} - {hit['timestamp']}")
            col_preview, col_stats = st.columns([2, 1])
            with col_preview:
                st.write(hit["highlight"], unsafe_allow_html=True)
            with col_stats:
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
    # Search engine statistics
    try:
        count, courts = get_stats()
    except ValueError as e:
        st.error("Impossibile scaricare le statistiche sulla piattaforma.")
        st.error(str(e))
        return
    col_count, col_courts = st.columns(2)
    with col_count:
        st.metric("Documenti indicizzati", count)
    with col_courts:
        st.metric("Tribunali di Sorveglianza", courts)
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
