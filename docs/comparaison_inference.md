# Partie 3 — Inférence RDFS : comparaison avec et sans inférence

Rapport produit par `python src/inference.py` (moteur : bibliothèque `owlrl`, sémantique RDFS).

## 1. Nombre de triplets

| Graphe | Triplets |
|---|---|
| Graphe initial : `ontologie.ttl` + `donnees.ttl` | 401 |
| Juste après owlrl (avec le bruit) | 794 |
| **Graphe inféré** : `data/graphe_infere.ttl` | **481** |
| Triplets déduits utiles | +80 |
| Triplets initiaux perdus | 0 |

Le « bruit » retiré est vrai mais sans intérêt métier : `x rdf:type rdfs:Resource`, `C rdfs:subClassOf C`, ou des triplets dont le sujet est un littéral (ex. `"120" rdf:type xsd:integer`). Seuls des triplets **déduits** sont retirés : le graphe inféré contient tous les triplets du graphe initial.

## 2. Exemples concrets : avant / après

| Ressource | Propriété observée | Sans inférence | Avec inférence | Règle |
|---|---|---|---|---|
| `res:Lablabi` | `rdf:type` | gt:Soupe | gt:Entree, gt:Plat, gt:Soupe | rdfs9 |
| `res:Bambalouni` | `rdf:type` | gt:Patisserie | gt:Dessert, gt:Patisserie, gt:Plat | rdfs9 |
| `res:HediJaziri` | `rdf:type` | foaf:Person | foaf:Person, gt:Chef | rdfs2 |
| `res:Harissa` | `rdf:type` | aucun | gt:Epice, gt:Ingredient | rdfs3 puis rdfs9 |
| `res:Ojja` | `gt:contientIngredient` | res:Ail, res:HuileOlive, res:Merguez, res:Tomate | res:Ail, res:Carvi, res:Harissa, res:HuileOlive, res:Merguez, res:Oeuf, res:Tomate | rdfs7 |

## 3. Triplets déduits, règle par règle

| Règle | Triplets déduits |
|---|---|
| rdfs11 — transitivité de rdfs:subClassOf | 2 |
| rdfs9 — héritage du type par rdfs:subClassOf | 36 |
| rdfs7 — rdfs:subPropertyOf | 30 |
| rdfs2 — rdfs:domain | 4 |
| rdfs3 — rdfs:range | 4 |
| Chaîne rdfs3 puis rdfs9 | 4 |
| **Total** | **80** |

### rdfs11 — transitivité de rdfs:subClassOf — 2 triplet(s)

**Principe** : Si A ⊑ B et B ⊑ C, alors A ⊑ C.

**Exemple de prémisses** : `gt:Soupe rdfs:subClassOf gt:Entree . gt:Entree rdfs:subClassOf gt:Plat .`

**Triplets déduits** :

- `gt:Patisserie rdfs:subClassOf gt:Plat`
- `gt:Soupe rdfs:subClassOf gt:Plat`

### rdfs9 — héritage du type par rdfs:subClassOf — 36 triplet(s)

**Principe** : Si x est de type A et A ⊑ B, alors x est aussi de type B.

**Exemple de prémisses** : `res:Lablabi rdf:type gt:Soupe . gt:Soupe rdfs:subClassOf gt:Entree .`

**Triplets déduits** :

- `res:Agneau rdf:type gt:Ingredient`
- `res:Ail rdf:type gt:Ingredient`
- `res:AssidaZgougou rdf:type gt:Plat`
- `res:Bambalouni rdf:type gt:Dessert`
- `res:Bambalouni rdf:type gt:Plat`
- `res:Blette rdf:type gt:Ingredient`
- `res:Boeuf rdf:type gt:Ingredient`
- `res:Brik rdf:type gt:Plat`
- `res:Chakchouka rdf:type gt:Plat`
- `res:ChorbaFrik rdf:type gt:Entree`
- `res:ChorbaFrik rdf:type gt:Plat`
- `res:Corete rdf:type gt:Ingredient`
- `res:Courgette rdf:type gt:Ingredient`
- `res:CouscousAgneau rdf:type gt:Plat`
- `res:CouscousPoisson rdf:type gt:Plat`
- `res:Farine rdf:type gt:Ingredient`
- `res:Frik rdf:type gt:Ingredient`
- `res:Kafteji rdf:type gt:Plat`
- `res:Lablabi rdf:type gt:Entree`
- `res:Lablabi rdf:type gt:Plat`
- `res:Makroudh rdf:type gt:Dessert`
- `res:Makroudh rdf:type gt:Plat`
- `res:Merguez rdf:type gt:Ingredient`
- `res:Merou rdf:type gt:Ingredient`
- `res:Mloukhia rdf:type gt:Plat`
- `res:Oignon rdf:type gt:Ingredient`
- `res:Ojja rdf:type gt:Plat`
- `res:PoisChiches rdf:type gt:Ingredient`
- `res:Poivron rdf:type gt:Ingredient`
- `res:PommeDeTerre rdf:type gt:Ingredient`
- `res:Riz rdf:type gt:Ingredient`
- `res:RouzJerbi rdf:type gt:Plat`
- `res:SaladeMechouia rdf:type gt:Plat`
- `res:Semoule rdf:type gt:Ingredient`
- `res:Thon rdf:type gt:Ingredient`
- `res:Tomate rdf:type gt:Ingredient`

### rdfs7 — rdfs:subPropertyOf — 30 triplet(s)

**Principe** : Si x P y et P est sous-propriété de Q, alors x Q y.

**Exemple de prémisses** : `res:Ojja gt:ingredientPrincipal res:Oeuf . gt:ingredientPrincipal rdfs:subPropertyOf gt:contientIngredient .`

**Triplets déduits** :

- `res:AssidaZgougou gt:contientIngredient res:Zgougou`
- `res:Bambalouni gt:contientIngredient res:Farine`
- `res:Brik gt:contientIngredient res:FeuilleBrik`
- `res:Chakchouka gt:contientIngredient res:Harissa`
- `res:Chakchouka gt:contientIngredient res:Poivron`
- `res:ChorbaFrik gt:contientIngredient res:Frik`
- `res:ChorbaFrik gt:contientIngredient res:Harissa`
- `res:ChorbaFrik gt:contientIngredient res:Tabel`
- `res:CouscousAgneau gt:contientIngredient res:Carvi`
- `res:CouscousAgneau gt:contientIngredient res:Harissa`
- `res:CouscousAgneau gt:contientIngredient res:Semoule`
- `res:CouscousPoisson gt:contientIngredient res:Harissa`
- `res:CouscousPoisson gt:contientIngredient res:Semoule`
- `res:CouscousPoisson gt:contientIngredient res:Tabel`
- `res:Kafteji gt:contientIngredient res:Harissa`
- `res:Kafteji gt:contientIngredient res:Poivron`
- `res:Lablabi gt:contientIngredient res:Cumin`
- `res:Lablabi gt:contientIngredient res:Harissa`
- `res:Lablabi gt:contientIngredient res:PoisChiches`
- `res:Makroudh gt:contientIngredient res:Semoule`
- `res:Mloukhia gt:contientIngredient res:Carvi`
- `res:Mloukhia gt:contientIngredient res:Corete`
- `res:Mloukhia gt:contientIngredient res:Tabel`
- `res:Ojja gt:contientIngredient res:Carvi`
- `res:Ojja gt:contientIngredient res:Harissa`
- `res:Ojja gt:contientIngredient res:Oeuf`
- `res:RouzJerbi gt:contientIngredient res:Riz`
- `res:RouzJerbi gt:contientIngredient res:Tabel`
- `res:SaladeMechouia gt:contientIngredient res:Carvi`
- `res:SaladeMechouia gt:contientIngredient res:Poivron`

### rdfs2 — rdfs:domain — 4 triplet(s)

**Principe** : Si x P y et le domaine de P est C, alors x est de type C.

**Exemple de prémisses** : `res:HediJaziri gt:specialite res:Brik . gt:specialite rdfs:domain gt:Chef .`

**Triplets déduits** :

- `res:AmiraBenSalem rdf:type gt:Chef`
- `res:HediJaziri rdf:type gt:Chef`
- `res:MounirGharbi rdf:type gt:Chef`
- `res:SoniaKaroui rdf:type gt:Chef`

### rdfs3 — rdfs:range — 4 triplet(s)

**Principe** : Si x P y et le co-domaine de P est C, alors y est de type C.

**Exemple de prémisses** : `res:Ojja gt:epiceUtilisee res:Harissa . gt:epiceUtilisee rdfs:range gt:Epice .`

**Triplets déduits** :

- `res:Carvi rdf:type gt:Epice`
- `res:Cumin rdf:type gt:Epice`
- `res:Harissa rdf:type gt:Epice`
- `res:Tabel rdf:type gt:Epice`

### Chaîne rdfs3 puis rdfs9 — 4 triplet(s)

**Principe** : Une épice sans type devient gt:Epice (rdfs3), puis gt:Ingredient (rdfs9).

**Exemple de prémisses** : `res:Harissa (aucun type) → gt:Epice → gt:Ingredient`

**Triplets déduits** :

- `res:Carvi rdf:type gt:Ingredient`
- `res:Cumin rdf:type gt:Ingredient`
- `res:Harissa rdf:type gt:Ingredient`
- `res:Tabel rdf:type gt:Ingredient`

## 4. Les 8 requêtes SPARQL : sans / avec inférence

| Requête | Sans inférence | Avec inférence | Différence |
|---|---|---|---|
| Q1 — Plats principaux avec leur région, leur temps et leur difficulté | 7 | 7 | — |
| Q2 — Plats végétariens prêts en 45 minutes maximum | 4 | 4 | — |
| Q3 — Catalogue complet des plats (instances de la super-classe gt:Plat) | 0 | **14** | **+14** |
| Q4 — Statistiques par région : nombre de plats, temps moyen, plats végétariens | 5 | 5 | — |
| Q5 — Chefs, leur ville, leurs spécialités et combien sont des plats de leur région | 0 | **4** | **+4** |
| Q6 — Plats contenant un ingrédient donné | 3 | **4** | **+1** |
| Q7 — Ingrédients utilisés dans au moins 3 plats | 7 | **12** | **+5** |
| Q8 — Plats qu'aucun chef n'a en spécialité, avec leur lien DBpedia éventuel | 6 | 6 | — |

Les requêtes Q1, Q2, Q4 et Q8 ne changent pas : elles n'utilisent que des triplets écrits explicitement dans les données. Les autres dépendent de triplets déduits.

## 5. Détail des requêtes qui changent

### Q3 — Catalogue complet des plats (instances de la super-classe gt:Plat)

**Pourquoi ça change ?** Aucun plat n'est typé directement gt:Plat dans les données. Sans inférence : 0 résultat. Avec la règle rdfs9 (héritage du type par subClassOf) : les 14 plats.

**Sans inférence** (0) :

_Aucun résultat._

**Avec inférence** (14) :

| plat | nom | categorie | region | tempsPreparation | estVegetarien |
|---|---|---|---|---|---|
| res:AssidaZgougou | Assidat zgougou | Dessert | Tunis | 180 | true |
| res:Bambalouni | Bambalouni | Pâtisserie | Tunis | 120 | true |
| res:Brik | Brik à l'œuf | Entrée | Tunis | 20 | false |
| res:Chakchouka | Chakchouka | Plat principal | Nabeul | 35 | true |
| res:ChorbaFrik | Chorba frik | Soupe | Tunis | 60 | false |
| res:CouscousPoisson | Couscous au poisson | Plat principal | Sfax | 120 | false |
| res:CouscousAgneau | Couscous à l'agneau | Plat principal | Tunis | 150 | false |
| res:Kafteji | Kafteji | Plat principal | Tunis | 45 | true |
| res:Lablabi | Lablabi | Soupe | Tunis | 30 | true |
| res:Makroudh | Makroudh | Pâtisserie | Kairouan | 90 | true |
| res:Mloukhia | Mloukhia | Plat principal | Tunis | 240 | false |
| res:Ojja | Ojja merguez | Plat principal | Tunis | 30 | false |
| res:RouzJerbi | Riz djerbien | Plat principal | Médenine (Djerba) | 90 | false |
| res:SaladeMechouia | Salade méchouia | Entrée | Nabeul | 40 | true |

Lignes nouvelles ou modifiées grâce à l'inférence : 14

### Q5 — Chefs, leur ville, leurs spécialités et combien sont des plats de leur région

**Pourquoi ça change ?** Dans les données, les chefs sont seulement des foaf:Person. Sans inférence : 0 résultat. Avec la règle rdfs2 (rdfs:domain de gt:specialite = gt:Chef) : les 4 chefs.

**Sans inférence** (0) :

_Aucun résultat._

**Avec inférence** (4) :

| chef | nom | ville | specialites | nbSpecialites | nbPlatsLocaux |
|---|---|---|---|---|---|
| res:HediJaziri | Hédi Jaziri | Tunis | Brik à l'œuf, Lablabi, Ojja merguez | 3 | 3 |
| res:AmiraBenSalem | Amira Ben Salem | Sfax | Couscous au poisson, Makroudh | 2 | 1 |
| res:SoniaKaroui | Sonia Karoui | Nabeul | Salade méchouia, Chakchouka | 2 | 2 |
| res:MounirGharbi | Mounir Gharbi | Médenine (Djerba) | Riz djerbien | 1 | 1 |

Lignes nouvelles ou modifiées grâce à l'inférence : 4

### Q6 — Plats contenant un ingrédient donné

**Pourquoi ça change ?** Pour l'Ojja, l'œuf est écrit avec gt:ingredientPrincipal (et non gt:contientIngredient). Sans inférence : 3 plats. Avec la règle rdfs7 (subPropertyOf) : 4 plats, l'Ojja apparaît.

**Sans inférence** (3) :

| plat | nom | nomIngredient |
|---|---|---|
| res:Brik | Brik à l'œuf | Œuf |
| res:Chakchouka | Chakchouka | Œuf |
| res:Kafteji | Kafteji | Œuf |

**Avec inférence** (4) :

| plat | nom | nomIngredient |
|---|---|---|
| res:Brik | Brik à l'œuf | Œuf |
| res:Chakchouka | Chakchouka | Œuf |
| res:Kafteji | Kafteji | Œuf |
| res:Ojja | Ojja merguez | Œuf |

Lignes nouvelles ou modifiées grâce à l'inférence : 1

### Q7 — Ingrédients utilisés dans au moins 3 plats

**Pourquoi ça change ?** Les ingrédients principaux et les épices deviennent aussi des gt:contientIngredient (règle rdfs7). Sans inférence : 7 ingrédients. Avec inférence : 12 (Harissa, Semoule, Poivron, Tabel, Carvi apparaissent).

**Sans inférence** (7) :

| ingredient | nom | nbPlats |
|---|---|---|
| res:HuileOlive | Huile d'olive | 7 |
| res:Tomate | Tomate | 7 |
| res:Ail | Ail | 4 |
| res:Agneau | Agneau | 3 |
| res:Oignon | Oignon | 3 |
| res:PoisChiches | Pois chiches | 3 |
| res:Oeuf | Œuf | 3 |

**Avec inférence** (12) :

| ingredient | nom | nbPlats |
|---|---|---|
| res:Harissa | Harissa | 7 |
| res:HuileOlive | Huile d'olive | 7 |
| res:Tomate | Tomate | 7 |
| res:Ail | Ail | 4 |
| res:Carvi | Carvi (karouia) | 4 |
| res:PoisChiches | Pois chiches | 4 |
| res:Tabel | Tabel (coriandre en poudre) | 4 |
| res:Oeuf | Œuf | 4 |
| res:Agneau | Agneau | 3 |
| res:Oignon | Oignon | 3 |
| res:Poivron | Poivron | 3 |
| res:Semoule | Semoule | 3 |

Lignes nouvelles ou modifiées grâce à l'inférence : 7

