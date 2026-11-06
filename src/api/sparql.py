"""
Pont entre le Web Service et les requêtes SPARQL.

Le Web Service n'écrit AUCUNE requête SPARQL lui-même : il exécute les
fichiers du dossier queries/ (les mêmes que dans les parties 2 et 3) et
convertit chaque ligne de résultat en dictionnaire Python, donc en JSON.
"""

from decimal import Decimal

from rdflib import Literal, URIRef

from commun import GT, RES, chemin_requete, executer


def en_json(valeur):
    """Valeur rdflib -> valeur JSON.
      - URI d'une ressource du projet -> identifiant court ("Ojja") ;
      - autre URI (ex. DBpedia)       -> texte de l'URI ;
      - littéral                      -> int, float, bool ou str ;
      - absent (OPTIONAL non trouvé)  -> None (null en JSON).
    """
    if valeur is None:
        return None
    if isinstance(valeur, URIRef):
        texte = str(valeur)
        return texte[len(RES):] if texte.startswith(RES) else texte
    if isinstance(valeur, Literal):
        python = valeur.toPython()
        # AVG / ROUND renvoient un décimal, non sérialisable en JSON -> int ou float
        if isinstance(python, (Decimal, float)):
            return int(python) if python == int(python) else float(python)
        return python
    return str(valeur)


def interroger(graphe, nom_requete, **parametres):
    """Exécute queries/<nom_requete>.rq avec ses paramètres.

    Exemple : interroger(g, "q2_vegetariens_rapides", max=Literal(30))
    Renvoie une liste de dictionnaires {"nomVariable": valeur, ...}.
    """
    resultat = executer(graphe, chemin_requete(nom_requete), **parametres)
    return [{str(var): en_json(ligne[var]) for var in resultat.vars} for ligne in resultat]


def uri_ressource(identifiant):
    return URIRef(RES + identifiant)


def uri_classe(nom_classe):
    return URIRef(GT + nom_classe)
