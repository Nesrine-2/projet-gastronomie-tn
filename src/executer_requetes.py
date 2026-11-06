"""
Partie 2 — Interrogation SPARQL du graphe initial (SANS inférence).

Ce script :
  1. charge data/ontologie.ttl + data/donnees.ttl dans un seul graphe ;
  2. exécute chaque requête queries/q1_... à queries/q8_... ;
  3. affiche les résultats dans le terminal ;
  4. écrit le rapport docs/resultats_sparql.md : pour chaque requête,
     la question métier, les notions SPARQL, le code et le tableau de résultats.

Lancement (terminal ouvert dans le dossier projet-gastronomie-tn, venv activé) :
    python src/executer_requetes.py
"""

import sys

from commun import (DOSSIER_DOCS, charger_graphe, entete_requete, executer, fichiers_requetes,
                    resultat_en_tableau, tableau_markdown, texte_sans_commentaires)

FICHIER_RAPPORT = DOSSIER_DOCS / "resultats_sparql.md"


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows : accents et arabe
    try:
        graphe = charger_graphe()
    except Exception as e:
        print(f"[ERREUR] Lecture des fichiers Turtle impossible : {e}")
        sys.exit(1)

    fichiers = fichiers_requetes()
    if not fichiers:
        print("[ERREUR] Aucun fichier q*.rq trouvé dans le dossier queries/")
        sys.exit(1)

    md = "# Partie 2 — Résultats des requêtes SPARQL (sans inférence)\n\n"
    md += (f"Graphe interrogé : `ontologie.ttl` + `donnees.ttl` = **{len(graphe)} triplets**, "
           "aucune règle d'inférence appliquée.\n\n")
    md += "Rapport produit par `python src/executer_requetes.py`.\n\n"
    md += "## Récapitulatif\n\n| Requête | Question métier | Résultats |\n|---|---|---|\n"
    sections = ""

    for f in fichiers:
        entete = entete_requete(f)
        try:
            colonnes, lignes = resultat_en_tableau(executer(graphe, f), graphe)
        except Exception as e:
            print(f"\n[ERREUR] {f.name} : {e}")
            sys.exit(1)

        print(f"\n=== {entete['titre']}  ({len(lignes)} résultat(s)) ===")
        for ligne in lignes:
            print("   " + " | ".join(ligne))

        md += f"| {entete['titre'].split(' — ')[0]} | {entete['question']} | {len(lignes)} |\n"
        sections += f"## {entete['titre']}\n\n"
        sections += f"- **Fichier** : `queries/{f.name}`\n"
        sections += f"- **Question métier** : {entete['question']}\n"
        sections += f"- **Notions SPARQL** : {entete['notions']}\n"
        sections += f"- **Nombre de résultats** : {len(lignes)}\n\n"
        sections += "```sparql\n" + texte_sans_commentaires(f) + "\n```\n\n"
        sections += tableau_markdown(colonnes, lignes) + "\n"

    md += "\n" + sections
    FICHIER_RAPPORT.write_text(md, encoding="utf-8")
    print(f"\nRapport écrit dans docs/{FICHIER_RAPPORT.name}")


if __name__ == "__main__":
    main()
