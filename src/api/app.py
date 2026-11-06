"""
Partie 4 — Web Service REST (Flask) : exposition des résultats en JSON.

Au démarrage, deux graphes sont préparés UNE seule fois et gardés en mémoire :
  - le graphe initial (ontologie + données, sans inférence) ;
  - le graphe inféré (mêmes triplets + déductions RDFS de la partie 3).
Chaque appel HTTP exécute une requête du dossier queries/ sur l'un des deux
graphes (paramètre ?inference=true par défaut, ou ?inference=false) et
renvoie le résultat en JSON.

Documentation interactive (Swagger UI) : http://127.0.0.1:5000/docs
Description OpenAPI                     : http://127.0.0.1:5000/openapi.yaml

Lancement (terminal ouvert dans le dossier projet-gastronomie-tn, venv activé) :
    python src/api/app.py
"""

import re
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from rdflib import Literal
from rdflib.namespace import RDF, RDFS

# Le dossier src/ contient commun.py et inference.py : on l'ajoute au chemin Python
DOSSIER_API = Path(__file__).resolve().parent
sys.path.insert(0, str(DOSSIER_API.parent))

import sparql as q  # noqa: E402
from commun import charger_graphe  # noqa: E402
from inference import comparer_requetes, graphe_infere  # noqa: E402

# ------------------------------------------------------------------------------
# Initialisation : les deux graphes sont chargés une seule fois
# ------------------------------------------------------------------------------
sys.stdout.reconfigure(encoding="utf-8")
print("Chargement du graphe initial et inférence RDFS...")
GRAPHE_INITIAL = charger_graphe()
GRAPHE_INFERE = graphe_infere()
print(f"Graphe initial : {len(GRAPHE_INITIAL)} triplets | graphe inféré : {len(GRAPHE_INFERE)} triplets")

# Catégories autorisées = gt:Plat et toutes ses sous-classes (lues dans le schéma)
CATEGORIES = sorted(str(c)[len(q.GT):] for c in
                    GRAPHE_INFERE.transitive_subjects(RDFS.subClassOf, q.uri_classe("Plat")))

# Comparaison des 8 requêtes, calculée une fois (voir GET /api/inference/comparaison)
COMPARAISON = [
    {
        "requete": c["entete"]["titre"].split(" — ")[0],
        "fichier": f"queries/{c['fichier']}",
        "titre": c["entete"]["titre"].split(" — ", 1)[-1],
        "sansInference": len(c["lignes_avant"]),
        "avecInference": len(c["lignes_apres"]),
        "change": c["lignes_avant"] != c["lignes_apres"],
        "explication": c["entete"]["inference"],
    }
    for c in comparer_requetes(GRAPHE_INITIAL, GRAPHE_INFERE)
]

app = Flask(__name__)
app.json.ensure_ascii = False   # garder les accents et l'arabe lisibles
app.json.sort_keys = False      # garder l'ordre des champs

# Swagger UI (fichiers fournis par le paquet flask-swagger-ui : fonctionne sans internet)
app.register_blueprint(
    get_swaggerui_blueprint("/docs", "/openapi.yaml",
                            config={"app_name": "API Gastronomie tunisienne"}),
    url_prefix="/docs",
)


@app.get("/openapi.yaml")
def specification_openapi():
    return send_from_directory(DOSSIER_API, "openapi.yaml", mimetype="application/yaml")


# ------------------------------------------------------------------------------
# Gestion des erreurs : toujours une réponse JSON {"erreur": {...}}
# ------------------------------------------------------------------------------
class ErreurApi(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@app.errorhandler(ErreurApi)
def erreur_api(e):
    return jsonify(erreur={"code": e.code, "message": e.message}), e.code


@app.errorhandler(404)
def introuvable(e):
    return jsonify(erreur={"code": 404, "message": "Route inconnue. Voir GET / ou /docs."}), 404


@app.errorhandler(405)
def methode_interdite(e):
    return jsonify(erreur={"code": 405, "message": "Méthode non autorisée (seul GET est accepté)."}), 405


@app.errorhandler(500)
def erreur_interne(e):
    return jsonify(erreur={"code": 500, "message": "Erreur interne du serveur."}), 500


# ------------------------------------------------------------------------------
# Lecture et validation des paramètres
# ------------------------------------------------------------------------------
def parametre_entier(nom, defaut, minimum, maximum):
    """Lit ?nom=... dans l'URL et vérifie que c'est un entier dans [minimum, maximum]."""
    texte = request.args.get(nom, str(defaut))
    if not texte.isdigit() or not (minimum <= int(texte) <= maximum):
        raise ErreurApi(400, f"Le paramètre '{nom}' doit être un entier entre {minimum} et {maximum} "
                             f"(reçu : '{texte}').")
    return int(texte)


def graphe_choisi():
    """?inference=true (défaut) -> graphe inféré ; ?inference=false -> graphe initial."""
    texte = request.args.get("inference", "true").lower()
    if texte not in ("true", "false"):
        raise ErreurApi(400, f"Le paramètre 'inference' doit valoir true ou false (reçu : '{texte}').")
    avec = texte == "true"
    return (GRAPHE_INFERE if avec else GRAPHE_INITIAL), avec


def ressource_existante(identifiant, classe, libelle):
    """Vérifie le format de l'identifiant, puis que la ressource est du bon type.
    Le contrôle se fait sur le graphe inféré (ex. res:Harissa n'est un
    gt:Ingredient que grâce à l'inférence)."""
    if not re.fullmatch(r"[A-Za-z0-9]+", identifiant):
        raise ErreurApi(400, f"Identifiant invalide : '{identifiant}' (lettres et chiffres uniquement).")
    uri = q.uri_ressource(identifiant)
    if (uri, RDF.type, q.uri_classe(classe)) not in GRAPHE_INFERE:
        raise ErreurApi(404, f"{libelle} '{identifiant}' introuvable.")
    return uri


def reponse_liste(requete, inference, resultats, **parametres):
    """Format commun des listes : requête utilisée, paramètres, nombre, résultats."""
    corps = {"requete": f"queries/{requete}.rq", "inference": inference}
    if parametres:
        corps["parametres"] = parametres
    corps["nombre"] = len(resultats)
    corps["resultats"] = resultats
    return jsonify(corps)


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@app.get("/")
def accueil():
    return jsonify(
        service="API Gastronomie tunisienne (RDF + RDFS + SPARQL + inférence)",
        documentation="/docs",
        triplets={"sansInference": len(GRAPHE_INITIAL), "avecInference": len(GRAPHE_INFERE)},
        endpoints={
            "GET /api/plats": "Catalogue des plats (Q3), filtre ?categorie=",
            "GET /api/plats/{id}": "Détail d'un plat (ex. /api/plats/Ojja)",
            "GET /api/plats/vegetariens": "Plats végétariens rapides (Q2), ?max_temps=",
            "GET /api/plats/sans-chef": "Plats sans chef associé (Q8)",
            "GET /api/ingredients/{id}/plats": "Plats contenant un ingrédient (Q6)",
            "GET /api/ingredients/frequents": "Ingrédients fréquents (Q7), ?min=",
            "GET /api/regions/stats": "Statistiques par région (Q4)",
            "GET /api/chefs": "Chefs et spécialités (Q5)",
            "GET /api/inference/comparaison": "Nombre de résultats des 8 requêtes sans / avec inférence",
        },
        parametreCommun="?inference=true (défaut) ou ?inference=false",
    )


@app.get("/api/plats")
def liste_plats():
    graphe, inference = graphe_choisi()
    categorie = request.args.get("categorie", "Plat")
    if categorie not in CATEGORIES:
        raise ErreurApi(400, f"Catégorie inconnue : '{categorie}'. Valeurs possibles : {CATEGORIES}.")
    resultats = q.interroger(graphe, "q3_tous_les_plats", classe=q.uri_classe(categorie))
    return reponse_liste("q3_tous_les_plats", inference, resultats, categorie=categorie)


@app.get("/api/plats/vegetariens")
def plats_vegetariens():
    graphe, inference = graphe_choisi()
    max_temps = parametre_entier("max_temps", defaut=45, minimum=1, maximum=1000)
    resultats = q.interroger(graphe, "q2_vegetariens_rapides", max=Literal(max_temps))
    return reponse_liste("q2_vegetariens_rapides", inference, resultats, max_temps=max_temps)


@app.get("/api/plats/sans-chef")
def plats_sans_chef():
    graphe, inference = graphe_choisi()
    return reponse_liste("q8_plats_sans_chef", inference, q.interroger(graphe, "q8_plats_sans_chef"))


@app.get("/api/plats/<identifiant>")
def detail_plat(identifiant):
    graphe, inference = graphe_choisi()
    plat = ressource_existante(identifiant, "Plat", "Plat")
    infos = q.interroger(graphe, "api/detail_plat", plat=plat)[0]
    ingredients = q.interroger(graphe, "api/ingredients_plat", plat=plat)
    chefs = q.interroger(graphe, "api/chefs_plat", plat=plat)
    return jsonify(
        id=identifiant,
        inference=inference,
        **infos,
        ingredientPrincipal=next((i["nom"] for i in ingredients if i["estPrincipal"]), None),
        epices=[i["nom"] for i in ingredients if i["estEpice"]],
        ingredients=[{"id": i["ingredient"], "nom": i["nom"]} for i in ingredients],
        chefs=[{"id": c["chef"], "nom": c["nom"]} for c in chefs],
    )


@app.get("/api/ingredients/<identifiant>/plats")
def plats_par_ingredient(identifiant):
    graphe, inference = graphe_choisi()
    ingredient = ressource_existante(identifiant, "Ingredient", "Ingrédient")
    resultats = q.interroger(graphe, "q6_plats_par_ingredient", ingredient=ingredient)
    nom = str(GRAPHE_INFERE.value(ingredient, RDFS.label))
    return reponse_liste("q6_plats_par_ingredient", inference, resultats, ingredient=identifiant, nom=nom)


@app.get("/api/ingredients/frequents")
def ingredients_frequents():
    graphe, inference = graphe_choisi()
    minimum = parametre_entier("min", defaut=3, minimum=1, maximum=100)
    resultats = q.interroger(graphe, "q7_ingredients_frequents", min=Literal(minimum))
    return reponse_liste("q7_ingredients_frequents", inference, resultats, min=minimum)


@app.get("/api/regions/stats")
def stats_regions():
    graphe, inference = graphe_choisi()
    return reponse_liste("q4_stats_par_region", inference, q.interroger(graphe, "q4_stats_par_region"))


@app.get("/api/chefs")
def chefs():
    graphe, inference = graphe_choisi()
    resultats = q.interroger(graphe, "q5_chefs_specialites")
    for chef in resultats:  # "A, B, C" -> ["A", "B", "C"] : plus propre en JSON
        chef["specialites"] = chef["specialites"].split(", ")
    return reponse_liste("q5_chefs_specialites", inference, resultats)


@app.get("/api/inference/comparaison")
def comparaison_inference():
    return jsonify(
        triplets={
            "sansInference": len(GRAPHE_INITIAL),
            "avecInference": len(GRAPHE_INFERE),
            "deduits": len(GRAPHE_INFERE) - len(GRAPHE_INITIAL),
        },
        requetes=COMPARAISON,
    )


if __name__ == "__main__":
    # debug=False : sinon Flask relance le script et refait l'inférence deux fois
    app.run(host="127.0.0.1", port=5000, debug=False)
