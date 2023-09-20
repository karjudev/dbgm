from datetime import datetime
from typing import List, Dict, Tuple

import streamlit as st
from streamlit_text_label import label_select, Selection
from streamlit.runtime.uploaded_file_manager import UploadedFile
from annotated_text import annotated_text

from auth import check_authentication, check_roles
from services.parser import parse_document
from services.anonymizer import (
    predict_annotations,
    correct_annotations,
    delete_document,
)
from services.search_engine import send_ordinance
from services.selections import (
    json_to_selections,
    selections_to_json,
    selections_to_annotated_text,
)

from constants import (
    COURTS,
    INSTITUTIONS,
    COURT_MEASURE_TYPES,
    OFFICE_MEASURE_TYPES,
    OFFICES,
    OUTCOME_TYPES,
)

# Accepted file extensions
FILE_EXTENSIONS: List[str] = ["doc", "docx", "odt", "rtf", "pdf", "txt"]

# Labels used to annotate
# LABELS: List[str] = ["LOC", "MISC", "ORG", "PER", "TIME"]
LABELS = ["LOC", "ORG", "PER", "TIME", "MISC"]


def _measures_selector(is_court: bool) -> bool:
    # List of results, saved in the session
    results: List[Dict[str, str]] = st.session_state.get("results", [])

    # Functions to add and remove data from the list
    def add_measure(m: str, o: str):
        results.append({"measure": m, "outcome": o})

    def remove_measure(index: int):
        del results[index]

    # Creates three columns to display data
    left_column, center_column, right_column = st.columns(3)
    # Displays the data entry controls
    with left_column:
        measure: str = st.selectbox(
            "Misura", options=COURT_MEASURE_TYPES if is_court else OFFICE_MEASURE_TYPES
        )
    with center_column:
        outcome: str = st.selectbox("Risultato", options=OUTCOME_TYPES)
    with right_column:
        st.button("Aggiungi", on_click=add_measure, args=(measure, outcome))
    # Displays the entries and a button to delete them
    for i, entry in enumerate(results):
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown(f"**{entry['measure']}** - {entry['outcome']}")
        with right_column:
            st.button("Rimuovi", key=i, on_click=remove_measure, args=(i,))
    st.session_state["results"] = results
    return len(results) > 0


def _upload_document(
    username: str,
    filename: str,
    institution: str,
    court: str,
    text: str,
    predicted: List[Dict],
    ground_truth: List[Dict],
    measures: List[Dict],
    publication_date: datetime,
) -> str:
    # Uploads the document to the anonymization service
    try:
        doc_id: str = correct_annotations(
            username, filename, text, predicted, ground_truth
        )
    except ValueError as e:
        st.error(
            "Impossibile caricare il documento nel servizio di anonimizzazione.\n\nIl file potrebbe essere un duplicato."
        )
        st.error(str(e))
        return None
    try:
        send_ordinance(
            doc_id,
            username,
            filename,
            institution,
            court,
            text,
            ground_truth,
            measures,
            publication_date,
        )
    except ValueError as e:
        st.error(
            "Impossibile caricare l'ordinanza nel motore di ricerca.\n\nIl file potrebbe essere un duplicato."
        )
        st.error(str(e))
        try:
            delete_document(doc_id)
        except ValueError as e:
            st.error(
                "Non è stato possibile cancellare il documento dal servizio di anonimizzazione.\nIl sistema potrebbe trovarsi in uno stato inconsistente."
            )
            st.error(str(e))
        return None
    return doc_id


def ingest_ordinance() -> None:
    st.set_page_config(
        page_title="Carica una Nuova Ordinanza",
        page_icon="⚖️",
        layout="wide",
    )
    if not check_authentication():
        st.error("Questa pagina è accessibile solo dagli utenti registrati.")
        return
    if not check_roles(["submitter", "judge"]):
        st.error("Non sei abilitato a caricare una ordinanza.")
        return
    # Used to guarantee that the \n and \t are correctly handled
    st.markdown(
        "<style> .stMarkdown>* {white-space: pre-wrap; text-align: justify; font-family: monospace;} </style>",
        unsafe_allow_html=True,
    )
    st.title("Carica una nuova ordinanza")
    uploaded_file: UploadedFile = st.file_uploader(
        "Carica un'ordinanza trascinando il file nella casella grigia.",
        type=FILE_EXTENSIONS,
        help="Carica un documento di testo, es. PDF, DOC, DOCX, RTF, TXT",
    )
    # If no file is uploaded exits
    if not uploaded_file:
        st.info("Carica un'ordinanza per poterla annotare automaticamente.")
        return
    # Reads the filename
    filename: str = uploaded_file.name
    # Reads the username
    username: str = st.session_state["username"]
    # Reads the institution, the court and the date
    col_institution, col_court, col_date = st.columns(3)
    with col_institution:
        institution: str = st.selectbox("Istituzione", options=INSTITUTIONS)
    # Flag that signals if the institution is a court or an office
    is_court = institution == "Tribunale di Sorveglianza"
    with col_court:
        court: str = st.selectbox("Luogo", options=COURTS if is_court else OFFICES)
    with col_date:
        publication_date: datetime = st.date_input("Data")
    # Reads the file's content in normalized text form
    content: str = parse_document(uploaded_file)
    # Predicts the selections with the machine learning annotator
    try:
        predicted_annotations = predict_annotations(content)
        predicted_selections = json_to_selections(predicted_annotations, content)
    except ValueError:
        st.error(
            "Non è stato possibile eseguire l'annotazione automatica. Il documento potrebbe essere in un formato non valido."
        )
        return
    # Displays the content in the annotator
    st.info(
        "- Per eseguire una nuova annotazione, clicca l'etichetta nel menu in alto e seleziona con il mouse "
        "il testo da annotare.\n"
        "- Per cancellare un'annotazione, cliccaci sopra con il mouse e premi *'Cancella'* (*'Delete'*).\n"
        "- Per confermare le annotazioni eseguite, premi il pulsante *'Update'*."
    )
    corrected_selections: List[Selection] = label_select(
        body=content,
        labels=LABELS,
        selections=predicted_selections,
    )
    if not corrected_selections:
        st.info("Per caricare le annotazioni premi il pulsante *'Update'*.")
        return
    # Previews the document to the user
    st.subheader("Il documento avrà questo aspetto:")
    st.info(
        "Puoi ancora modificare le annotazioni. Per aggiornare l'anteprima, premi il pulsante *'Update'*."
    )
    redact: bool = st.checkbox("Ometti le informazioni annotate")
    annotations: List[str | Tuple[str]] = selections_to_annotated_text(
        content, corrected_selections, redact=redact
    )
    annotated_text(*annotations)
    # Collects type of measure and outcome
    st.header("Tipi di provvedimento")
    selected: bool = _measures_selector(is_court)
    if not selected:
        st.warning("Seleziona almeno un tipo di provvedimento e un risultato")
        return
    # Prompts the user to send the annotated ordinance to the back-ends
    st.warning("Quando l'ordinanza è pronta, inviala premendo il pulsante *'Invia'*.")
    confirm = st.button("Invia")
    if not confirm:
        return
    measures: List[Dict[str, str]] = st.session_state["results"]
    # Converts the selections to JSON
    corrected_annotations = selections_to_json(content, corrected_selections)
    # Sends the corrected selections to the anonymization and search engines
    doc_id: str = _upload_document(
        username,
        filename,
        institution,
        court,
        content,
        predicted_annotations,
        corrected_annotations,
        measures,
        publication_date,
    )
    if doc_id is not None:
        del st.session_state["results"]
        st.success(f"Ordinanza caricata con successo. Il suo identificativo è {doc_id}")


if __name__ == "__main__":
    ingest_ordinance()
