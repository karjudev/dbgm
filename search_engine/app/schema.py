from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class MeasureType(Enum):
    """Type of possible measure."""

    AFF_PRO = "Affidamento in prova al servizio sociale (art. 47 l. Ord. Pen.)"
    AFF_TER = "Affidamento terapeutico (art. 94 D.P.R. 309/1990)"
    DET_DOM = "Detenzione domiciliare (art. 47 ter e 47 quater l. Ord. Pen.)"
    DET_SPE = "Detenzione domiciliare speciale (art. 47 quinquies l. Ord. Pen.)"
    SEM_LIB = "Semilibertà (artt. 48 e ss. l. Ord. Pen.)"
    LIB_CON = "Liberazione condizionale (art. 176 C.P.)"
    RIN_ESE = "Rinvio dell'Esecuzione (artt. 146 e 147 c.p., 684 c.p.p.)"
    APP_MIS = "Appelli su Misure di Sicurezza (art. 680 c.p.p.)"
    ACC_COL = "Accertamento della Collaborazione con la Giustizia (art. 58 ter o.p.)"
    OPP_ESP = "Opposizione all'Espulsione (art. 16 D. Lgs. 286/1998)"
    REV_PRO = "Revoca di un Provvedimento"
    OTHER = "Altro"


class OutcomeType(Enum):
    """Type of outcom of a measure."""

    CON = "Concessa"
    REJ = "Rigettata"


class MeasureEntry(BaseModel):
    """Tuple of a measure and its outcome."""

    measure: MeasureType
    outcome: OutcomeType


class InstitutionType(Enum):
    """Institution that delivered the ordinance."""

    COURT = "Tribunale di Sorveglianza"
    OFFICE = "Ufficio di Sorveglianza"


class Ordinance(BaseModel):
    """Anonymized ordinance."""

    filename: str
    username: str
    institution: InstitutionType
    court: str
    content: str
    measures: List[MeasureEntry]
    timestamp: Optional[int | str]


class Statistics(BaseModel):
    """Statistics about the ordinances in the documents."""

    count: int
    courts: int


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
    timestamp: str
