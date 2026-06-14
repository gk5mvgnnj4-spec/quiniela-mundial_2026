# -*- coding: utf-8 -*-
"""
Mapeo de equipos: nombre que devuelve API-Football  ->  código de 3 letras de la quiniela.

API-Football devuelve nombres en inglés. Aquí mapeamos cada uno a tu código.
Incluimos variantes/alias comunes para que el casado nunca falle por un nombre raro.
La llave se normaliza (minúsculas, sin acentos) antes de buscar, así que no importa
mayúsculas ni tildes.
"""

# código -> nombre bonito en español (solo para logs legibles)
NOMBRE = {
    "MEX": "México", "SUD": "Sudáfrica", "CDS": "Corea del Sur", "CHE": "Chequia",
    "CAN": "Canadá", "BOS": "Bosnia", "EUA": "EUA", "PAR": "Paraguay",
    "QAT": "Qatar", "SUI": "Suiza", "BRA": "Brasil", "MAR": "Marruecos",
    "HAI": "Haití", "ESC": "Escocia", "AUS": "Australia", "TUR": "Turquía",
    "ALE": "Alemania", "CUR": "Curazao", "HOL": "Países Bajos", "JPN": "Japón",
    "CDM": "Costa de Marfil", "ECU": "Ecuador", "SUE": "Suecia", "TUN": "Túnez",
    "ESP": "España", "CAB": "Cabo Verde", "BEL": "Bélgica", "EGP": "Egipto",
    "ARA": "Arabia Saudita", "URU": "Uruguay", "IRN": "Irán", "NZL": "Nueva Zelanda",
    "FRA": "Francia", "SEN": "Senegal", "IRK": "Irak", "NOR": "Noruega",
    "ARG": "Argentina", "ARL": "Argelia", "AUT": "Austria", "JOR": "Jordania",
    "POR": "Portugal", "CON": "RD Congo", "ING": "Inglaterra", "CRO": "Croacia",
    "GHA": "Ghana", "PAN": "Panamá", "UZB": "Uzbekistán", "COL": "Colombia",
}

# Cada alias (en minúsculas, sin acentos) -> código.
# Pon TODOS los nombres con que la API podría devolver cada selección.
_RAW_ALIASES = {
    "MEX": ["mexico"],
    "SUD": ["south africa"],
    "CDS": ["south korea", "korea republic", "korea south", "republic of korea"],
    "CHE": ["czech republic", "czechia"],
    "CAN": ["canada"],
    "BOS": ["bosnia and herzegovina", "bosnia & herzegovina", "bosnia-herzegovina", "bosnia herzegovina", "bosnia"],
    "EUA": ["usa", "united states", "united states of america"],
    "PAR": ["paraguay"],
    "QAT": ["qatar"],
    "SUI": ["switzerland"],
    "BRA": ["brazil"],
    "MAR": ["morocco"],
    "HAI": ["haiti"],
    "ESC": ["scotland"],
    "AUS": ["australia"],
    "TUR": ["turkey", "turkiye", "türkiye"],
    "ALE": ["germany"],
    "CUR": ["curacao", "curaçao"],
    "HOL": ["netherlands", "holland"],
    "JPN": ["japan"],
    "CDM": ["ivory coast", "cote d'ivoire", "côte d'ivoire", "cote divoire"],
    "ECU": ["ecuador"],
    "SUE": ["sweden"],
    "TUN": ["tunisia"],
    "ESP": ["spain"],
    "CAB": ["cape verde", "cabo verde", "cape verde islands"],
    "BEL": ["belgium"],
    "EGP": ["egypt"],
    "ARA": ["saudi arabia"],
    "URU": ["uruguay"],
    "IRN": ["iran", "ir iran", "islamic republic of iran"],
    "NZL": ["new zealand"],
    "FRA": ["france"],
    "SEN": ["senegal"],
    "IRK": ["iraq"],
    "NOR": ["norway"],
    "ARG": ["argentina"],
    "ARL": ["algeria"],
    "AUT": ["austria"],
    "JOR": ["jordan"],
    "POR": ["portugal"],
    "CON": ["congo dr", "dr congo", "democratic republic of congo", "congo democratic republic",
            "democratic republic of the congo", "dr congo (zaire)"],
    "ING": ["england"],
    "CRO": ["croatia"],
    "GHA": ["ghana"],
    "PAN": ["panama"],
    "UZB": ["uzbekistan"],
    "COL": ["colombia"],
}


def _norm(s):
    """minúsculas, sin acentos, sin espacios extra."""
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


# construye el índice alias_normalizado -> código
ALIAS = {}
for code, names in _RAW_ALIASES.items():
    ALIAS[_norm(NOMBRE[code])] = code  # el nombre español también vale
    for n in names:
        ALIAS[_norm(n)] = code


def code_for(api_name):
    """
    Devuelve el código de 3 letras para un nombre que vino de la API.
    Si no lo reconoce, devuelve None (y el script lo va a reportar en el log).
    """
    return ALIAS.get(_norm(api_name))
