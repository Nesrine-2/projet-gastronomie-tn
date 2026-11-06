"""
Fonctions communes à toutes les parties du projet.

- chemins des dossiers (data/, queries/, docs/) ;
- chargement du graphe RDF (ontologie + données) ;
- lecture des requêtes SPARQL stockées dans queries/*.rq ;
- exécution d'une requête avec des paramètres (sans injection SPARQL).

Les requêtes SPARQL n'existent qu'à UN seul endroit : le dossier queries/.
Les scripts (parties 2 et 3) et le Web Service (partie 4) lisent les mêmes fichiers.
"""

import re
from pathlib import Path

from rdflib import Graph, Literal, URIRef

# ------------------------------------------------------------------------------
# Chemins
# ------------------------------------------------------------------------------
RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_REQUETES = RACINE / "queries"
DOSSIER_DOCS = RACINE / "docs"

FICHIER_ONTOLOGIE = DOSSIER_DATA / "ontologie.ttl"
FICHIER_DONNEES = DOSSIER_DATA / "donnees.ttl"
FICHIER_GRAPHE_INFERE = DOSSIER_DATA / "graphe_infere.ttl"

# Espaces de noms du projet
GT = "http://example.org/gastronomie-tn/ontologie#"
RES = "http://example.org/gastronomie-tn/ressource/"


# ------------------------------------------------------------------------------
# Graphe
# ------------------------------------------------------------------------------
def charger_graphe():
    """Charge le schéma (ontologie.ttl) et les données (donnees.ttl) dans un
    même graphe, SANS inférence."""
    g = Graph()
    g.parse(FICHIER_ONTOLOGIE, format="turtle")
    g.parse(FICHIER_DONNEES, format="turtle")
    g.bind("gt", GT)
    g.bind("res", RES)
    g.bind("dbr", "http://dbpedia.org/resource/")
    return g


# ------------------------------------------------------------------------------
# Requêtes SPARQL (.rq)
# ------------------------------------------------------------------------------
def fichiers_requetes():
    """Les 8 requêtes de la partie 2 : queries/q1_... à queries/q8_..."""
    return sorted(DOSSIER_REQUETES.glob("q*.rq"))


def chemin_requete(nom):
    """'q2_vegetariens_rapides' ou 'api/detail_plat' -> chemin du fichier .rq"""
    return DOSSIER_REQUETES / f"{nom}.rq"


def entete_requete(fichier_rq):
    """Lit les commentaires du début du fichier .rq.

    Renvoie un dictionnaire :
      titre     : 1re ligne (ex. "Q1 — Plats principaux ...")
      question  : ligne "Question métier : ..."
      notions   : ligne "Notions SPARQL : ..."
      inference : ligne "Effet de l'inférence : ..."
    """
    lignes = Path(fichier_rq).read_text(encoding="utf-8").splitlines()
    commentaires = []
    for ligne in lignes:
        if not ligne.startswith("#"):
            break
        commentaires.append(ligne.lstrip("#").strip())

    def champ(debut):
        for c in commentaires:
            if c.startswith(debut):
                valeur = c.split(":", 1)[1].strip()
                return valeur[:1].upper() + valeur[1:]
        return ""

    return {
        "titre": commentaires[0] if commentaires else Path(fichier_rq).stem,
        "question": champ("Question métier"),
        "notions": champ("Notions SPARQL"),
        "inference": champ("Effet de l'inférence"),
    }


def texte_sans_commentaires(fichier_rq):
    """Le texte SPARQL du fichier, sans le bloc de commentaires du début."""
    lignes = Path(fichier_rq).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lignes) and (lignes[i].startswith("#") or not lignes[i].strip()):
        i += 1
    return "\n".join(lignes[i:]).strip()


def preparer_requete(texte, parametres):
    """Retire les lignes 'VALUES ?x { ... }' des variables passées en paramètre.

    Dans les fichiers .rq, chaque paramètre a une valeur par défaut écrite avec
    VALUES (ex. VALUES ?max { 45 }), pour que la requête reste exécutable telle
    quelle. Quand l'API fournit une autre valeur, on enlève cette ligne et on
    passe la valeur à rdflib avec initBindings : la valeur n'est jamais collée
    dans le texte SPARQL, donc aucune injection n'est possible.
    """
    for nom in parametres:
        texte = re.sub(r"VALUES\s+\?" + re.escape(nom) + r"\s*\{[^}]*\}", "", texte)
    return texte


def executer(graphe, fichier_rq, **parametres):
    """Exécute un fichier .rq sur un graphe.

    parametres : valeurs rdflib (Literal, URIRef) qui remplacent les valeurs
                 par défaut des VALUES. Exemple : executer(g, f, max=Literal(30))
    Renvoie le résultat rdflib (itérable de lignes, avec .vars).
    """
    texte = Path(fichier_rq).read_text(encoding="utf-8")
    texte = preparer_requete(texte, parametres)
    return graphe.query(texte, initBindings=parametres)


# ------------------------------------------------------------------------------
# Affichage
# ------------------------------------------------------------------------------
def valeur_lisible(valeur, graphe):
    """URI -> forme courte (res:Ojja) ; littéral -> sa valeur ; vide -> ''."""
    if valeur is None:
        return ""
    if isinstance(valeur, URIRef):
        return graphe.namespace_manager.normalizeUri(valeur)
    if isinstance(valeur, Literal):
        return str(valeur)
    return str(valeur)


def resultat_en_tableau(resultat, graphe):
    """Résultat rdflib -> (noms_colonnes, lignes de texte)."""
    colonnes = [str(v) for v in resultat.vars]
    lignes = [[valeur_lisible(ligne[v], graphe) for v in resultat.vars] for ligne in resultat]
    return colonnes, lignes


def tableau_markdown(colonnes, lignes):
    if not lignes:
        return "_Aucun résultat._\n"
    md = "| " + " | ".join(colonnes) + " |\n"
    md += "|" + "---|" * len(colonnes) + "\n"
    for ligne in lignes:
        md += "| " + " | ".join(c.replace("|", "\\|") for c in ligne) + " |\n"
    return md
