"""
Partie 1 — Vérification de la modélisation RDFS et des données RDF.

Ce script :
  1. charge data/ontologie.ttl et data/donnees.ttl ;
  2. vérifie les exigences du sujet (>= 5 classes, >= 8 propriétés,
     rdfs:subClassOf, rdfs:subPropertyOf, rdfs:domain / rdfs:range,
     vocabulaire externe) ;
  3. vérifie la cohérence données <-> schéma (classes et propriétés
     utilisées bien déclarées, pas de faute de frappe dans les URI,
     types des valeurs numériques / booléennes corrects).

Lancement (terminal ouvert dans le dossier projet-gastronomie-tn, venv activé) :
    python src/verifier_modele.py
"""

import sys

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

from commun import FICHIER_DONNEES, FICHIER_ONTOLOGIE

sys.stdout.reconfigure(encoding="utf-8")  # accents et arabe lisibles sous Windows

GT = Namespace("http://example.org/gastronomie-tn/ontologie#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

erreurs = []


def ok(message):
    print(f"  [OK]     {message}")


def erreur(message):
    print(f"  [ERREUR] {message}")
    erreurs.append(message)


def court(uri, graphe):
    """Affiche une URI sous forme courte (gt:Plat au lieu de l'URI complète)."""
    try:
        return graphe.namespace_manager.normalizeUri(uri)
    except Exception:
        return str(uri)


# ------------------------------------------------------------------
# 1. Chargement des fichiers
# ------------------------------------------------------------------
print("\n=== 1. Chargement des fichiers Turtle ===")
onto = Graph()
donnees = Graph()
try:
    onto.parse(FICHIER_ONTOLOGIE, format="turtle")
    ok(f"ontologie.ttl chargé : {len(onto)} triplets")
    donnees.parse(FICHIER_DONNEES, format="turtle")
    ok(f"donnees.ttl chargé   : {len(donnees)} triplets")
except Exception as e:
    print(f"  [ERREUR] Impossible de lire un fichier Turtle : {e}")
    sys.exit(1)

tout = onto + donnees  # graphe complet (schéma + données)
tout.bind("gt", GT)
tout.bind("foaf", FOAF)

# ------------------------------------------------------------------
# 2. Exigences du sujet
# ------------------------------------------------------------------
print("\n=== 2. Exigences du sujet ===")

classes = set(onto.subjects(RDF.type, RDFS.Class))
proprietes = set(onto.subjects(RDF.type, RDF.Property))
classes_gt = {c for c in classes if str(c).startswith(str(GT))}
proprietes_gt = {p for p in proprietes if str(p).startswith(str(GT))}

(ok if len(classes_gt) >= 5 else erreur)(f"{len(classes_gt)} classes définies (minimum 5)")
(ok if len(proprietes_gt) >= 8 else erreur)(f"{len(proprietes_gt)} propriétés définies (minimum 8)")

sous_classes = list(onto.subject_objects(RDFS.subClassOf))
sous_proprietes = list(onto.subject_objects(RDFS.subPropertyOf))
(ok if sous_classes else erreur)(f"{len(sous_classes)} relations rdfs:subClassOf")
for s, o in sous_classes:
    print(f"             {court(s, tout)}  ->  {court(o, tout)}")
(ok if sous_proprietes else erreur)(f"{len(sous_proprietes)} relations rdfs:subPropertyOf")
for s, o in sous_proprietes:
    print(f"             {court(s, tout)}  ->  {court(o, tout)}")

for p in sorted(proprietes_gt):
    a_domain = (p, RDFS.domain, None) in onto
    a_range = (p, RDFS.range, None) in onto
    if a_domain and a_range:
        ok(f"{court(p, tout)} a un rdfs:domain et un rdfs:range")
    else:
        erreur(f"{court(p, tout)} : domain ou range manquant")

utilise_foaf = any(str(p).startswith(str(FOAF)) for p in donnees.predicates()) or \
    (None, RDFS.subClassOf, FOAF.Person) in onto
(ok if utilise_foaf else erreur)("vocabulaire externe FOAF réutilisé (foaf:Person, foaf:name, foaf:based_near)")

# ------------------------------------------------------------------
# 3. Cohérence données <-> schéma
# ------------------------------------------------------------------
print("\n=== 3. Cohérence entre les données et le schéma ===")

# Prédicats standards autorisés même s'ils ne sont pas redéclarés
standards = {RDF.type, RDFS.label, RDFS.comment, RDFS.seeAlso}

# 3a. Toute propriété utilisée dans les données doit être déclarée
inconnues = {p for p in donnees.predicates() if p not in proprietes and p not in standards}
if inconnues:
    for p in inconnues:
        erreur(f"propriété utilisée mais non déclarée : {p}")
else:
    ok("toutes les propriétés utilisées dans les données sont déclarées")

# 3b. Toute classe utilisée avec rdf:type doit être déclarée
classes_utilisees = set(donnees.objects(predicate=RDF.type))
non_declarees = classes_utilisees - classes
if non_declarees:
    for c in non_declarees:
        erreur(f"classe utilisée mais non déclarée : {c}")
else:
    ok("toutes les classes utilisées dans les données sont déclarées")

# 3c. Les objets des propriétés gt: doivent exister (détecte les fautes de frappe)
sujets_connus = set(donnees.subjects())
proprietes_objet = [GT.contientIngredient, GT.ingredientPrincipal, GT.epiceUtilisee,
                    GT.originaireDe, GT.specialite]
fautes = [(s, p, o) for p in proprietes_objet for s, o in donnees.subject_objects(p)
          if o not in sujets_connus]
if fautes:
    for s, p, o in fautes:
        erreur(f"{court(s, tout)} {court(p, tout)} {o} : ressource inexistante (faute de frappe ?)")
else:
    ok("toutes les ressources référencées existent (aucune faute de frappe dans les URI)")

# 3d. Les valeurs littérales doivent respecter le rdfs:range déclaré
for p in proprietes_gt:
    rng = onto.value(p, RDFS.range)
    if rng is None or not str(rng).startswith(str(XSD)):
        continue
    for s, valeur in donnees.subject_objects(p):
        dt = valeur.datatype if isinstance(valeur, Literal) else None
        # un littéral sans type explicite est un xsd:string
        dt = dt or XSD.string
        if dt != rng:
            erreur(f"{court(s, tout)} {court(p, tout)} : type {court(dt, tout)} au lieu de {court(rng, tout)}")
ok("vérification des types des valeurs (integer / string / boolean) terminée")

# ------------------------------------------------------------------
# 4. Statistiques des données
# ------------------------------------------------------------------
print("\n=== 4. Contenu de la base ===")
SOUS_CLASSES_PLAT = [GT.Entree, GT.Soupe, GT.PlatPrincipal, GT.Dessert, GT.Patisserie]
nb_plats = len({s for c in SOUS_CLASSES_PLAT for s in donnees.subjects(RDF.type, c)})
print(f"  Plats       : {nb_plats}")
print(f"  Régions     : {len(set(donnees.subjects(RDF.type, GT.Region)))}")
print(f"  Personnes   : {len(set(donnees.subjects(RDF.type, FOAF.Person)))}")
print(f"  Triplets    : {len(tout)} (schéma + données)")

# ------------------------------------------------------------------
print("\n=== RÉSULTAT ===")
if erreurs:
    print(f"  {len(erreurs)} erreur(s) trouvée(s). Corrigez-les avant de passer à la partie 2.")
    sys.exit(1)
print("  Partie 1 valide : schéma et données cohérents.")
