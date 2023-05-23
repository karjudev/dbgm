from typing import List, Mapping, Tuple

# Possible institutions
INSTITUTIONS: List[str] = ["Tribunale di Sorveglianza", "Ufficio di Sorveglianza"]


# Possible measure types
COURT_MEASURE_TYPES: List[str] = [
    "Affidamento in prova al servizio sociale (art. 47 l. Ord. Pen.)",
    "Affidamento terapeutico (art. 94 D.P.R. 309/1990)",
    "Detenzione domiciliare (art. 47 ter e 47 quater l. Ord. Pen.)",
    "Detenzione domiciliare speciale (art. 47 quinquies l. Ord. Pen.)",
    "Semilibertà (artt. 48 e ss. l. Ord. Pen.)",
    "Liberazione condizionale (art. 176 C.P.)",
    "Rinvio dell'Esecuzione (artt. 146 e 147 c.p., 684 c.p.p.)",
    "Appelli su Misure di Sicurezza (art. 680 c.p.p.)",
    "Accertamento della Collaborazione con la Giustizia (art. 58 ter o.p.)",
    "Opposizione all'Espulsione (art. 16 D. Lgs. 286/1998)",
    "Revoca di un Provvedimento",
    "Altro",
]
OFFICE_MEASURE_TYPES: List[str] = [
    "Approvazione del programma di trattamento (art. 69 co. 5° o.p.)",
    "Ammissione al lavoro all'esterno (artt. 21 co. 4° e 69 co. 5° o.p.)",
    "Permesso di necessità (art. 30 o.p.)",
    "Permesso premio (artt. 30-ter e 30-quater o.p.)",
    "Reclamo giurisdizionale (artt. 69 co. 6° lett. b) e 35-bis o.p.)",
    "Rimedio compensativo/risarcitorio per trattamento inumano e degradante (art. 35-ter o.p.)",
    "Reclamo in ambito disciplinare (artt. 69 co. 6° lett a) e art. 35-bis o.p.)",
    "Applicazione provvisoria di misure alternative (art. 47 co. 4° o.p.)",
    "Liberazione anticipata (art. 69-bis o.p.)",
    "Sospensione cautelativa delle misure alternative (art.51-ter o.p.)",
    "Misure di sicurezza: applicazione, trasformazione e revoca (artt. 69 co. 4° o.p. e 679 c.p.p.)",
    "Rinvio/sospensione in via provvisoria dell’esecuzione nei casi degli artt. 146-147 c.p. (art.684 co.2° c.p.p.",
    "Rinvio/sospensione dell’esecuzione per sopravvenuta infermità psichica (art. 148 c.p.)",
    "Esecuzione in detenzione (l. 199/2010)",
    "Espulsione a titolo di misura alternativa (art. 16 co. 5° d.lsgl. 286/1998",
]


# Names and coordinates of the courts and offices
COURT_PLACES: Mapping[str, Tuple[float, float]] = {
    "Bologna": (44.49127098761863, 11.342363226196898),
    "Firenze": (43.79600084533369, 11.225716999186927),
    "Firenze - Minorile": (43.775703898691916, 11.245387056858691),
    "Genova": (44.40783114436098, 8.937426355029931),
    "Perugia": (43.109972556572274, 12.389705112138815),
}
OFFICE_PLACES: Mapping[str, Tuple[float, float]] = {
    "Bologna": (44.49127098761863, 11.342363226196898),
    "Firenze": (43.79600084533369, 11.225716999186927),
    "Firenze - Minorile": (43.775703898691916, 11.245387056858691),
    "Livorno": (43.5556413, 10.3061561),
    "Modena": (44.6461092, 10.9248039),
    "Perugia": (43.109972556572274, 12.389705112138815),
    "Pisa": (43.7147902, 10.4007644),
    "Reggio Emilia": (41.6037701, 10.2483079),
    "Siena": (43.3239106, 11.0212403),
    "Spoleto": (42.7386715, 12.7330119),
}


# All the "Tribunale di Sorveglianza" and "Ufficio di Sorveglianza" in Italy
COURTS: List[str] = COURT_PLACES.keys()
OFFICES: List[str] = OFFICE_PLACES.keys()


# Possible outcomes
OUTCOME_TYPES: List[str] = ["Concessa", "Rigettata"]
