# Pitch : contenu des slides

> Format visé : ~5 min de pitch + démo. Chaque slide a son texte **à l'écran** (court) et ce qu'on **dit** (notes orateur).
> Les `[TODO]` sont des chiffres à sortir d'un run avant de figer les slides.

---

## 0. Le fil rouge (à garder en tête, pas une slide)

Tout le monde va arriver avec un graphe de dépendances et un dashboard. On ne gagne pas sur « on a plus de features », on gagne sur une phrase :

> **« On ne vous montre pas un risque. On vous dit quoi faire, et on vous prouve qu'on avait raison la dernière fois. »**

Trois piliers, répétés du hook au closing :
1. **Leur question, leurs mots** : combien je perds, en combien de temps, je reste ou je sors. Pas un score de risque.
2. **Prouvé sur le passé** : le backtest du 25 août 2026, 13 emprunteurs prédits, les 13 mêmes liquidés.
3. **Honnête sur ce qu'on ne sait pas** : on n'invente pas de probabilité de hack, on donne le seuil (p\*) à partir duquel sortir paie.

---

## 1. Hook : « Voici ce que votre client achète vraiment »

**À l'écran**
- Plein écran : le graphe du vault Belem RWA EURCV (`graph --vault 0xD6d4…48Ec`), toutes les dépendances dépliées.
- Un seul compteur en haut : **[TODO : N] contrats, [N] oracles/feeds, [N] marchés frères, [N] admins.**

**À dire**
> « Votre client voit une ligne : un vault EURCV, un APY. Voici ce qu'il y a derrière cette ligne. »
> *(pause, laisser le graphe respirer)*
> « Dans ce graphe, un feed NAV n'a pas été mis à jour depuis 17,5 jours. Un seul emprunteur porte 22 % du vault. Et tout ça est invisible depuis l'interface Morpho. »
> « Question simple : si mGLOeuro est marqué −30 % demain matin, combien perd votre client, en combien de temps, et doit-il sortir ? Aujourd'hui, personne ne peut répondre en moins d'une journée. Nous, en 3 secondes. »

**Pourquoi ça marche** : on ne parle pas de DeFi en général, on parle *de leur vault*, avec deux faits précis qu'ils ne connaissaient peut-être pas. Ça les fait se pencher en avant.

> ⚠️ À vérifier avant : que le vault 0xD6d4… est bien curaté par Belem, que le graphe est enregistré (sinon `graph --vault … --record` en amont), et re-confirmer les chiffres « 17,5 jours » et « 22 % » sur le run du jour.

---

## 2. Proposition de valeur : pas une liste, trois promesses

### Slide 2a : « Une décision, pas un dashboard »

**À l'écran**
> Un incident touche une dépendance.
> → **Combien** vous perdez. **Quand** ça arrive. **Rester ou sortir.**

**À dire**
> « Les outils de risque vous donnent des scores, des couleurs, des alertes. Le curator, lui, doit prendre une décision : je sors ou je reste, sachant que sortir coûte cher et c'est certain, et que rester est gratuit mais incertain. C'est exactement la question du brief, et notre outil répond à cette question-là, en une ligne : STAY, REDUCE ou EXIT, avec le montant. »

### Slide 2b : « On ne vous invente pas de probabilité »

**À l'écran**
> « Sortir paie si la probabilité de l'incident sur 30 jours dépasse **7,92 %**. »
> Prix de la couverture Nexus Mutual : 1,2 %–13,7 %/an.

**À dire**
> « Tout le monde est tenté de vous sortir une probabilité de hack. Elle est fausse, et vous le savez. Nous, on renverse la question : voici le seuil au-dessus duquel sortir vaut le coût. Et pour vous aider à juger, voici ce que le marché de l'assurance facture pour ce risque. La décision reste la vôtre, mais elle devient chiffrée. »

**Pourquoi c'est un avantage** : c'est ce qui nous distingue d'une équipe qui affiche « risque : 23 % ». Un jury de gestionnaires de risque se méfie des chiffres sortis du chapeau ; montrer qu'on sait ce qu'on ne sait pas, c'est un signal de sérieux.

### Slide 2c : « Les dépendances qu'on ne voit pas »

**À l'écran**
> Un oracle à prix constant ne liquide personne.
> → La perte tombe sur **les prêteurs**, c'est-à-dire vos clients.

**À dire**
> « Un graphe de dépendances, plusieurs équipes en auront un. La différence, c'est qu'on sait ce que chaque arête *fait* au moment du choc. Un oracle NAV ne bouge pas quand le token décroche : les emprunteurs ne sont pas liquidés, c'est le vault qui absorbe. Le choc se propage aussi aux marchés frères qui partagent un feed ou un collatéral, et nos règles de propagation sont dans un fichier que votre équipe peut lire et modifier. Pas de boîte noire. »

---

## 3. Démo (≈ 2 min, offline, sur enregistrements mainnet)

> Tout tourne **offline sur des enregistrements mainnet** : pas de dépendance au wifi ni au RPC le jour J. Le dire, c'est aussi un argument de crédibilité (reproductible).

**Étape 1 : le graphe** (déjà vu dans le hook, on clique)
- Cliquer sur le feed NAV mGLOeuro : l'amont/aval s'allume, le panneau risque affiche `STALE`.

**Étape 2 : l'incident**
```bash
uv run python -m riskdep analyze --vault 0xd6d4b804014ef27836dbe9f8f6bf6c71251548ec --shock token=mGLOeuro:0.30
```
- Montrer 3 lignes, pas plus : la perte par marché, « how fast » (à la publication du NAV), le verdict.
- `[TODO : coller les 3 lignes exactes du run]`

**Étape 3 : l'arbitrage du brief, avec leur propre exemple**
```bash
uv run python -m riskdep analyze --book examples/brief-ten-pockets.json --shock token=mGLOeuro:0.30 --exit-cost 0.11 --conditional
```
- La ligne à montrer : *« Sortir de Belem RWA EURCV coûte 110 000 USD à coup sûr, contre 53 445 économisés si l'incident arrive : STAY. »*
- Puis la distribution : *« rester perd 52 067 USD en moyenne, 99e percentile 352 195 ; rester est pire dans 18 % des 10 000 chemins »*.

> **À dire** : « Notez que l'outil dit **STAY**. Un outil de risque qui crie toujours EXIT ne sert à rien : il faut qu'il sache aussi vous dire de ne pas paniquer. »
> → C'est un moment fort : contre-intuitif, et ça montre qu'on a modélisé le coût de sortie, pas juste la peur.

**Étape 4 (option, si le temps) : la crise en direct sur fork**
- `scripts/fork/crisis-belem.sh` : markdown −10 % de l'émetteur, liquidation, bank run, upgrade du feed programmé 48 h sur le timelock Midas.
- Montrer l'alerte Telegram qui arrive : la cause, la perte et EXIT/STAY en haut du message.
- Message : « et en production, vous n'avez pas besoin de lancer la commande, c'est elle qui vous appelle, 48 h *avant* que l'upgrade n'atterrisse. »

> ⚠️ Ne pas montrer les deux alertes `critical` du mock web : elles sont fabriquées. Utiliser le fork ou le replay `--record-as fork-belem`.

### Slide 3b : « C'est joli, mais est-ce juste ? » (le backtest)

**À l'écran**

| 25 août 2026, PT-reUSD/USDC | Prédit | Réel |
|---|---|---|
| Positions liquidées | 13 | 13, **les mêmes emprunteurs** |
| Dette liquidée | 35,46 M | 35,19 M (**−0,8 %**) |
| Bad debt | 0 | 0 |

+ crash du 10/10/2025 : **aucun emprunteur liquidé manqué** sur les 6 marchés les plus touchés.

**À dire**
> « On a rejoué un vrai incident. On a pris l'état de la chaîne 60 blocs avant, appliqué la chute de l'oracle, et comparé notre prédiction aux 33 liquidations réelles. Mêmes emprunteurs, dette à moins de 1 %. On vous dit aussi où on se trompe : dans un crash rapide on surestime le nombre de liquidations, parce que les liquidateurs arrivent après la mèche. »

**Pourquoi c'est notre meilleure carte** : c'est la seule slide qu'une équipe concurrente ne peut pas improviser. Si on ne garde qu'un chiffre du pitch, c'est **13/13**.

---

## 4. Impact pour Belem Capital

**À l'écran** (trois colonnes, chacune = un moment de la vie du curator)

| Avant d'allouer | Pendant la vie du vault | Le jour de la crise |
|---|---|---|
| Voir tout ce dont dépend un marché avant d'y mettre le capital des clients | Être alerté des changements qui comptent : feed périmé, upgrade programmé, emprunteur trop concentré | Une décision chiffrée en secondes, défendable devant le client |

**À dire**
> « Pour Belem, concrètement :
> - **Avant** : vous auditez un marché RWA en quelques minutes, pas en quelques jours, et vous voyez les admins, les timelocks, les marchés frères.
> - **Pendant** : vous apprenez qu'un upgrade est programmé sur le timelock Midas 48 h avant qu'il ne prenne effet, pas après.
> - **Le jour J** : vous expliquez à votre client pourquoi vous êtes restés ou sortis, avec des chiffres. Et ça, c'est votre métier de curator : la confiance de vos déposants. »

Angle business à glisser : **la transparence est un argument commercial pour Belem**. Un curator qui peut montrer ce graphe et ce verdict à ses clients se différencie des autres curators. Ce n'est pas seulement un outil interne, c'est un argument de vente pour eux.

---

## 5. Closing

**À l'écran**
> **Combien. Quand. Rester ou sortir.**
> Prouvé sur le 25 août : 13/13.
> *[nom de l'équipe] · repo · contact*

**À dire**
> « Votre client voyait une ligne. Vous, vous voyez maintenant tout ce qu'il y a derrière, et vous savez quoi faire quand l'une de ces dépendances casse. On l'a testé sur le passé, ça marche sur vos vaults aujourd'hui, et ça tourne sans clé, sur des données publiques. Merci. »

Boucler sur l'image du hook : réafficher le graphe, cette fois avec le chemin du choc allumé en rouge. Même image, mais maintenant on la comprend.

---

## Annexe : brainstorm, comment tourner le pitch à notre avantage

**Ce que les autres équipes vont probablement montrer** : un graphe, un dashboard, des alertes, peut-être un score de risque. Donc ne pas *vendre* ces éléments, les *utiliser* comme décor.

**Nos angles différenciants, du plus fort au plus faible :**
1. **Le backtest** (13/13, −0,8 %). Personne d'autre n'aura validé contre des événements réels. À placer juste après la démo, comme réponse à l'objection « c'est joli, mais est-ce juste ».
2. **L'outil peut dire STAY.** Contre-intuitif, mémorable, prouve qu'on a modélisé le coût de sortie (11 %) et pas juste le risque.
3. **p\* au lieu d'une probabilité inventée** + référence Nexus. Parle directement à des gens du risque, qui détestent les faux chiffres.
4. **Leur vault, leurs tokens, leur exemple du brief.** Chaque chiffre montré vient de Belem ou du brief, jamais d'un exemple générique.
5. **Détection en amont** : l'upgrade est vu au moment où il est programmé sur le timelock, pas quand il atterrit. Des heures d'avance.
6. **Règles éditables, pas de boîte noire** (`registry.json`). Pour un curator, un modèle qu'on peut auditer vaut plus qu'un modèle opaque.

**Pièges à éviter :**
- Énumérer les 5 modes (analyze/watch/graph/shock/notify) : c'est la liste de features qu'on veut éviter. Le jury n'a pas besoin de connaître les noms des commandes.
- Montrer le terminal en entier : n'afficher que 2-3 lignes surlignées par étape, ou passer par l'UI web.
- Trop de chiffres : un chiffre fort par slide maximum.
- Survendre : dire ce qui n'est pas testé (la chute de l'oracle elle-même, le squeeze sur Pendle) renforce la crédibilité au lieu de l'affaiblir. Une phrase suffit.

**Questions du jury à préparer :**
- « D'où vient la probabilité ? » → on n'en donne pas, p\* + Nexus.
- « Ça marche hors Morpho ? » → Morpho Blue + Vault V2 + Pendle aujourd'hui ; le moteur de propagation est générique (règles sur les arêtes du graphe).
- « Et si le RPC tombe ? » → cross-check avec deux RPC indépendants, alerte critique si les hashes divergent.
- « Pourquoi pas du temps réel via websocket ? » → doc `websocket-vs-polling.md`, polling 12 s à 2 blocs de la tête.
