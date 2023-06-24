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
    "Reclamo giurisdizionale (artt. 69 co. 6° lett. b) e 35-bis o.p.)",
    "Rimedio compensativo/risarcitorio per trattamento inumano e degradante (art. 35-ter o.p.)",
    "Misure di sicurezza - Applicazione (artt. 69 co. 4° o.p. e 679 c.p.p.)",
    "Misure di sicurezza - Esecuzione (artt. 69 co. 4° o.p. e 679 c.p.p.)",
    "Misure di sicurezza - Trasformazione (artt. 69 co. 4° o.p. e 679 c.p.p.)",
    "Misure di sicurezza - Revoca (artt. 69 co. 4° o.p. e 679 c.p.p.)",
]


# Names and coordinates of the courts and offices
COURT_PLACES: Mapping[str, Tuple[float, float]] = {
    "Bologna": (44.491194452642766, 11.342384683869515),
    "Firenze": (43.79649183411269, 11.225651500440986),
    "Firenze - Minorile": (43.77568833058416, 11.245215380608315),
    "Genova": (44.407938446339074, 8.937286880157929),
    "Perugia": (43.109933393984015, 12.389147212650807),
}
OFFICE_PLACES: Mapping[str, Tuple[float, float]] = {
    "Bologna": (44.491194452642766, 11.342384683869515),
    "Firenze": (43.79649183411269, 11.225651500440986),
    "Firenze - Minorile": (43.77568833058416, 11.245215380608315),
    "Genova": (44.407938446339074, 8.937286880157929),
    "Livorno": (43.5558316774945, 10.309321068396983),
    "Massa": (44.03464459654947, 10.135436953700136),
    "Modena": (44.64620181710008, 10.929833989694327),
    "Perugia": (43.109933393984015, 12.389147212650807),
    "Pisa": (43.71488718189306, 10.4035431452194),
    "Reggio Emilia": (44.94436068104855, 10.675464528818178),
    "Siena": (43.389752704941884, 11.31250754667315),
    "Spoleto": (42.735113803366126, 12.736203712859886),
}


# All the "Tribunale di Sorveglianza" and "Ufficio di Sorveglianza" in Italy
COURTS: List[str] = COURT_PLACES.keys()
OFFICES: List[str] = OFFICE_PLACES.keys()


# Possible outcomes
OUTCOME_TYPES: List[str] = ["Concessa", "Rigettata"]
