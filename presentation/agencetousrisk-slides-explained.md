# Présentation agencetousrisk : explication slide par slide

Le support : [slides.fuca.ch/agencetoutrisk](https://slides.fuca.ch/agencetoutrisk/slides.html) (9 slides, lu le 2026-10-11). Pour chaque slide : ce qu'elle montre, comment lire les chiffres, ce qu'on peut dire, et deux questions qu'un juge technique de Belem pourrait poser, avec une réponse. Le fil rouge est un seul vault, **RockawayX USDC Yield** (`0xE018…1965`, 18,44M USDC alloués), et un seul incident, **strUSD −30 %**.

Les chiffres viennent de `riskdep` : le graphe (`graph`), l'incident (`analyze --vault … --shock token=strUSD:0.3`) et le backtest (`backtest`). Les améliorations proposées sont reprises dans `docs/analysis/GAP4.md`.

## Vocabulaire minimum

| Terme | En une phrase |
|---|---|
| Vault | un pot commun de dépôts USDC, prêté par un curator sur plusieurs marchés Morpho |
| Marché | un prêt isolé : on emprunte des USDC contre un collatéral (strUSD, PT-reUSD…) |
| Oracle | le contrat qui donne au marché le prix du collatéral |
| LLTV | le seuil de liquidation : au-delà de ce ratio dette ÷ collatéral, la position est liquidée |
| Bad debt | la dette qu'un collatéral ne couvre plus : elle tombe sur les prêteurs, donc les déposants du vault |
| p\* | la probabilité de l'incident au-dessus de laquelle sortir rapporte plus que ça ne coûte |

---

## Slide 1 · RockawayX USDC Yield

**Ce qu'elle montre.** Un seul point : le vault. C'est ce que voit un déposant sur l'interface de Morpho : un nom, un rendement, un montant.

**À dire.** « Voici ce que voit un déposant : un vault, un rendement. Rien sur ce qui se trouve derrière. »

**Rôle.** Elle prépare le contraste avec la slide 2. Rester dessus deux ou trois secondes.

**Questions d'un juge technique**

**1. Pourquoi partir du vault et pas de la position d'un déposant ?**

Le vault est l'unité que gère un curator, et le risque d'un déposant est celui des marchés du vault, au prorata de sa part. L'outil sait aussi partir d'une adresse : `watch --user` retrouve toutes les positions Morpho d'une adresse (emprunts Blue et dépôts en Vault V2) et les surveille ensemble.

**2. Un Vault V2 passe par des adapters. Vous voyez ce qui est derrière chaque adapter ?**

Oui pour les adapters vers Morpho Blue : l'outil lit la structure vault → adapters → marchés Blue, avec les caps et l'adapter de liquidité. Ce qui n'est pas lu on-chain : un dépôt direct en Vault V1 et les venues hors Morpho, comme Kamino sur Solana. Ces lignes-là sont déclarées dans `registry.json` et citées à côté du résultat, pas calculées.

---

## Slide 2 · RockawayX USDC Yield, le graphe

**Ce qu'elle montre.** Le même vault, avec tout ce dont il dépend, découvert automatiquement on-chain : 84 nœuds et 146 liens. Les six marchés où le vault prête sont nommés (PT-reUSD, PT-strUSD, strUSD, etrUSD, siUSD, PRIME, tous contre USDC), ainsi que strUSD et PT-strUSD. Derrière : les oracles, les feeds, les émetteurs, les ponts, les admins.

**Comment la lire.**
- À gauche le vault, au milieu ses marchés, à droite ce qui fixe le prix de chaque collatéral et qui le contrôle.
- Une couleur par type de nœud (actif, marché, oracle, admin…), les mêmes que dans le graphe de `riskdep`.

**À dire.** « Le même vault, vu par notre outil : 84 dépendances. Six marchés, et derrière chacun un oracle, un émetteur, parfois un pont ou une clé d'admin. Un problème sur n'importe lequel de ces points peut atteindre les déposants. »

**Questions d'un juge technique**

**1. Comment savez-vous que le graphe est complet ? Qu'est-ce qui manque ?**

La découverte suit la chaîne : allocation du vault, paramètres de chaque marché, composition de chaque oracle (feeds de base et de quote, taux de change de vaults ERC-4626), qui peut modifier chaque feed (owner, Safe, timelock), et les marchés frères qui partagent le même collatéral ou le même oracle. Ce qui manque :
- le collatéral réel hors chaîne d'un émetteur, lu seulement là où une source existe (Pharos, ou la comptabilité on-chain d'infiniFi, f(x) ou Sky) ;
- les autres chaînes ;
- les dépendances qu'aucun contrat ne déclare, comme un accord juridique.

**2. D'où viennent les données, et pourquoi leur faire confiance ?**

Des sources publiques sans clé : un RPC Ethereum public, les API Morpho, Pendle et DefiLlama. Deux contrôles tournent à chaque bloc :
- le hash du bloc est comparé à celui d'un second RPC ; un écart donne une alerte critique ;
- les chiffres de l'API Morpho sont comparés à l'état on-chain, avec 0,5 % de tolérance.

Chaque réponse est mise en cache : une analyse se rejoue hors ligne à l'identique, ce qui permet de la vérifier.

**Amélioration possible.** Le chemin de strUSD (six nœuds) est marqué dans le SVG pour passer en rouge, mais le style « shock » n'est pas activé sur cette slide. L'activer ferait le lien visuel avec l'incident des slides suivantes.

---

## Slide 3 · Logo agencetousrisk

**Rôle.** Transition entre le problème (on ne voit pas les dépendances) et la réponse (ce que l'outil calcule). Présenter l'équipe en une phrase, puis enchaîner.

**Questions d'un juge technique**

**1. L'outil tourne en continu ou à la demande ?**

Les deux :
- **En continu :** `watch` suit un vault bloc par bloc, toutes les 12 secondes, deux blocs derrière la tête de chaîne, et envoie les alertes sur Telegram.
- **À la demande :** `analyze` calcule un incident et la décision rester ou sortir ; `graph` et `shock` construisent le graphe et propagent une panne.

Une API et une application web présentent les mêmes résultats.

**2. Qu'est-ce qui est mesuré, et qu'est-ce qui est supposé ?**

**Mesuré on-chain :** les positions, les oracles, les seuils, la liquidité disponible, l'historique des prix des feeds.

**Supposé :** les probabilités a priori (hacks, depegs), les paramètres de la simulation conditionnelle, le coût de sortie quand il n'est pas mesurable.

Chaque hypothèse est écrite dans `registry.json` avec sa justification, pour pouvoir être discutée.

---

## Slide 4 · Rester ou sortir ?

**Le cadre.** strUSD perd 30 %. On se place du côté du premier déposant de RockawayX USDC Yield : 7,15M USDC, 39 % du vault. Cinq questions, cinq chiffres :

| Question | Réponse | D'où vient le chiffre |
|---|---|---|
| Si je reste, je perds combien ? | **4,75 %** | la perte du vault : 875 531 USDC sur 18,44M, partagée par tous les déposants |
| Si je sors, je perds combien ? | **0,48 %** | ce qui ne peut pas sortir tout de suite (le vault n'a pas assez de liquidité pour 7,15M d'un coup) |
| Combien je laisse sur la table ? | **6,28 %/an** | le rendement du vault que je perds en sortant |
| Combien coûte la couverture ? | **2,33 %/an** | le prix d'une assurance Nexus Mutual sur Tori Finance, l'émetteur de strUSD |
| À partir de quel risque je sors ? | **12,10 % sur 30 jours** | p\*, détaillé à la slide 5 |

**À dire.** « Le brief demande une décision rester ou sortir. La voici en cinq chiffres. Si strUSD perd 30 %, rester coûte 4,75 %, sortir en premier 0,48 %. Mais sortir a un prix certain : le rendement. La vraie question est donc : à partir de quelle probabilité de l'incident est-ce que je sors ? Réponse : 12 % sur 30 jours. »

**Questions d'un juge technique**

**1. Comment obtenez-vous 4,75 % ? Le choc est-il propagé à travers les dépendances ?**

Le choc est une dévalorisation de strUSD que tous les oracles voient, comme une baisse de valeur publiée par l'émetteur. Il est appliqué à chaque marché dont le collatéral est strUSD ou un jeton construit dessus. Pour chaque emprunteur de ces marchés, le modèle de liquidation de Morpho calcule ce qui est liquidé et la dette que le collatéral ne couvre plus. Cette bad debt est la perte du vault : 875 531 USDC, soit 4,75 % de ses 18,44M. Quand le graphe du vault est enregistré, le moteur de propagation porte le choc à travers les jetons enveloppés.

**2. Pourquoi perd-on encore 0,48 % en sortant ? Vous supposez que ce déposant sort avant les autres ?**

Oui, c'est le scénario « sortir en premier », et il est dit comme tel. Le déposant retire ce que le vault peut payer tout de suite : sa trésorerie et la liquidité libre de ses marchés. Le reste, environ 0,7M sur 7,15M, reste dans le vault et subit la perte. S'il n'est pas le premier, il recule dans la file : l'outil calcule la perte selon la position dans la file de sortie (`exit_queue.py`).

---

## Slide 5 · Sortir paie au-dessus de p\*

**Ce qu'elle montre.** D'où vient le 12,10 %.

$$
p^\star = \frac{\text{coût certain de sortir}}{\text{perte évitée en sortant}} = \frac{36\,900}{339\,509 - 34\,538} \approx 12{,}10\ \%
$$

- **Coût de sortir :** 36 900 USDC, le rendement perdu sur 30 jours (7,15M × 6,28 %/an × 30/365).
- **Perte évitée :** 339 509 si je reste, moins 34 538 si je sors en premier (chiffres de la slide 7).
- **Couverture :** Nexus Mutual assure Tori Finance pour 2,33 % par an.

**Comment la lire.** On n'invente pas la probabilité de l'incident, d'où le titre « pas de probabilité inventée ». On calcule le seuil, et c'est au curator de dire s'il pense que le risque est au-dessus ou en dessous.

**À dire.** « Nous ne prétendons pas connaître la probabilité que strUSD perde 30 %. Nous donnons le seuil : si vous pensez que c'est plus de 12 % sur 30 jours, sortez. Pour vous situer, le marché de l'assurance prend 2,33 % par an pour couvrir Tori. »

**Questions d'un juge technique**

**1. Le coût de sortir n'est que le rendement perdu ? Pas de gas, de slippage, de coût de redéploiement ?**

Retirer d'un vault Morpho se fait au prix de la part, sans slippage, et le gas est négligeable à cette taille. Le coût retenu est le rendement du vault perdu sur l'horizon. C'est prudent : l'argent retiré peut être placé ailleurs, donc le vrai coût est plus bas, et p\* aussi. Quand la sortie a un coût réel, par exemple vendre un PT dans un pool, il est mesuré par des cotations, ou donné à la main avec `--exit-cost`.

**2. Comparer p\* à la prime Nexus, c'est légitime ? Nexus couvre une faille, pas une baisse de 30 %.**

Non, ce n'est pas la même chose, et l'outil ne s'en sert pas comme d'une entrée. La prime Nexus est une vue extérieure : ce que le marché de l'assurance demande pour couvrir une défaillance de Tori, marge comprise. Elle sert d'ordre de grandeur à côté de p\*. Ramené à l'année, p\* vaut environ 79 % : il faudrait croire le risque plus de trente fois supérieur au prix de l'assurance pour sortir avant l'incident.

**Amélioration possible.** Afficher aussi p\* par an (≈ 79 %/an) à côté des 2,33 %/an. Comparer un chiffre sur 30 jours à un chiffre par an oblige le public à faire la conversion.

---

## Slide 6 · Les dépendances qu'on ne voit pas

**Ce qu'elle montre.** L'allocation du vault par marché, lue on-chain, colorée selon l'oracle : rouge pour un **prix constant**, bleu pour un prix qui **suit le marché**. 50 % du vault (9,14M sur 18,44M) est sur des oracles à prix constant.

| Marché | Alloué | Oracle |
|---|---|---|
| PT-reUSD/USDC | 9,30M | suit le marché (TWAP Pendle) |
| strUSD/USDC | 4,91M | prix constant : valeur publiée par l'émetteur (RedStone « fundamental ») |
| siUSD/USDC | 2,36M | prix constant : taux de change du vault infiniFi × un feed fixé à 1,0 |
| PRIME/USDC | 1,51M | prix constant : taux qui ne fait que monter (intérêts) |
| PT-strUSD/USDC | 0,26M | prix constant : formule de décote linéaire jusqu'à l'échéance |
| etrUSD/USDC | 0,11M | prix constant : valeur publiée par l'émetteur |

**Pourquoi c'est important.**
- Un oracle qui suit le marché baisse avec le collatéral : les liquidations se déclenchent à temps, les prêteurs sont protégés.
- Un oracle à prix constant ne bouge pas si le marché chute : personne n'est liquidé, des emprunteurs peuvent même continuer à emprunter. La perte arrive d'un coup quand l'émetteur publie la nouvelle valeur. À ce moment le collatéral ne couvre plus la dette, et la bad debt tombe sur les déposants.

**À dire.** « La moitié de ce vault est prêtée contre des collatéraux dont l'oracle ne suit pas le marché. Si strUSD chute sur le marché, l'oracle continue d'afficher 1. Personne n'est liquidé, et la perte arrive d'un coup, sur les prêteurs. Rien de tout ça n'apparaît sur la page du vault. »

**Questions d'un juge technique**

**1. Comment classez-vous un oracle en « prix constant » ? Quel risque d'erreur ?**

Chaque entrée de l'oracle est examinée dans cet ordre :
- **sa structure :** un taux de change ERC-4626, ou un oracle Pendle à décote linéaire (`baseDiscountPerYear`) ;
- **son historique de rounds :** des rounds qui ne baissent jamais indiquent un taux qui accumule des intérêts, une réponse inchangée un prix fixe, et exactement 1,0 sans historique une valeur codée en dur ;
- **son nom :** « FUNDAMENTAL », « exchange rate ».

Une entrée que rien ne classe est marquée « non classée », jamais devinée. Le risque principal vient des noms : un feed mal nommé peut être mal classé. C'est pourquoi la structure et l'historique passent en premier.

**2. Un prix constant protège aussi des liquidations injustes, comme le montre la slide 8. Pourquoi est-ce un risque ?**

C'est un compromis, et il dépend du côté où l'on se trouve. Pour l'emprunteur, c'est une protection contre le bruit et la manipulation. Pour le prêteur, donc le déposant du vault, c'est une exposition : la perte d'un depeg ne déclenche aucune liquidation et lui revient en entier. Pire, tant que l'oracle surévalue le collatéral, la liquidité libre du marché peut être empruntée contre lui. L'outil calcule ce seuil, le « drain threshold ». Un curator est du côté prêteur, d'où la couleur rouge.

**Amélioration possible.** Nommer le vault sur la slide (« RockawayX USDC Yield, 18,44M alloués »).

---

## Slide 7 · Même incident, deux verdicts

**En bref.** Cette slide montre que la bonne décision ne dépend pas seulement de l'incident, mais de la façon dont on peut sortir. Le même incident (strUSD −30 %) donne deux verdicts opposés. La poche du brief doit vendre avec 11 % de décote : sortir lui coûte 110 000, plus que les 43 692 que ça lui évite, donc elle reste (STAY). Le premier déposant du vault, lui, retire ses USDC au prix plein avant que la perte n'arrive dans le prix de la part : sortir lui évite environ 305 000 de perte pour le seul coût du rendement perdu, donc il sort (EXIT). Le bas de la slide confirme ce choix sur 10 000 scénarios : rester est pire dans 86 % des cas.

**Ce qu'elle montre.** Le même incident, strUSD −30 % (le vault perd 875 531 USDC, 4,75 %), vu par deux détenteurs différents :

| | Poche du brief | Premier déposant |
|---|---|---|
| Taille | 1M | 7,15M (39 % du vault) |
| Comment sortir | vendre avec 11 % de décote (hypothèse du brief) | retirer du vault au prix plein, avant que la perte n'arrive dans le prix de la part |
| Coût de sortir | 110 000, certain | le rendement perdu seulement |
| Économisé en sortant | 43 692 | 339 509 − 34 538 = 304 971 |
| Perte si je reste / si je sors | | 339 509 / 34 538 |
| Verdict | **STAY** | **EXIT** |

En bas, la distribution pour le déposant, sur 10 000 scénarios où l'incident s'aggrave ou se résorbe : perte moyenne en restant de 298 985 USDC, 923 216 dans le pire 1 %, et rester est pire dans 86 % des cas.

**À dire.** « Même incident, deux réponses opposées. La poche du brief doit vendre avec 11 % de décote : sortir lui coûte plus que ce que ça sauve, elle reste. Un déposant de vault Morpho, lui, peut retirer au prix plein tant que la perte n'est pas comptabilisée : il sort. La décision dépend de la façon dont on peut sortir, pas seulement de l'incident. »

**Questions d'un juge technique**

**1. Les 10 000 chemins : d'où viennent les paramètres, et sont-ils calibrés ?**

Ils sont dans `registry.json` (`conditional`), avec leur justification, et ce sont des jugements, pas encore une calibration :
- 30 % de chances que la baisse se résorbe en partie ;
- sinon une baisse qui tient ou s'aggrave, de dispersion σ = 0,35 ;
- une probabilité qu'aucun liquidateur n'agisse, selon la profondeur de la route de sortie du collatéral.

Les pertes elles-mêmes ne sont pas modélisées : elles viennent de vraies simulations de l'incident à 0,25× jusqu'à 2× la baisse. Le verdict EXIT n'en dépend pas : il vient du calcul déterministe de p\*. La distribution ne sert qu'à montrer la queue.

**2. « Sortir en premier au prix plein » : et si tous les déposants sortent en même temps ?**

C'est exactement ce que mesure le 34 538 : la part que même le premier ne peut pas retirer, faute de liquidité. L'outil modélise la file de sortie. Chaque déposant passe dans l'ordre, sur la trésorerie du vault et la liquidité libre de ses marchés. Celui qui sort après les autres trouve moins de liquidité et perd davantage. Le résultat donne la perte selon la position dans la file, pas seulement pour le premier.

**Amélioration possible.** Remplacer « au pair » par « sans décote » ou « au prix plein », et étiqueter le 34 538 comme « perte restante » plutôt que comme un coût.

---

## Slide 8 · Backtest du 25 août 2026

**Le cadre.** « C'est joli, mais est-ce juste ? » On rejoue un vrai incident pour vérifier l'outil.

**L'incident.** Le 25 août 2026, un portefeuille achète du YT-reUSD sur Pendle pour 320 000 SY. Acheter du YT revient à vendre du PT dans le pool, donc le prix du PT baisse. L'oracle des deux marchés Morpho, qui lit une moyenne sur 15 minutes, suit avec retard et baisse de 2,45 % à 2,76 %. Les emprunteurs étaient tout près de leur seuil de 91,5 %, et cette baisse les a fait passer à 91,8–93,4 % : 33 liquidations, 36,1M de dette remboursée, pas de bad debt.

**Le test.** On lit l'état de la chaîne 12 minutes **avant** la première liquidation, on applique la baisse de l'oracle et on demande à l'outil qui sera liquidé.

| Marché | Positions (prédit / réel) | Dette (prédit / réel) | Bad debt |
|---|---|---|---|
| PT-reUSD/USDC | 13 / 13, mêmes emprunteurs | 35,46M / 35,19M | 0 / 0 |
| PT-reUSD/USDT | 7 / 7, mêmes emprunteurs | 1,89M / 0,96M | 0 / 0 |

**Comment la lire.**
- **Les positions :** exactement les mêmes emprunteurs, aucun oublié, aucun de trop. C'est le résultat principal.
- **La dette :** à gauche la dette *liquidable* (le maximum possible), à droite la dette *remboursée*. Morpho autorise les liquidations partielles. Sur USDT, trois positions ont été liquidées en partie, par petits morceaux, et les liquidateurs se sont arrêtés quand la position est redevenue saine. Le montant réel reste entre le minimum imposé par la règle de Morpho et le maximum, pour les 20 positions.
- **Pas de bad debt :** il aurait fallu dépasser environ 97,4 % de LTV ; la pire position était à 93,4 %. Le retard de l'oracle a décalé les liquidations sans créer de perte pour les prêteurs. Ce sont les emprunteurs qui ont payé : 945 796 de bonus aux liquidateurs.
- **Le lien avec le vault :** PT-reUSD/USDC est le premier marché de RockawayX USDC Yield (9,3M, la barre bleue de la slide 6).
- **La note du bas :** un deuxième backtest, le krach du 10 octobre 2025 sur les six marchés Morpho les plus touchés, ne manque aucun emprunteur liquidé.

**À dire.** « Pour vérifier, on a rejoué un vrai incident. Le 25 août, un achat de 320 000 dollars sur Pendle a fait baisser l'oracle de moins de 3 %, et 36 millions de dettes ont été liquidées. Depuis l'état de la chaîne douze minutes avant, l'outil prédit 13 sur 13 et 7 sur 7 : exactement les mêmes emprunteurs, et zéro bad debt, comme dans la réalité. »

**Questions d'un juge technique**

**1. Vous appliquez la baisse observée de l'oracle. N'est-ce pas circulaire ?**

Pour ce premier test, la baisse est une donnée : il vérifie « étant donné le mouvement de prix, qui est liquidé ». Un second test enlève cette donnée. Le pool Pendle est reconstruit depuis son état avant l'achat, avec les formules de Pendle :
- la vente observée de 5,43M de PT y fait baisser le prix de 2,36 %, contre 2,45 % et 2,76 % observés ;
- à ce niveau, l'outil prédit les mêmes 20 positions, aucune oubliée, aucune de trop ;
- en ajoutant la revente du collatéral saisi dans le pool, la baisse passe à 2,46 %, avec le même résultat.

**2. Un épisode de 20 positions, c'est peu. Comment se comporte le modèle ailleurs ?**

Le deuxième épisode est le krach du 10 octobre 2025 sur six marchés (Mog, PEPE, SPX, WBTC, wstETH). Aucun emprunteur liquidé n'est manqué, et pour WBTC/USDC la dette et le bonus sont à 2 % près. Les limites sont dites aussi :
- dans un krach rapide, le modèle prédit trop de positions : sur les 52 en trop de Mog, 36 ont été liquidées plus tard dans la nuit, quelques-unes défendues par leur emprunteur, le reste est de la poussière qu'aucun liquidateur ne prend ;
- la bad debt prédite au point bas est surestimée (Mog : 403k contre 22,7k réels), parce que les liquidateurs ont atteint beaucoup de positions après la mèche.

**Amélioration possible** (`GAP4.md` G4.3). Renommer la colonne en « Dette liquidable / remboursée » et afficher la fourchette : « 35,19M dans 8,05–35,46M », « 0,96M dans 0,33–1,89M ».

---

## Slide 9 · Impact pour Belem Capital

**Ce qu'elle montre.** Ce que l'outil apporte à un curator, à chaque moment de la vie d'un vault :

| Moment | Ce que l'outil donne | Où on l'a vu |
|---|---|---|
| Avant d'allouer | tout ce dont dépend un marché, avant d'y mettre le capital des clients | slides 2 et 6 |
| Pendant la vie du vault | des alertes sur ce qui compte : feed périmé, upgrade programmé, emprunteur trop concentré | la démo sur fork et le bot Telegram |
| Le jour de la crise | une décision chiffrée en secondes, défendable devant le client | slides 4, 5 et 7, validées par la slide 8 |

**À dire.** « Pour Belem Capital, ça couvre les trois moments d'un curator. Avant d'allouer : voir les 84 dépendances, pas seulement le rendement. Pendant : être alerté de ce qui compte, pas de tout. Le jour de la crise : une décision chiffrée en secondes, et un backtest qui montre qu'on peut la défendre. »

**Questions d'un juge technique**

**1. En production, quel délai entre un événement on-chain et l'alerte ? Et si la chaîne se réorganise ?**

La surveillance interroge la chaîne toutes les 12 secondes et lit deux blocs derrière la tête, donc une alerte part de l'ordre de 30 secondes à une minute après l'événement. Ces deux blocs de marge couvrent les réorganisations courantes ; une réorganisation plus profonde n'est pas gérée, et c'est écrit. Si l'outil redémarre, il reprend au dernier bloc traité sans en sauter, parce que le curseur est sauvegardé en dernier.

**2. Qu'est-ce que l'outil ne couvre pas encore pour un curator comme Belem ?**

- **Les autres chaînes :** l'outil lit Ethereum seulement ; Morpho sur les autres chaînes demande d'en faire un paramètre.
- **Les venues hors Morpho :** la ligne Kamino de Huma est citée depuis `registry.json`, pas lue ; Lista sur BSC n’est pas couverte.
- **Les positions confidentielles Zama :** le montant d'un déposant confidentiel doit venir de lui, car seul lui peut le déchiffrer.
- **Les probabilités a priori :** elles ne sont pas calibrées par protocole, d'où le choix de donner p\* plutôt qu'une probabilité inventée.

**Conclusion possible.** Revenir à la slide 1 : « Un déposant voit un point. Nous lui montrons ce qu'il y a derrière, et quoi faire quand ça casse. »
