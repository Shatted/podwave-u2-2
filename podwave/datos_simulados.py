"""
Datos simulados de PodWave — estructuras de Python (Unidad 1).

La Unidad 1 exige demostrar el comportamiento de la aplicación con DATOS
SIMULADOS EN MEMORIA mediante estructuras de Python (listas, diccionarios,
tuplas), sin depender de una base de datos. Este módulo es la fuente única
de esos datos:

  - PISTAS_DEMO: lista de diccionarios con el catálogo de demostración.
  - GENEROS_SUGERIDOS: lista de tuplas (valor, etiqueta) para el filtro de
    la biblioteca y las sugerencias del formulario.
  - resumen_por_genero(): función que recorre la lista con iteraciones y
    decisiones y devuelve un diccionario con estadísticas por género.
  - pista_aleatoria(): demostración de manejo de excepciones (índices
    inválidos) y operaciones sobre la estructura.

En la evolución del proyecto hacia la Unidad 2, seed_demo.py toma estas
mismas estructuras para poblar la base de datos con el ORM: los datos
simulados de la UA1 se convierten así en los registros reales de la UA2.
El filtro por género de la biblioteca (TrackListView) también se construye
a partir de GENEROS_SUGERIDOS y viaja a la plantilla mediante el contexto
de la View, tal como exige la separación MVT.
"""
import random

# Géneros sugeridos del catálogo (lista de tuplas: valor, etiqueta).
GENEROS_SUGERIDOS = [
    ('Tecnología', 'Tecnología'),
    ('Historia', 'Historia'),
    ('Música', 'Música'),
    ('Noticias', 'Noticias'),
    ('Educación', 'Educación'),
    ('Entretenimiento', 'Entretenimiento'),
    ('Ciencia', 'Ciencia'),
    ('Deportes', 'Deportes'),
]

# Catálogo de demostración (lista de diccionarios): equivale a los "datos
# de prueba sugeridos" de la SPA original y alimenta la BD vía seed_demo.py.
PISTAS_DEMO = [
    {
        'title': 'Lo-fi Beats to Study',
        'artist': 'Chillhop Music',
        'genre': 'Música',
        'filename': 'SoundHelix-Song-1.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
    },
    {
        'title': 'Historia de la Computación — Ep. 3',
        'artist': 'Tech & Café Podcast',
        'genre': 'Tecnología',
        'filename': 'SoundHelix-Song-2.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
    },
    {
        'title': 'Misterios del Universo — Ep. 12',
        'artist': 'Ciencia al Día',
        'genre': 'Ciencia',
        'filename': 'SoundHelix-Song-3.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
    },
    {
        'title': 'Grandes Batallas de la Historia',
        'artist': 'Pasado Presente',
        'genre': 'Historia',
        'filename': 'SoundHelix-Song-4.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
    },
    {
        'title': 'Noticias Tech de la Semana',
        'artist': 'Byte Report',
        'genre': 'Noticias',
        'filename': 'SoundHelix-Song-5.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',
    },
    {
        'title': 'Aprende Inglés Escuchando — Nivel B1',
        'artist': 'Academia Idiomas',
        'genre': 'Educación',
        'filename': 'SoundHelix-Song-6.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
    },
    {
        'title': 'Rutas gastronómicas: Santiago',
        'artist': 'Sabor Local',
        'genre': 'Entretenimiento',
        'filename': 'SoundHelix-Song-7.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3',
    },
    {
        'title': 'Fútbol analizado con datos',
        'artist': 'Zona 3-5-2',
        'genre': 'Deportes',
        'filename': 'SoundHelix-Song-8.mp3',
        'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3',
    },
]


# Listas de reproducción de demostración (Unidad 2): estructura de Python
# que el comando seed_demo transforma en filas de Playlist y PlaylistTrack
# (relación N:M con campo "order"). Los títulos referencian PISTAS_DEMO.
LISTAS_DEMO = [
    {
        'name': 'Estudiar sin distracciones',
        'description': 'Beats lo-fi, ciencia e inglés para concentrarse.',
        'tracks': [
            'Lo-fi Beats to Study',
            'Misterios del Universo — Ep. 12',
            'Aprende Inglés Escuchando — Nivel B1',
        ],
    },
    {
        'name': 'Mantenerse informado',
        'description': 'Actualidad tecnológica y noticias de la semana.',
        'tracks': [
            'Historia de la Computación — Ep. 3',
            'Noticias Tech de la Semana',
        ],
    },
    {
        'name': 'Sobremesa del fin de semana',
        'description': 'Historia, gastronomía y fútbol para compartir.',
        'tracks': [
            'Grandes Batallas de la Historia',
            'Rutas gastronómicas: Santiago',
            'Fútbol analizado con datos',
        ],
    },
]


def resumen_por_genero(pistas):
    """
    Recorre la lista de pistas (iteración) y acumula un contador por género
    (diccionario). Devuelve una lista de tuplas ordenada de mayor a menor
    cantidad, lista para renderizar en una plantilla.
    """
    conteo = {}  # diccionario: género -> cantidad de pistas
    for pista in pistas:                      # iteración
        genero = pista.get('genre', 'Sin género')
        if genero in conteo:                  # decisión
            conteo[genero] += 1               # operación
        else:
            conteo[genero] = 1
    # Orden descendente por cantidad; empates por orden alfabético.
    return sorted(conteo.items(), key=lambda par: (-par[1], par[0]))


def pista_aleatoria(pistas=None):
    """
    Devuelve una pista al azar del catálogo simulado.
    Demuestra manejo de excepciones: si la lista está vacía se levanta
    IndexError y se devuelve un diccionario vacío con un mensaje.
    """
    if pistas is None:
        pistas = PISTAS_DEMO
    try:
        return random.choice(pistas)
    except IndexError:        # lista vacía: nada que elegir
        return {
            'title': 'Sin pistas disponibles',
            'artist': '—',
            'genre': '—',
            'filename': '',
            'url': '',
        }


def pistas_de_genero(pistas, genero):
    """Filtra la lista por género (comprensión de listas + decisión)."""
    objetivo = (genero or '').strip().lower()
    if not objetivo:
        return list(pistas)
    return [p for p in pistas if p.get('genre', '').lower() == objetivo]
