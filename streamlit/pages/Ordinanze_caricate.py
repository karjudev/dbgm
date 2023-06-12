from datetime import date
from typing import Dict, List

import streamlit as st
from auth import check_authentication, check_roles
from services.anonymizer import delete_document
from services.search_engine import (
    delete_ordinance,
    edit_publication_date,
    list_ordinances_user,
)


def _remove_document(doc_id: str) -> None:
    """Removes a document from the server.

    Args:
        doc_id (str): Document ID.
    """
    try:
        delete_document(doc_id)
    except ValueError as e:
        st.error("Documento non trovato nel servizio di anonimizzazione.")
        st.error(str(e))
        return
    try:
        delete_ordinance(doc_id)
    except ValueError as e:
        st.error("Documento non trovato nel motore di ricerca.")
        st.error(str(e))
        return


def _edit_date(doc_id: str, publication_date: date) -> None:
    try:
        edit_publication_date(doc_id, publication_date)
        st.success(
            f"Data del documento con ID {doc_id} aggiornata con successo con il valore {publication_date}"
        )
    except:
        st.error(f"Impossibile aggiornare la data del documento con ID {doc_id}")


def list_data_user() -> None:
    """Displays all the ordinances submitted by a user."""
    st.set_page_config(
        page_title="Ordinanze Caricate",
        page_icon="⚖️",
        layout="wide",
    )
    if not check_authentication():
        st.error("Questa pagina è accedibile solo dagli utenti registrati.")
        return
    if not check_roles(["submitter", "judge"]):
        st.error("Non sei abilitato a caricare una ordinanza.")
        return
    # Gets the username to fetch
    username: str = st.session_state["username"]
    # If available, gets the starting index
    search_from: int = st.session_state.get("search_from", 0)
    st.title("Ordinanze caricate")
    # Ordinances of the user
    try:
        ordinances: List[Dict] = list_ordinances_user(username, search_from)
    except ValueError as e:
        st.error("Impossibile scaricare la lista delle ordinanze.")
        st.error(str(e))
        return
    if len(ordinances) == 0:
        st.info("Non ci sono ordinanze da mostrare.")
    # Shows every ordinance in a container
    for i, ordinance in enumerate(ordinances):
        with st.container():
            st.subheader(
                f"`{ordinance['filename']}` - **{ordinance['institution']} di {ordinance['court']}**"
            )
            pub_date = st.date_input(
                label="Data di Pubblicazione",
                value=ordinance["publication_date"],
                key=f"date_{i}",
            )
            with st.expander(label="Testo completo"):
                st.write(ordinance["content"], unsafe_allow_html=True)
            col_update, _, col_remove = st.columns(3)
            with col_update:
                st.button(
                    "Aggiorna data",
                    key=f"update_{i}",
                    on_click=_edit_date,
                    args=(ordinance["doc_id"], pub_date),
                    type="secondary",
                )
            with col_remove:
                st.button(
                    "Rimuovi",
                    key=f"remove_{i}",
                    on_click=_remove_document,
                    args=(ordinance["doc_id"]),
                    type="primary",
                )
    # Previous and next parameters
    col_prev, _, col_next = st.columns(3)
    with col_prev:
        if st.button("⬅️ Precedente"):
            search_from = st.session_state.get("search_from", 0)
            st.session_state["search_from"] = max(0, search_from - 10)
            st.experimental_rerun()
    with col_next:
        if st.button("Successivo ➡️"):
            search_from = st.session_state.get("search_from", 0)
            st.session_state["search_from"] = search_from + 10
            st.experimental_rerun()


if __name__ == "__main__":
    list_data_user()
