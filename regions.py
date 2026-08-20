from __future__ import annotations

# Representative coordinates are analysis points, not administrative polygon centroids.
# They are used to query NASA POWER consistently. A future version can replace them
# with polygon/grid aggregation for area-weighted regional statistics.
POLISH_VOIVODESHIPS = {
    "dolnoslaskie": {"name": "Dolnośląskie", "latitude": 51.0, "longitude": 16.3},
    "kujawsko-pomorskie": {"name": "Kujawsko-Pomorskie", "latitude": 53.1, "longitude": 18.1},
    "lubelskie": {"name": "Lubelskie", "latitude": 51.2, "longitude": 22.8},
    "lubuskie": {"name": "Lubuskie", "latitude": 52.1, "longitude": 15.5},
    "lodzkie": {"name": "Łódzkie", "latitude": 51.75, "longitude": 19.5},
    "malopolskie": {"name": "Małopolskie", "latitude": 49.9, "longitude": 20.0},
    "mazowieckie": {"name": "Mazowieckie", "latitude": 52.3, "longitude": 21.0},
    "opolskie": {"name": "Opolskie", "latitude": 50.6, "longitude": 17.9},
    "podkarpackie": {"name": "Podkarpackie", "latitude": 49.9, "longitude": 22.3},
    "podlaskie": {"name": "Podlaskie", "latitude": 53.3, "longitude": 23.2},
    "pomorskie": {"name": "Pomorskie", "latitude": 54.2, "longitude": 18.3},
    "slaskie": {"name": "Śląskie", "latitude": 50.3, "longitude": 19.0},
    "swietokrzyskie": {"name": "Świętokrzyskie", "latitude": 50.8, "longitude": 20.7},
    "warminsko-mazurskie": {"name": "Warmińsko-Mazurskie", "latitude": 53.8, "longitude": 20.9},
    "wielkopolskie": {"name": "Wielkopolskie", "latitude": 52.3, "longitude": 17.2},
    "zachodniopomorskie": {"name": "Zachodniopomorskie", "latitude": 53.5, "longitude": 15.4},
}

CENTRAL_EASTERN_EUROPE = {
    "Polska": {"latitude": 52.1, "longitude": 19.4},
    "Czechy": {"latitude": 49.8, "longitude": 15.5},
    "Słowacja": {"latitude": 48.7, "longitude": 19.7},
    "Węgry": {"latitude": 47.2, "longitude": 19.5},
    "Rumunia": {"latitude": 45.9, "longitude": 24.9},
    "Bułgaria": {"latitude": 42.7, "longitude": 25.5},
    "Ukraina": {"latitude": 49.0, "longitude": 31.2},
    "Litwa": {"latitude": 55.2, "longitude": 23.9},
    "Łotwa": {"latitude": 56.9, "longitude": 24.6},
    "Estonia": {"latitude": 58.6, "longitude": 25.0},
}
