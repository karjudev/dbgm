from datetime import date
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class InstitutionType(Enum):
    """Institution that delivered the ordinance."""

    COURT = "Tribunale di Sorveglianza"
    OFFICE = "Ufficio di Sorveglianza"


class MeasureType(Enum):
    """Type of possible measure."""

    CRT_AFF_PRO = "Affidamento in prova al servizio sociale (art. 47 l. Ord. Pen.)"
    CRT_AFF_TER = "Affidamento terapeutico (art. 94 D.P.R. 309/1990)"
    CRT_DET_DOM = "Detenzione domiciliare (art. 47 ter e 47 quater l. Ord. Pen.)"
    CRT_DET_SPE = "Detenzione domiciliare speciale (art. 47 quinquies l. Ord. Pen.)"
    CRT_SEM_LIB = "Semilibertà (artt. 48 e ss. l. Ord. Pen.)"
    CRT_LIB_CON = "Liberazione condizionale (art. 176 C.P.)"
    CRT_RIN_ESE = "Rinvio dell'Esecuzione (artt. 146 e 147 c.p., 684 c.p.p.)"
    CRT_APP_MIS = "Appelli su Misure di Sicurezza (art. 680 c.p.p.)"
    CRT_ACC_COL = (
        "Accertamento della Collaborazione con la Giustizia (art. 58 ter o.p.)"
    )
    CRT_OPP_ESP = "Opposizione all'Espulsione (art. 16 D. Lgs. 286/1998)"
    CRT_REV_PRO = "Revoca di un Provvedimento"
    OFF_APP_TRA = "Approvazione del programma di trattamento (art. 69 co. 5° o.p.)"
    OFF_AMM_LAV = "Ammissione al lavoro all'esterno (artt. 21 co. 4° e 69 co. 5° o.p.)"
    OFF_PER_NEC = "Permesso di necessità (art. 30 o.p.)"
    OFF_PER_PRE = "Permesso premio (artt. 30-ter e 30-quater o.p.)"
    OFF_REC_GIU = "Reclamo giurisdizionale (artt. 69 co. 6° lett. b) e 35-bis o.p.)"
    OFF_RIM_COM = "Rimedio compensativo/risarcitorio per trattamento inumano e degradante (art. 35-ter o.p.)"
    OFF_REC_DIS = (
        "Reclamo in ambito disciplinare (artt. 69 co. 6° lett a) e art. 35-bis o.p.)"
    )
    OFF_APP_PRO = "Applicazione provvisoria di misure alternative (art. 47 co. 4° o.p.)"
    OFF_LIB_ANT = "Liberazione anticipata (art. 69-bis o.p.)"
    OFF_SOS_CAU = "Sospensione cautelativa delle misure alternative (art.51-ter o.p.)"
    OFF_MIS_SIC = "Misure di sicurezza: applicazione, trasformazione e revoca (artt. 69 co. 4° o.p. e 679 c.p.p.)"
    OFF_RIN_ESE = "Rinvio/sospensione in via provvisoria dell’esecuzione nei casi degli artt. 146-147 c.p. (art.684 co.2° c.p.p."
    OFF_RIN_INF = "Rinvio/sospensione dell’esecuzione per sopravvenuta infermità psichica (art. 148 c.p.)"
    OFF_ESE_DET = "Esecuzione in detenzione (l. 199/2010)"
    OFF_ESP_ALT = (
        "Espulsione a titolo di misura alternativa (art. 16 co. 5° d.lsgl. 286/1998"
    )
    OTHER = "Altro"


class MeasureEntry(BaseModel):
    """Tuple of a measure and its outcome."""

    measure: MeasureType
    outcome: bool


class Ordinance(BaseModel):
    """Anonymized ordinance."""

    filename: str
    username: str
    institution: InstitutionType
    court: str
    content: str
    measures: List[MeasureEntry]
    publication_date: Optional[date]
    timestamp: Optional[int | str]


class OrdinanceEntry(Ordinance):
    doc_id: str


class QueryResponse(BaseModel):
    """Response entry to a query."""

    highlight: str
    content: str
    institution: InstitutionType
    measures: List[MeasureEntry]
    pos_keywords: List[str]
    dictionary_keywords: List[str]
    ner_keywords: List[str]
    court: str
    publication_date: Optional[date]
