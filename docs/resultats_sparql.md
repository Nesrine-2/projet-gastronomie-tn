# Partie 2 — Résultats des requêtes SPARQL (sans inférence)

Graphe interrogé : `ontologie.ttl` + `donnees.ttl` = **401 triplets**, aucune règle d'inférence appliquée.

Rapport produit par `python src/executer_requetes.py`.

## Récapitulatif

| Requête | Question métier | Résultats |
|---|---|---|
| Q1 | Quels plats principaux propose-t-on, d'où viennent-ils et combien de temps faut-il pour les préparer ? | 7 |
| Q2 | Je suis végétarien et pressé : que puis-je cuisiner ? | 4 |
| Q3 | Quel est le catalogue complet des plats, toutes catégories confondues ? | 0 |
| Q4 | Quelle région est la plus représentée et ses plats sont-ils longs à préparer ? | 5 |
| Q5 | Quels chefs mettent en avant la cuisine de leur propre région ? | 0 |
| Q6 | J'ai des œufs : quels plats puis-je préparer ? | 3 |
| Q7 | Quels produits faut-il toujours avoir dans une cuisine tunisienne ? | 7 |
| Q8 | Quels plats ne sont mis en avant par aucun chef (idée : recruter un chef pour ces plats) ? | 6 |

## Q1 — Plats principaux avec leur région, leur temps et leur difficulté

- **Fichier** : `queries/q1_plats_principaux.rq`
- **Question métier** : Quels plats principaux propose-t-on, d'où viennent-ils et combien de temps faut-il pour les préparer ?
- **Notions SPARQL** : Motif de triplets, FILTER sur la langue (lang), ORDER BY
- **Nombre de résultats** : 7

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?plat ?nom ?region ?tempsPreparation ?difficulte
WHERE {
  ?plat a gt:PlatPrincipal ;
        rdfs:label ?nom ;
        gt:originaireDe ?r ;
        gt:tempsPreparation ?tempsPreparation ;
        gt:difficulte ?difficulte .
  ?r rdfs:label ?region .
  FILTER (lang(?nom) = "fr" && lang(?region) = "fr")
}
ORDER BY ?tempsPreparation
```

| plat | nom | region | tempsPreparation | difficulte |
|---|---|---|---|---|
| res:Ojja | Ojja merguez | Tunis | 30 | Facile |
| res:Chakchouka | Chakchouka | Nabeul | 35 | Facile |
| res:Kafteji | Kafteji | Tunis | 45 | Moyenne |
| res:RouzJerbi | Riz djerbien | Médenine (Djerba) | 90 | Moyenne |
| res:CouscousPoisson | Couscous au poisson | Sfax | 120 | Difficile |
| res:CouscousAgneau | Couscous à l'agneau | Tunis | 150 | Difficile |
| res:Mloukhia | Mloukhia | Tunis | 240 | Difficile |

## Q2 — Plats végétariens prêts en 45 minutes maximum

- **Fichier** : `queries/q2_vegetariens_rapides.rq`
- **Question métier** : Je suis végétarien et pressé : que puis-je cuisiner ?
- **Notions SPARQL** : VALUES (paramètre), FILTER booléen et numérique, OPTIONAL
- **Nombre de résultats** : 4

```sparql
PREFIX gt:      <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?plat ?nom ?tempsPreparation ?description
WHERE {
  VALUES ?max { 45 }
  ?plat gt:estVegetarien true ;
        gt:tempsPreparation ?tempsPreparation ;
        rdfs:label ?nom .
  OPTIONAL { ?plat dcterms:description ?description }
  FILTER (?tempsPreparation <= ?max && lang(?nom) = "fr")
}
ORDER BY ?tempsPreparation
```

| plat | nom | tempsPreparation | description |
|---|---|---|---|
| res:Lablabi | Lablabi | 30 | Soupe de pois chiches servie sur du pain, à l'ail et au cumin. |
| res:Chakchouka | Chakchouka | 35 | Poivrons et tomates mijotés avec des œufs. |
| res:SaladeMechouia | Salade méchouia | 40 | Poivrons et tomates grillés, écrasés à l'ail et à l'huile d'olive. |
| res:Kafteji | Kafteji | 45 | Légumes frits hachés avec des œufs. |

## Q3 — Catalogue complet des plats (instances de la super-classe gt:Plat)

- **Fichier** : `queries/q3_tous_les_plats.rq`
- **Question métier** : Quel est le catalogue complet des plats, toutes catégories confondues ?
- **Notions SPARQL** : Rdf:type sur une super-classe, VALUES (paramètre), chemin de propriété rdfs:subClassOf*, FILTER NOT EXISTS
- **Nombre de résultats** : 0

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?plat ?nom ?categorie ?region ?tempsPreparation ?estVegetarien
WHERE {
  VALUES ?classe { gt:Plat }
  ?plat a ?classe ;
        rdfs:label ?nom ;
        gt:originaireDe ?r ;
        gt:tempsPreparation ?tempsPreparation ;
        gt:estVegetarien ?estVegetarien .
  ?r rdfs:label ?region .
  FILTER (lang(?nom) = "fr" && lang(?region) = "fr")

  # Classe la plus précise : une classe de plat dont le plat n'a aucune sous-classe plus précise
  ?plat a ?cat .
  ?cat rdfs:subClassOf* gt:Plat ;
       rdfs:label ?categorie .
  FILTER NOT EXISTS { ?plat a ?sous . ?sous rdfs:subClassOf ?cat . FILTER (?sous != ?cat) }
}
ORDER BY ?nom
```

_Aucun résultat._

## Q4 — Statistiques par région : nombre de plats, temps moyen, plats végétariens

- **Fichier** : `queries/q4_stats_par_region.rq`
- **Question métier** : Quelle région est la plus représentée et ses plats sont-ils longs à préparer ?
- **Notions SPARQL** : GROUP BY, COUNT, AVG, ROUND, SUM + IF, ORDER BY DESC
- **Nombre de résultats** : 5

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?region ?nom (COUNT(?plat) AS ?nbPlats) (ROUND(AVG(?temps)) AS ?tempsMoyen)
       (SUM(IF(?vege, 1, 0)) AS ?nbVegetariens)
WHERE {
  ?plat gt:originaireDe ?region ;
        gt:tempsPreparation ?temps ;
        gt:estVegetarien ?vege .
  ?region rdfs:label ?nom .
  FILTER (lang(?nom) = "fr")
}
GROUP BY ?region ?nom
ORDER BY DESC(?nbPlats) ?nom
```

| region | nom | nbPlats | tempsMoyen | nbVegetariens |
|---|---|---|---|---|
| res:Tunis | Tunis | 9 | 97 | 4 |
| res:Nabeul | Nabeul | 2 | 38 | 2 |
| res:Kairouan | Kairouan | 1 | 90 | 1 |
| res:Medenine | Médenine (Djerba) | 1 | 90 | 0 |
| res:Sfax | Sfax | 1 | 120 | 0 |

## Q5 — Chefs, leur ville, leurs spécialités et combien sont des plats de leur région

- **Fichier** : `queries/q5_chefs_specialites.rq`
- **Question métier** : Quels chefs mettent en avant la cuisine de leur propre région ?
- **Notions SPARQL** : Vocabulaire FOAF, GROUP_CONCAT, COUNT, SUM + IF, GROUP BY
- **Nombre de résultats** : 0

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT ?chef ?nom ?ville
       (GROUP_CONCAT(?nomPlat; separator=", ") AS ?specialites)
       (COUNT(?plat) AS ?nbSpecialites)
       (SUM(IF(?origine = ?r, 1, 0)) AS ?nbPlatsLocaux)
WHERE {
  ?chef a gt:Chef ;
        foaf:name ?nom ;
        foaf:based_near ?r ;
        gt:specialite ?plat .
  ?r rdfs:label ?ville .
  ?plat rdfs:label ?nomPlat ;
        gt:originaireDe ?origine .
  FILTER (lang(?ville) = "fr" && lang(?nomPlat) = "fr")
}
GROUP BY ?chef ?nom ?ville
ORDER BY DESC(?nbSpecialites) ?nom
```

_Aucun résultat._

## Q6 — Plats contenant un ingrédient donné

- **Fichier** : `queries/q6_plats_par_ingredient.rq`
- **Question métier** : J'ai des œufs : quels plats puis-je préparer ?
- **Notions SPARQL** : VALUES (paramètre), propriété gt:contientIngredient
- **Nombre de résultats** : 3

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX res:  <http://example.org/gastronomie-tn/ressource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?plat ?nom ?nomIngredient
WHERE {
  VALUES ?ingredient { res:Oeuf }
  ?plat gt:contientIngredient ?ingredient ;
        rdfs:label ?nom .
  ?ingredient rdfs:label ?nomIngredient .
  FILTER (lang(?nom) = "fr")
}
ORDER BY ?nom
```

| plat | nom | nomIngredient |
|---|---|---|
| res:Brik | Brik à l'œuf | Œuf |
| res:Chakchouka | Chakchouka | Œuf |
| res:Kafteji | Kafteji | Œuf |

## Q7 — Ingrédients utilisés dans au moins 3 plats

- **Fichier** : `queries/q7_ingredients_frequents.rq`
- **Question métier** : Quels produits faut-il toujours avoir dans une cuisine tunisienne ?
- **Notions SPARQL** : VALUES (paramètre), COUNT(DISTINCT), GROUP BY, HAVING
- **Nombre de résultats** : 7

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?ingredient ?nom (COUNT(DISTINCT ?plat) AS ?nbPlats)
WHERE {
  VALUES ?min { 3 }
  ?plat gt:contientIngredient ?ingredient .
  ?ingredient rdfs:label ?nom .
}
GROUP BY ?ingredient ?nom ?min
HAVING (COUNT(DISTINCT ?plat) >= ?min)
ORDER BY DESC(?nbPlats) ?nom
```

| ingredient | nom | nbPlats |
|---|---|---|
| res:HuileOlive | Huile d'olive | 7 |
| res:Tomate | Tomate | 7 |
| res:Ail | Ail | 4 |
| res:Agneau | Agneau | 3 |
| res:Oignon | Oignon | 3 |
| res:PoisChiches | Pois chiches | 3 |
| res:Oeuf | Œuf | 3 |

## Q8 — Plats qu'aucun chef n'a en spécialité, avec leur lien DBpedia éventuel

- **Fichier** : `queries/q8_plats_sans_chef.rq`
- **Question métier** : Quels plats ne sont mis en avant par aucun chef (idée : recruter un chef pour ces plats) ?
- **Notions SPARQL** : Négation FILTER NOT EXISTS, OPTIONAL, lien externe DBpedia (rdfs:seeAlso)
- **Nombre de résultats** : 6

```sparql
PREFIX gt:   <http://example.org/gastronomie-tn/ontologie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?plat ?nom ?lienDBpedia
WHERE {
  ?plat gt:originaireDe ?region ;
        rdfs:label ?nom .
  FILTER (lang(?nom) = "fr")
  FILTER NOT EXISTS { ?chef gt:specialite ?plat }
  OPTIONAL { ?plat rdfs:seeAlso ?lienDBpedia }
}
ORDER BY ?nom
```

| plat | nom | lienDBpedia |
|---|---|---|
| res:AssidaZgougou | Assidat zgougou |  |
| res:Bambalouni | Bambalouni |  |
| res:ChorbaFrik | Chorba frik |  |
| res:CouscousAgneau | Couscous à l'agneau | dbr:Couscous |
| res:Kafteji | Kafteji |  |
| res:Mloukhia | Mloukhia |  |

