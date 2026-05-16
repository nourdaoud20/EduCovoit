# cities_data.py
# Tunisian Cities and Universities Database

CITIES_AND_UNIVERSITIES = {
    "Tunis": [
        "Université de Tunis - El Manar",
        "Université de Carthage",
        "Université de Tunis",
        "ESPRIT",
        "Faculté des Sciences de Tunis",
        "École Nationale d'Ingénieurs de Tunis (ENIT)",
        "Institut Supérieur d'Informatique (ISI)",
        "Institut Supérieur de Gestion (ISG)",
        "Université Virtuelle de Tunis"
    ],
    "Ariana": [
        "Université El Manar (Campus d'Ariana)",
        "Institut Supérieur de Technologie",
        "École d'Ingénieurs Ariana",
        "Institut Supérieur d'Éducation Continue"
    ],
    "Ben Arous": [
        "Université de Carthage (Campus Ben Arous)",
        "ISET Radès",
        "Institut Supérieur des Études Technologiques de Ben Arous"
    ],
    "Manouba": [
        "Université de la Manouba",
        "Institut Supérieur de Formation Continue",
        "Faculté des Lettres et des Sciences Humaines"
    ],
    "Sfax": [
        "Université de Sfax",
        "École Nationale d'Ingénieurs de Sfax",
        "Faculté des Sciences Économiques et de Gestion",
        "Faculté de Médecine de Sfax",
        "Institut Supérieur de Biotechnologie"
    ],
    "Sousse": [
        "Université de Sousse",
        "Université de Sousse - Technopole",
        "Institut Supérieur d'Informatique et de Multimédia de Sfax",
        "École Supérieure de Commerce"
    ],
    "Gafsa": [
        "Université de Gafsa",
        "Institut Supérieur de Gafsa"
    ],
    "Kairouan": [
        "Université de Kairouan",
        "Institut Supérieur de Kairouan"
    ],
    "Kasserine": [
        "Université de Kasserine",
        "Institut Supérieur de Kasserine"
    ],
    "Nabeul": [
        "Université de Carthage (Campus Nabeul)",
        "Institut Supérieur Agricole de Chott Mariem"
    ],
    "Tataouine": [
        "Institut Supérieur de Tataouine"
    ],
    "Jendouba": [
        "Université de Jendouba",
        "Institut Supérieur de Jendouba"
    ],
    "Le Kef": [
        "Institut Supérieur de Le Kef"
    ],
    "Médenine": [
        "Institut Supérieur de Médenine"
    ],
    "Gabès": [
        "Université de Gabès",
        "Institut Supérieur de Gabès"
    ],
    "Sidi Bouzid": [
        "Institut Supérieur de Sidi Bouzid"
    ],
    "Tozeur": [
        "Institut Supérieur de Tozeur"
    ]
}

def get_cities():
    """Return list of all cities"""
    return sorted(list(CITIES_AND_UNIVERSITIES.keys()))

def get_universities_by_city(city):
    """Return list of universities for a given city"""
    return CITIES_AND_UNIVERSITIES.get(city, [])

def validate_city_university(city, university):
    """Validate if university belongs to city"""
    universities = get_universities_by_city(city)
    return university in universities
