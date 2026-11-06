"""
Partie 3 — Enrichissement du graphe par inférence RDFS (bibliothèque owlrl).

Ce script :
  1. charge le graphe initial (ontologie + données) et compte les triplets ;
  2. applique les règles RDFS sur une COPIE du graphe ;
  3. retire le « bruit » (déductions vraies mais sans intérêt métier),
     sans jamais retirer un triplet du graphe initial ;
  4. classe les triplets déduits par règle ;
  5. relance les 8 requêtes de la partie 2 et compare AVANT / APRÈS ;
  6. écrit data/graphe_infere.ttl et docs/comparaison_inference.md.

Règles RDFS utilisées (numérotation de la norme W3C « RDF 1.1 Semantics ») :
  - rdfs11 : subClassOf est transitif  (Soupe ⊑ Entree ⊑ Plat  =>  Soupe ⊑ Plat)
  - rdfs9  : héritage du type          (x a Soupe, Soupe ⊑ Plat  =>  x a Plat)
  - rdfs7  : subPropertyOf             (x ingredientPrincipal y  =>  x contientIngredient y)
  - rdfs2  : domain                    (x specialite y, domain Chef  =>  x a Chef)
  - rdfs3  : range                     (x epiceUtilisee y, range Epice  =>  y a Epice)

Lancement (terminal ouvert dans le dossier projet-gastronomie-tn, venv activé) :
    python src/inference.py
"""

import sys

from owlrl import DeductiveClosure, RDFS_Semantics
from rdflib import Literal, Namespace
from rdflib.namespace import RDF, RDFS

from commun import (DOSSIER_DOCS, FICHIER_GRAPHE_INFERE, charger_graphe, entete_requete, executer,
                    fichiers_requetes, resultat_en_tableau, tableau_markdown)

FICHIER_RAPPORT = DOSSIER_DOCS / "comparaison_inference.md"

GT = Namespace("http://example.org/gastronomie-tn/ontologie#")
RES = Namespace("http://example.org/gastronomie-tn/ressource/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


# ------------------------------------------------------------------------------
# Inférence
# ------------------------------------------------------------------------------
def est_bruit(s, p, o):
    """Déductions RDFS vraies mais inutiles pour notre métier :
      - sujet littéral       : ex. "120" rdf:type xsd:integer (interdit en Turtle) ;
      - x rdf:type rdfs:Resource, rdfs:Class, rdf:Property, rdfs:Datatype
        (« tout est une ressource », « toute propriété est une propriété »...) ;
      - C rdfs:subClassOf C, P rdfs:subPropertyOf P (réflexivité) ;
      - C rdfs:subClassOf rdfs:Resource.
    """
    if isinstance(s, Literal):
        return True
    if p == RDF.type and o in (RDFS.Resource, RDF.Property, RDFS.Class, RDFS.Datatype):
        return True
    if p in (RDFS.subClassOf, RDFS.subPropertyOf) and (s == o or o == RDFS.Resource):
        return True
    return False


def appliquer_inference(graphe):
    """Applique les règles RDFS sur le graphe (modifié sur place).

    Le bruit est retiré UNIQUEMENT parmi les triplets nouvellement déduits :
    tous les triplets du graphe initial sont conservés (par exemple
    « gt:Plat rdf:type rdfs:Class », qui déclare une classe de l'ontologie).
    Renvoie le nombre de triplets juste après owlrl (avant nettoyage).
    """
    initiaux = set(graphe)
    DeductiveClosure(RDFS_Semantics, axiomatic_triples=False, datatype_axioms=False).expand(graphe)
    nb_brut = len(graphe)
    for triplet in [t for t in graphe if t not in initiaux and est_bruit(*t)]:
        graphe.remove(triplet)
    return nb_brut


def graphe_infere():
    """Graphe initial + triplets déduits (utilisé aussi par le Web Service)."""
    g = charger_graphe()
    appliquer_inference(g)
    return g


# ------------------------------------------------------------------------------
# Analyse des résultats
# ------------------------------------------------------------------------------
REGLES = {
    "rdfs11": ("rdfs11 — transitivité de rdfs:subClassOf",
               "Si A ⊑ B et B ⊑ C, alors A ⊑ C.",
               "gt:Soupe rdfs:subClassOf gt:Entree . gt:Entree rdfs:subClassOf gt:Plat ."),
    "rdfs9": ("rdfs9 — héritage du type par rdfs:subClassOf",
              "Si x est de type A et A ⊑ B, alors x est aussi de type B.",
              "res:Lablabi rdf:type gt:Soupe . gt:Soupe rdfs:subClassOf gt:Entree ."),
    "rdfs7": ("rdfs7 — rdfs:subPropertyOf",
              "Si x P y et P est sous-propriété de Q, alors x Q y.",
              "res:Ojja gt:ingredientPrincipal res:Oeuf . "
              "gt:ingredientPrincipal rdfs:subPropertyOf gt:contientIngredient ."),
    "rdfs2": ("rdfs2 — rdfs:domain",
              "Si x P y et le domaine de P est C, alors x est de type C.",
              "res:HediJaziri gt:specialite res:Brik . gt:specialite rdfs:domain gt:Chef ."),
    "rdfs3": ("rdfs3 — rdfs:range",
              "Si x P y et le co-domaine de P est C, alors y est de type C.",
              "res:Ojja gt:epiceUtilisee res:Harissa . gt:epiceUtilisee rdfs:range gt:Epice ."),
    "chaine": ("Chaîne rdfs3 puis rdfs9",
               "Une épice sans type devient gt:Epice (rdfs3), puis gt:Ingredient (rdfs9).",
               "res:Harissa (aucun type) → gt:Epice → gt:Ingredient"),
    "autres": ("Autres déductions", "Déductions RDFS non classées ci-dessus.", ""),
}


def regle_du_triplet(s, p, o, avant):
    """Indique quelle règle a produit un triplet déduit."""
    if p == RDF.type and o == GT.Ingredient and (s, RDF.type, None) not in avant:
        return "chaine"
    if p == RDFS.subClassOf:
        return "rdfs11"
    if p == GT.contientIngredient:
        return "rdfs7"
    if p == RDF.type and o == GT.Chef:
        return "rdfs2"
    if p == RDF.type and o == GT.Epice:
        return "rdfs3"
    if p == RDF.type:
        return "rdfs9"
    return "autres"


def comparer_requetes(avant, apres):
    """Exécute les 8 requêtes sur les deux graphes. Renvoie une liste de dicts."""
    comparaison = []
    for f in fichiers_requetes():
        entete = entete_requete(f)
        col_av, lig_av = resultat_en_tableau(executer(avant, f), avant)
        col_ap, lig_ap = resultat_en_tableau(executer(apres, f), apres)
        comparaison.append({
            "fichier": f.name, "entete": entete,
            "colonnes_avant": col_av, "lignes_avant": lig_av,
            "colonnes_apres": col_ap, "lignes_apres": lig_ap,
        })
    return comparaison


def types_de(graphe, ressource):
    court = graphe.namespace_manager.normalizeUri
    return ", ".join(sorted(court(o) for o in graphe.objects(ressource, RDF.type))) or "aucun"


def ingredients_de(graphe, plat):
    court = graphe.namespace_manager.normalizeUri
    return ", ".join(sorted(court(o) for o in graphe.objects(plat, GT.contientIngredient))) or "aucun"


# ------------------------------------------------------------------------------
# Programme principal
# ------------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    avant = charger_graphe()                  # graphe initial, jamais modifié
    apres = charger_graphe()                  # copie qui sera enrichie
    nb_brut = appliquer_inference(apres)

    nouveaux = sorted(set(apres) - set(avant))
    perdus = set(avant) - set(apres)
    if perdus:  # ne doit jamais arriver : l'inférence ajoute, elle ne retire rien
        print(f"[ERREUR] {len(perdus)} triplet(s) du graphe initial ont disparu.")
        sys.exit(1)

    court = apres.namespace_manager.normalizeUri
    print("=== Nombre de triplets ===")
    print(f"  Graphe initial (sans inférence) : {len(avant)}")
    print(f"  Juste après owlrl (brut)        : {nb_brut}")
    print(f"  Graphe inféré (bruit retiré)    : {len(apres)}  (+{len(nouveaux)} triplets déduits)")
    print("  Triplets initiaux perdus        : 0")

    # --- 1. Nombre de triplets -------------------------------------------------
    md = "# Partie 3 — Inférence RDFS : comparaison avec et sans inférence\n\n"
    md += "Rapport produit par `python src/inference.py` (moteur : bibliothèque `owlrl`, sémantique RDFS).\n\n"
    md += "## 1. Nombre de triplets\n\n| Graphe | Triplets |\n|---|---|\n"
    md += f"| Graphe initial : `ontologie.ttl` + `donnees.ttl` | {len(avant)} |\n"
    md += f"| Juste après owlrl (avec le bruit) | {nb_brut} |\n"
    md += f"| **Graphe inféré** : `data/graphe_infere.ttl` | **{len(apres)}** |\n"
    md += f"| Triplets déduits utiles | +{len(nouveaux)} |\n"
    md += "| Triplets initiaux perdus | 0 |\n\n"
    md += ("Le « bruit » retiré est vrai mais sans intérêt métier : `x rdf:type rdfs:Resource`, "
           "`C rdfs:subClassOf C`, ou des triplets dont le sujet est un littéral "
           "(ex. `\"120\" rdf:type xsd:integer`). Seuls des triplets **déduits** sont retirés : "
           "le graphe inféré contient tous les triplets du graphe initial.\n\n")

    # --- 2. Exemples concrets avant / après -----------------------------------
    md += "## 2. Exemples concrets : avant / après\n\n"
    md += "| Ressource | Propriété observée | Sans inférence | Avec inférence | Règle |\n|---|---|---|---|---|\n"
    exemples = [
        (RES.Lablabi, "rdf:type", types_de, "rdfs9"),
        (RES.Bambalouni, "rdf:type", types_de, "rdfs9"),
        (RES.HediJaziri, "rdf:type", types_de, "rdfs2"),
        (RES.Harissa, "rdf:type", types_de, "rdfs3 puis rdfs9"),
        (RES.Ojja, "gt:contientIngredient", ingredients_de, "rdfs7"),
    ]
    for ressource, propriete, fonction, regle in exemples:
        md += (f"| `{court(ressource)}` | `{propriete}` | {fonction(avant, ressource)} "
               f"| {fonction(apres, ressource)} | {regle} |\n")
    md += "\n"

    # --- 3. Triplets déduits, règle par règle ---------------------------------
    print("\n=== Triplets déduits, par règle ===")
    md += "## 3. Triplets déduits, règle par règle\n\n"
    par_regle = {cle: [] for cle in REGLES}
    for t in nouveaux:
        par_regle[regle_du_triplet(*t, avant)].append(t)
    md += "| Règle | Triplets déduits |\n|---|---|\n"
    for cle, triplets in par_regle.items():
        if triplets:
            md += f"| {REGLES[cle][0]} | {len(triplets)} |\n"
    md += f"| **Total** | **{len(nouveaux)}** |\n\n"
    for cle, triplets in par_regle.items():
        if not triplets:
            continue
        nom, principe, exemple = REGLES[cle]
        print(f"\n-- {nom} : {len(triplets)} triplet(s)")
        md += f"### {nom} — {len(triplets)} triplet(s)\n\n**Principe** : {principe}\n\n"
        if exemple:
            md += f"**Exemple de prémisses** : `{exemple}`\n\n"
        md += "**Triplets déduits** :\n\n"
        for s, p, o in triplets:
            ligne = f"{court(s)} {court(p)} {court(o)}"
            print(f"   {ligne}")
            md += f"- `{ligne}`\n"
        md += "\n"

    # --- 4. Requêtes avant / après --------------------------------------------
    print("\n=== Requêtes : nombre de résultats sans / avec inférence ===")
    md += "## 4. Les 8 requêtes SPARQL : sans / avec inférence\n\n"
    md += "| Requête | Sans inférence | Avec inférence | Différence |\n|---|---|---|---|\n"
    details = ""
    for c in comparer_requetes(avant, apres):
        titre = c["entete"]["titre"]
        n_av, n_ap = len(c["lignes_avant"]), len(c["lignes_apres"])
        change = c["lignes_avant"] != c["lignes_apres"]
        print(f"  {titre[:70]:70} {n_av:>3} -> {n_ap:>3}{'  <-- différent' if change else ''}")
        diff = f"**+{n_ap - n_av}**" if n_ap != n_av else ("valeurs modifiées" if change else "—")
        md += f"| {titre} | {n_av} | {'**' + str(n_ap) + '**' if change else n_ap} | {diff} |\n"
        if change:
            gagnes = [ligne for ligne in c["lignes_apres"] if ligne not in c["lignes_avant"]]
            details += f"### {titre}\n\n"
            details += f"**Pourquoi ça change ?** {c['entete']['inference']}\n\n"
            details += f"**Sans inférence** ({n_av}) :\n\n" + tableau_markdown(c["colonnes_avant"], c["lignes_avant"])
            details += f"\n**Avec inférence** ({n_ap}) :\n\n" + tableau_markdown(c["colonnes_apres"], c["lignes_apres"])
            details += f"\nLignes nouvelles ou modifiées grâce à l'inférence : {len(gagnes)}\n\n"
    md += ("\nLes requêtes Q1, Q2, Q4 et Q8 ne changent pas : elles n'utilisent que des triplets "
           "écrits explicitement dans les données. Les autres dépendent de triplets déduits.\n\n")
    md += "## 5. Détail des requêtes qui changent\n\n" + details

    # --- Sauvegarde -----------------------------------------------------------
    apres.serialize(FICHIER_GRAPHE_INFERE, format="turtle")
    FICHIER_RAPPORT.write_text(md, encoding="utf-8")
    print(f"\nRapport écrit dans docs/{FICHIER_RAPPORT.name}")
    print(f"Graphe inféré sauvegardé dans data/{FICHIER_GRAPHE_INFERE.name}")


if __name__ == "__main__":
    main()
