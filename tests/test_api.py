"""
Tests automatiques du projet (pytest) — sans lancer le serveur.

Le client de test de Flask simule des appels HTTP directement en Python.

Lancement (terminal ouvert dans le dossier projet-gastronomie-tn, venv activé) :
    python -m pytest -v
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "src" / "api"))

from app import GRAPHE_INFERE, GRAPHE_INITIAL, app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return app.test_client()


# (URL, code HTTP attendu, nombre de résultats attendu ou None)
CAS = [
    ("/", 200, None),
    # Q3 : 14 plats grâce à l'inférence, 0 sans
    ("/api/plats", 200, 14),
    ("/api/plats?inference=false", 200, 0),
    ("/api/plats?categorie=Dessert", 200, 3),       # Assida + 2 pâtisseries
    ("/api/plats?categorie=Entree", 200, 4),        # Brik, Méchouia + 2 soupes
    ("/api/plats?categorie=Pizza", 400, None),
    ("/api/plats?inference=peut-etre", 400, None),
    # Détail
    ("/api/plats/Ojja", 200, None),
    ("/api/plats/Inexistant", 404, None),
    ("/api/plats/Ojja%20x", 400, None),
    # Q2
    ("/api/plats/vegetariens", 200, 4),
    ("/api/plats/vegetariens?max_temps=30", 200, 1),
    ("/api/plats/vegetariens?max_temps=abc", 400, None),
    # Q8
    ("/api/plats/sans-chef", 200, 6),
    # Q6 : l'Ojja n'apparaît qu'avec l'inférence
    ("/api/ingredients/Oeuf/plats", 200, 4),
    ("/api/ingredients/Oeuf/plats?inference=false", 200, 3),
    ("/api/ingredients/Harissa/plats", 200, 7),
    ("/api/ingredients/Sfax/plats", 404, None),     # Sfax est une région
    # Q7
    ("/api/ingredients/frequents", 200, 12),
    ("/api/ingredients/frequents?inference=false", 200, 7),
    ("/api/ingredients/frequents?min=5", 200, 3),
    ("/api/ingredients/frequents?min=0", 400, None),
    # Q4
    ("/api/regions/stats", 200, 5),
    # Q5 : chefs typés gt:Chef uniquement grâce à l'inférence
    ("/api/chefs", 200, 4),
    ("/api/chefs?inference=false", 200, 0),
    # Comparaison et erreurs générales
    ("/api/inference/comparaison", 200, None),
    ("/api/route-inconnue", 404, None),
]


@pytest.mark.parametrize("url, code, nombre", CAS)
def test_endpoint(client, url, code, nombre):
    r = client.get(url)
    assert r.status_code == code
    assert r.is_json
    if nombre is not None:
        assert r.get_json()["nombre"] == nombre


def test_methode_interdite(client):
    r = client.post("/api/plats")
    assert r.status_code == 405
    assert r.get_json()["erreur"]["code"] == 405


def test_detail_ojja(client):
    corps = client.get("/api/plats/Ojja").get_json()
    assert corps["nom"] == "Ojja merguez"
    assert corps["ingredientPrincipal"] == "Œuf"
    assert sorted(corps["epices"]) == ["Carvi (karouia)", "Harissa"]
    assert [c["id"] for c in corps["chefs"]] == ["HediJaziri"]


def test_inference_ne_perd_aucun_triplet():
    assert set(GRAPHE_INITIAL) <= set(GRAPHE_INFERE)
    assert len(GRAPHE_INITIAL) == 401
    assert len(GRAPHE_INFERE) == 481


def test_comparaison(client):
    corps = client.get("/api/inference/comparaison").get_json()
    resume = {r["requete"]: (r["sansInference"], r["avecInference"]) for r in corps["requetes"]}
    assert resume == {"Q1": (7, 7), "Q2": (4, 4), "Q3": (0, 14), "Q4": (5, 5),
                      "Q5": (0, 4), "Q6": (3, 4), "Q7": (7, 12), "Q8": (6, 6)}


def test_swagger(client):
    assert client.get("/docs/").status_code == 200
    r = client.get("/openapi.yaml")
    assert r.status_code == 200
    assert b"openapi: 3.0.3" in r.data


def test_openapi_documente_toutes_les_routes():
    """Chaque route /api/... de Flask doit être décrite dans openapi.yaml, et inversement."""
    import yaml
    spec = yaml.safe_load((RACINE / "src" / "api" / "openapi.yaml").read_text(encoding="utf-8"))
    documentees = set(spec["paths"])
    routes = {str(r.rule).replace("<identifiant>", "{id}")
              for r in app.url_map.iter_rules() if str(r.rule).startswith("/api/")}
    assert routes == documentees
