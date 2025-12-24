"""
Spanish word database for the Impostor Word Game
"""
import random
from typing import Optional

WORD_CATEGORIES = {
    "animales": [
        "elefante", "jirafa", "tigre", "delfin", "aguila", "serpiente",
        "cocodrilo", "canguro", "pingüino", "leon", "oso", "lobo",
        "zorro", "conejo", "tortuga", "ballena", "tiburon", "pulpo",
        "mariposa", "abeja", "hormiga", "araña", "caballo", "vaca",
        "cerdo", "gallina", "pato", "buho", "flamenco", "koala"
    ],
    "comida": [
        "pizza", "hamburguesa", "sushi", "tacos", "paella", "lasaña",
        "ensalada", "sopa", "helado", "chocolate", "pastel", "galleta",
        "pan", "queso", "jamon", "huevo", "arroz", "pasta",
        "pollo", "pescado", "manzana", "banana", "naranja", "fresa",
        "sandia", "uva", "limon", "zanahoria", "tomate", "cebolla"
    ],
    "objetos": [
        "telefono", "computadora", "televisor", "lampara", "silla", "mesa",
        "cama", "sofa", "espejo", "reloj", "llave", "libro",
        "lapiz", "tijeras", "paraguas", "maleta", "billetera", "gafas",
        "camara", "guitarra", "piano", "violin", "pelota", "bicicleta",
        "coche", "avion", "barco", "tren", "cohete", "globo"
    ],
    "lugares": [
        "playa", "montaña", "bosque", "desierto", "isla", "rio",
        "lago", "cascada", "volcan", "cueva", "parque", "jardin",
        "hospital", "escuela", "biblioteca", "museo", "cine", "teatro",
        "restaurante", "supermercado", "aeropuerto", "estacion", "hotel", "castillo",
        "iglesia", "estadio", "gimnasio", "piscina", "zoologico", "circo"
    ],
    "profesiones": [
        "doctor", "maestro", "bombero", "policia", "piloto", "astronauta",
        "chef", "pintor", "musico", "actor", "escritor", "fotografo",
        "arquitecto", "ingeniero", "abogado", "veterinario", "dentista", "enfermero",
        "electricista", "plomero", "carpintero", "jardinero", "agricultor", "pescador",
        "cartero", "periodista", "cientifico", "detective", "atleta", "bailarin"
    ],
    "deportes": [
        "futbol", "baloncesto", "tenis", "natacion", "atletismo", "boxeo",
        "ciclismo", "golf", "beisbol", "voleibol", "surf", "esqui",
        "patinaje", "gimnasia", "karate", "judo", "esgrima", "arqueria",
        "escalada", "buceo", "remo", "vela", "equitacion", "rugby",
        "hockey", "badminton", "ping-pong", "ajedrez", "billar", "dardos"
    ],
    "naturaleza": [
        "sol", "luna", "estrella", "nube", "lluvia", "nieve",
        "arcoiris", "tornado", "terremoto", "oceano", "mar", "ola",
        "arena", "roca", "arbol", "flor", "hoja", "raiz",
        "semilla", "fruta", "hierba", "musgo", "hongo", "cactus",
        "coral", "perla", "cristal", "diamante", "oro", "plata"
    ],
    "emociones": [
        "alegria", "tristeza", "miedo", "sorpresa", "amor", "odio",
        "esperanza", "nostalgia", "envidia", "orgullo", "verguenza", "culpa",
        "ansiedad", "calma", "emocion", "aburrimiento", "curiosidad", "confusion",
        "frustracion", "satisfaccion", "gratitud", "compasion", "admiracion", "desprecio",
        "celos", "soledad", "paz", "felicidad", "melancolia", "euforia"
    ]
}

# Flatten all words for random selection
ALL_WORDS = [word for category in WORD_CATEGORIES.values() for word in category]


def get_random_word(category: Optional[str] = None) -> str:
    """Get a random word, optionally from a specific category."""
    if category and category in WORD_CATEGORIES:
        return random.choice(WORD_CATEGORIES[category])
    return random.choice(ALL_WORDS)


def get_random_category() -> str:
    """Get a random category name."""
    return random.choice(list(WORD_CATEGORIES.keys()))


def get_word_with_category() -> tuple[str, str]:
    """Get a random word along with its category."""
    category = get_random_category()
    word = random.choice(WORD_CATEGORIES[category])
    return word, category


def is_word_match(guess: str, secret: str) -> bool:
    """Check if the guess matches the secret word (case insensitive, accent tolerant)."""
    # Normalize strings
    def normalize(s: str) -> str:
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ñ': 'n'
        }
        result = s.lower().strip()
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result

    return normalize(guess) == normalize(secret)
