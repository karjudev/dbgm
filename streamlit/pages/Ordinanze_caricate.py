from typing import Dict, List

import streamlit as st
from auth import check_authentication, check_roles
from services.anonymizer import (
    list_documents_user,
    delete_document,
)
from services.search_engine import delete_ordinance


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
    if "selected_ordinance" in st.session_state:
        del st.session_state["selected_ordinance"]


def list_ordinances_user() -> None:
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
    username: str = st.session_state["username"]
    st.title("Ordinanze caricate")
    # Ordinances of the user
    try:
        ordinances: List[Dict] = list_documents_user(username)
    except ValueError as e:
        st.error("Impossibile scaricare la lista delle ordinanze.")
        st.error(str(e))
        return
    if len(ordinances) == 0:
        st.info("Non hai ancora caricato nessuna ordinanza.")
        return
    for i, ordinance in enumerate(ordinances):
        col_title, col_remove = st.columns(2)
        with col_title:
            st.markdown(f"**{ordinance['filename']}**")
        with col_remove:
            st.button(
                "Rimuovi",
                key=f"remove_{i}",
                on_click=_remove_document,
                args=(ordinance["doc_id"],),
                type="primary",
            )


if __name__ == "__main__":
    list_ordinances_user()
