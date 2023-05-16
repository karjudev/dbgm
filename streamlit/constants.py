from typing import List, Mapping, Tuple


# Possible measure types
MEASURE_TYPES: List[str] = [
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


# Names and coordinates of the courts
COURTS: Mapping[str, Tuple[float, float]] = {
    "Bologna": (44.49127098761863, 11.342363226196898),
    "Firenze": (43.79600084533369, 11.225716999186927),
    "Firenze - Minorile": (43.775703898691916, 11.245387056858691),
    "Genova": (44.40783114436098, 8.937426355029931),
    "Perugia": (43.109972556572274, 12.389705112138815),
}
