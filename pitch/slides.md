---
marp: true
theme: agencetousrisk
paginate: true
header: '![agencetousrisk](../web/public/logo.png)'
title: agencetousrisk
---

<!-- _class: center -->
<!-- _header: '' -->
<!-- _paginate: false -->

<img class="logo" src="../web/public/logo.png" alt="agencetousrisk">

# Combien. Quand.<br>Rester ou sortir.

<p class="muted" style="margin-top:24px">DeFi Risk Dependency Challenge · Belem Capital · EPFL Hackathon 2026</p>

<!--
On ne vous montre pas un risque. On vous dit quoi faire, et on vous prouve qu'on avait raison la dernière fois.
-->

---

<p class="eyebrow">Vault Belem RWA EURCV</p>

## Ce que votre client achète vraiment

<div class="stats" style="margin-bottom:20px">
  <div class="stat"><div class="label">Nœuds</div><div class="value">112</div></div>
  <div class="stat"><div class="label">Oracles et feeds</div><div class="value">51</div></div>
  <div class="stat"><div class="label">Marchés frères</div><div class="value">26</div></div>
  <div class="stat"><div class="label">Admins</div><div class="value">4</div></div>
</div>

<svg class="graph" viewBox="0 0 1100 470" xmlns="http://www.w3.org/2000/svg"><path class="edge shock-path" d="M150 235 C207 235 207 70 264 70"/><path class="edge" d="M150 235 C207 235 207 180 264 180"/><path class="edge" d="M150 235 C207 235 207 290 264 290"/><path class="edge" d="M150 235 C207 235 207 400 264 400"/><path class="edge shock-path" d="M316 70 C387 70 387 50 458 50"/><path class="edge" d="M316 70 C459 70 459 90 602 90"/><path class="edge" d="M316 180 C387 180 387 160 458 160"/><path class="edge" d="M316 180 C459 180 459 200 602 200"/><path class="edge" d="M316 290 C387 290 387 270 458 270"/><path class="edge" d="M316 290 C459 290 459 310 602 310"/><path class="edge" d="M316 400 C387 400 387 380 458 380"/><path class="edge" d="M316 400 C459 400 459 420 602 420"/><path class="edge" d="M502 50 C652 50 652 30 802 30"/><path class="edge" d="M658 90 C733 90 733 115 808 115"/><path class="edge" d="M658 200 C733 200 733 220 808 220"/><path class="edge" d="M658 310 C733 310 733 220 808 220"/><path class="edge" d="M658 200 C733 200 733 320 808 320"/><path class="edge" d="M658 310 C733 310 733 320 808 320"/><path class="edge" d="M658 420 C733 420 733 320 808 320"/><path class="edge" d="M658 420 C733 420 733 420 808 420"/><g class="faint"><path class="edge" stroke-dasharray="4 4" d="M852 115 C930 115 930 190 960 190"/><path class="edge" stroke-dasharray="4 4" d="M852 220 C930 220 930 200 960 200"/><path class="edge" stroke-dasharray="4 4" d="M852 320 C930 320 930 210 960 210"/><rect class="node" x="960" y="176" width="130" height="48" rx="6"/><text x="1025" y="205">+ 26 marchés frères</text></g><rect class="node" x="0" y="205" width="150" height="60" rx="6"/><rect class="shock-ring" x="0" y="205" width="150" height="60" rx="6"/><circle cx="75" cy="235" r="6" fill="#0072B2"/><text x="75" y="283">Belem RWA EURCV</text><rect class="node" x="264" y="47" width="52" height="46" rx="6"/><rect class="shock-ring" x="264" y="47" width="52" height="46" rx="6"/><circle cx="290" cy="70" r="6" fill="#009E73"/><text x="290" y="111">mGLOeuro/EURCV</text><circle class="node" cx="480" cy="50" r="22"/><circle class="shock-ring" cx="480" cy="50" r="22"/><circle cx="480" cy="50" r="6" fill="#E69F00"/><text x="480" y="90">mGLOeuro</text><polygon class="node" points="602,90 616,66 644,66 658,90 644,114 616,114"/><circle cx="630" cy="90" r="6" fill="#CC79A7"/><text x="630" y="132">Oracle</text><rect class="node" x="264" y="157" width="52" height="46" rx="6"/><circle cx="290" cy="180" r="6" fill="#009E73"/><text x="290" y="221">cbBTC/EURCV</text><circle class="node" cx="480" cy="160" r="22"/><circle cx="480" cy="160" r="6" fill="#E69F00"/><text x="480" y="200">cbBTC</text><polygon class="node" points="602,200 616,176 644,176 658,200 644,224 616,224"/><circle cx="630" cy="200" r="6" fill="#CC79A7"/><text x="630" y="242">Oracle</text><rect class="node" x="264" y="267" width="52" height="46" rx="6"/><circle cx="290" cy="290" r="6" fill="#009E73"/><text x="290" y="331">WBTC/EURCV</text><circle class="node" cx="480" cy="270" r="22"/><circle cx="480" cy="270" r="6" fill="#E69F00"/><text x="480" y="310">WBTC</text><polygon class="node" points="602,310 616,286 644,286 658,310 644,334 616,334"/><circle cx="630" cy="310" r="6" fill="#CC79A7"/><text x="630" y="352">Oracle</text><rect class="node" x="264" y="377" width="52" height="46" rx="6"/><circle cx="290" cy="400" r="6" fill="#009E73"/><text x="290" y="441">wstETH/EURCV</text><circle class="node" cx="480" cy="380" r="22"/><circle cx="480" cy="380" r="6" fill="#E69F00"/><text x="480" y="420">wstETH</text><polygon class="node" points="602,420 616,396 644,396 658,420 644,444 616,444"/><circle cx="630" cy="420" r="6" fill="#CC79A7"/><text x="630" y="462">Oracle</text><polygon class="node" points="802,30 816,6 844,6 858,30 844,54 816,54"/><circle cx="830" cy="30" r="6" fill="#999999"/><text x="830" y="72">Midas RWA</text><polygon class="node" points="808,115 819,96 841,96 852,115 841,134 819,134"/><polygon class="warn-ring" points="808,115 819,96 841,96 852,115 841,134 819,134"/><circle cx="830" cy="115" r="6" fill="#CC79A7"/><text x="830" y="152">mGLOeuro/EUR</text><polygon class="node" points="808,220 819,201 841,201 852,220 841,239 819,239"/><circle cx="830" cy="220" r="6" fill="#CC79A7"/><text x="830" y="257">BTC / USD</text><polygon class="node" points="808,320 819,301 841,301 852,320 841,339 819,339"/><circle cx="830" cy="320" r="6" fill="#CC79A7"/><text x="830" y="357">EUR / USD</text><polygon class="node" points="808,420 819,401 841,401 852,420 841,439 819,439"/><circle cx="830" cy="420" r="6" fill="#CC79A7"/><text x="830" y="457">ETH / USD</text><text class="tag warn" x="830" y="167">STALE · 17,5 j</text><text class="tag crit shock-only" x="480" y="12">−30 %</text></svg>

<!--
Votre client voit une ligne : un vault EURCV, un APY. Voici ce qu'il y a derrière cette ligne.
(pause, laisser le graphe respirer)
Dans ce graphe, un feed NAV n'a pas été mis à jour depuis 17,5 jours. Un seul emprunteur porte 22 % du vault. Et tout ça est invisible depuis l'interface Morpho.
Question simple : si mGLOeuro est marqué −30 % demain matin, combien perd votre client, en combien de temps, et doit-il sortir ? Aujourd'hui, personne ne peut répondre en moins d'une journée. Nous, en 3 secondes.
-->

---

<p class="eyebrow">Un incident touche une dépendance</p>

## Une décision, pas un dashboard

<div class="cols" style="margin-top:24px">
  <div class="stat"><div class="label">Combien</div><div class="value">vous perdez</div></div>
  <div class="stat"><div class="label">Quand</div><div class="value">ça arrive</div></div>
  <div class="stat"><div class="label">Rester ou sortir</div><div class="value"><span class="verdict stay">STAY</span> <span class="verdict reduce">REDUCE</span> <span class="verdict exit">EXIT</span></div></div>
</div>

<!--
Les outils de risque vous donnent des scores, des couleurs, des alertes. Le curator, lui, doit prendre une décision : je sors ou je reste, sachant que sortir coûte cher et c'est certain, et que rester est gratuit mais incertain. C'est exactement la question du brief, et notre outil répond à cette question-là, en une ligne : STAY, REDUCE ou EXIT, avec le montant.
-->

---

<p class="eyebrow">Pas de probabilité inventée</p>

## Sortir paie au-dessus de p\*

<div class="split">
  <div class="stat prominent"><div class="label">p* · probabilité de l'incident sur 30 jours</div><div class="value">7<span class="m">,92 %</span></div></div>
  <div class="stat"><div class="label">Prix de la couverture Nexus Mutual</div><div class="value">1,2 – 13,7 <span class="m">% / an</span></div></div>
</div>

<!--
Tout le monde est tenté de vous sortir une probabilité de hack. Elle est fausse, et vous le savez. Nous, on renverse la question : voici le seuil au-dessus duquel sortir vaut le coût. Et pour vous aider à juger, voici ce que le marché de l'assurance facture pour ce risque. La décision reste la vôtre, mais elle devient chiffrée.
-->

---

<p class="eyebrow">Ce que chaque arête fait au moment du choc</p>

## Les dépendances qu'on ne voit pas

<svg class="graph" viewBox="0 0 1100 200" xmlns="http://www.w3.org/2000/svg" style="margin-top:24px">
<path class="edge" d="M220 90 L450 90"/><path class="edge" d="M650 90 L880 90"/>
<polygon class="node" points="120,90 155,50 225,50 260,90 225,130 155,130" transform="translate(-50 0)"/><circle cx="140" cy="90" r="8" fill="#CC79A7"/>
<text x="140" y="165" style="font-size:20px">Oracle à prix constant</text>
<rect class="node" x="510" y="50" width="80" height="80" rx="6"/><circle cx="550" cy="90" r="8" fill="#009E73"/>
<text x="550" y="165" style="font-size:20px">Aucun emprunteur liquidé</text>
<rect class="node" x="890" y="40" width="180" height="100" rx="6"/><rect class="shock-ring" x="890" y="40" width="180" height="100" rx="6" style="stroke:var(--critical)"/><circle cx="980" cy="90" r="8" fill="#0072B2"/>
<text x="980" y="165" style="font-size:20px">Perte sur les prêteurs</text>
</svg>

<p class="muted" style="margin-top:32px">Les prêteurs, c'est-à-dire vos clients. Règles de propagation lisibles et modifiables.</p>

<!--
Un graphe de dépendances, plusieurs équipes en auront un. La différence, c'est qu'on sait ce que chaque arête fait au moment du choc. Un oracle NAV ne bouge pas quand le token décroche : les emprunteurs ne sont pas liquidés, c'est le vault qui absorbe. Le choc se propage aussi aux marchés frères qui partagent un feed ou un collatéral, et nos règles de propagation sont dans un fichier que votre équipe peut lire et modifier. Pas de boîte noire.
-->

---

<p class="eyebrow">L'exemple du brief · mGLOeuro −30 %, sortie à 11 %</p>

## Rester ou sortir de Belem RWA EURCV <span class="verdict stay">STAY</span>

<div class="bars" style="margin:12px 0 48px">
  <div class="label">Coût de sortie, certain</div>
  <div class="bar" style="width:100%;background:var(--critical)"></div>
  <div class="num">110 000 <span class="m">USD</span></div>
  <div class="label">Économisé si l'incident arrive</div>
  <div class="bar" style="width:48.6%;background:var(--ok)"></div>
  <div class="num">53 445 <span class="m">USD</span></div>
</div>

<div class="stats">
  <div class="stat"><div class="label">Perte moyenne en restant</div><div class="value">52 067 <span class="m">USD</span></div></div>
  <div class="stat"><div class="label">99e percentile</div><div class="value">352 195 <span class="m">USD</span></div></div>
  <div class="stat"><div class="label">Rester est pire</div><div class="value">18 <span class="m">% des 10 000 chemins</span></div></div>
</div>

<!--
Démo offline, sur enregistrements mainnet : pas de dépendance au wifi ni au RPC.
Sortir de Belem RWA EURCV coûte 110 000 USD à coup sûr, contre 53 445 économisés si l'incident arrive : STAY.
Notez que l'outil dit STAY. Un outil de risque qui crie toujours EXIT ne sert à rien : il faut qu'il sache aussi vous dire de ne pas paniquer.
-->

---

<p class="eyebrow">C'est joli, mais est-ce juste ?</p>

## Backtest du 25 août 2026

<div class="split" style="grid-template-columns:auto 1fr">
  <div class="stat prominent"><div class="label">Emprunteurs liquidés</div><div class="value">13<span class="m">/13</span></div></div>
  <table>
    <thead><tr><th>PT-reUSD/USDC</th><th>Prédit</th><th>Réel</th></tr></thead>
    <tbody>
      <tr><td>Positions liquidées</td><td>13</td><td>13, les mêmes</td></tr>
      <tr><td>Dette liquidée</td><td>35,46 <span class="m">M</span></td><td>35,19 <span class="m">M</span> · −0,8 <span class="m">%</span></td></tr>
      <tr><td>Bad debt</td><td>0</td><td>0</td></tr>
    </tbody>
  </table>
</div>

<p class="muted" style="margin-top:40px">Crash du 10/10/2025 : aucun emprunteur liquidé manqué sur les 6 marchés les plus touchés.</p>

<!--
On a rejoué un vrai incident. On a pris l'état de la chaîne 60 blocs avant, appliqué la chute de l'oracle, et comparé notre prédiction aux liquidations réelles. Mêmes emprunteurs, dette à moins de 1 %. On vous dit aussi où on se trompe : dans un crash rapide on surestime le nombre de liquidations, parce que les liquidateurs arrivent après la mèche.
Si on ne garde qu'un chiffre du pitch, c'est 13/13.
-->

---

<p class="eyebrow">Impact pour Belem Capital</p>

## Chaque moment de la vie du curator

<table>
  <thead><tr><th>Avant d'allouer</th><th>Pendant la vie du vault</th><th>Le jour de la crise</th></tr></thead>
  <tbody><tr>
    <td>Tout ce dont dépend un marché, avant d'y mettre le capital des clients</td>
    <td>Alerté de ce qui compte : feed périmé, upgrade programmé, emprunteur trop concentré</td>
    <td>Une décision chiffrée en secondes, défendable devant le client</td>
  </tr></tbody>
</table>

<!--
Avant : vous auditez un marché RWA en quelques minutes, pas en quelques jours, et vous voyez les admins, les timelocks, les marchés frères.
Pendant : vous apprenez qu'un upgrade est programmé sur le timelock Midas 48 h avant qu'il ne prenne effet, pas après.
Le jour J : vous expliquez à votre client pourquoi vous êtes restés ou sortis, avec des chiffres. C'est votre métier de curator : la confiance de vos déposants.
Angle business : la transparence est un argument commercial. Un curator qui peut montrer ce graphe et ce verdict à ses clients se différencie.
-->

---

<!-- _class: shock -->

## Combien. Quand. Rester ou sortir.

<p class="muted">Prouvé sur le 25 août : <strong>13/13</strong> · agencetousrisk · repo · contact</p>

<svg class="graph" viewBox="0 0 1100 470" xmlns="http://www.w3.org/2000/svg"><path class="edge shock-path" d="M150 235 C207 235 207 70 264 70"/><path class="edge" d="M150 235 C207 235 207 180 264 180"/><path class="edge" d="M150 235 C207 235 207 290 264 290"/><path class="edge" d="M150 235 C207 235 207 400 264 400"/><path class="edge shock-path" d="M316 70 C387 70 387 50 458 50"/><path class="edge" d="M316 70 C459 70 459 90 602 90"/><path class="edge" d="M316 180 C387 180 387 160 458 160"/><path class="edge" d="M316 180 C459 180 459 200 602 200"/><path class="edge" d="M316 290 C387 290 387 270 458 270"/><path class="edge" d="M316 290 C459 290 459 310 602 310"/><path class="edge" d="M316 400 C387 400 387 380 458 380"/><path class="edge" d="M316 400 C459 400 459 420 602 420"/><path class="edge" d="M502 50 C652 50 652 30 802 30"/><path class="edge" d="M658 90 C733 90 733 115 808 115"/><path class="edge" d="M658 200 C733 200 733 220 808 220"/><path class="edge" d="M658 310 C733 310 733 220 808 220"/><path class="edge" d="M658 200 C733 200 733 320 808 320"/><path class="edge" d="M658 310 C733 310 733 320 808 320"/><path class="edge" d="M658 420 C733 420 733 320 808 320"/><path class="edge" d="M658 420 C733 420 733 420 808 420"/><g class="faint"><path class="edge" stroke-dasharray="4 4" d="M852 115 C930 115 930 190 960 190"/><path class="edge" stroke-dasharray="4 4" d="M852 220 C930 220 930 200 960 200"/><path class="edge" stroke-dasharray="4 4" d="M852 320 C930 320 930 210 960 210"/><rect class="node" x="960" y="176" width="130" height="48" rx="6"/><text x="1025" y="205">+ 26 marchés frères</text></g><rect class="node" x="0" y="205" width="150" height="60" rx="6"/><rect class="shock-ring" x="0" y="205" width="150" height="60" rx="6"/><circle cx="75" cy="235" r="6" fill="#0072B2"/><text x="75" y="283">Belem RWA EURCV</text><rect class="node" x="264" y="47" width="52" height="46" rx="6"/><rect class="shock-ring" x="264" y="47" width="52" height="46" rx="6"/><circle cx="290" cy="70" r="6" fill="#009E73"/><text x="290" y="111">mGLOeuro/EURCV</text><circle class="node" cx="480" cy="50" r="22"/><circle class="shock-ring" cx="480" cy="50" r="22"/><circle cx="480" cy="50" r="6" fill="#E69F00"/><text x="480" y="90">mGLOeuro</text><polygon class="node" points="602,90 616,66 644,66 658,90 644,114 616,114"/><circle cx="630" cy="90" r="6" fill="#CC79A7"/><text x="630" y="132">Oracle</text><rect class="node" x="264" y="157" width="52" height="46" rx="6"/><circle cx="290" cy="180" r="6" fill="#009E73"/><text x="290" y="221">cbBTC/EURCV</text><circle class="node" cx="480" cy="160" r="22"/><circle cx="480" cy="160" r="6" fill="#E69F00"/><text x="480" y="200">cbBTC</text><polygon class="node" points="602,200 616,176 644,176 658,200 644,224 616,224"/><circle cx="630" cy="200" r="6" fill="#CC79A7"/><text x="630" y="242">Oracle</text><rect class="node" x="264" y="267" width="52" height="46" rx="6"/><circle cx="290" cy="290" r="6" fill="#009E73"/><text x="290" y="331">WBTC/EURCV</text><circle class="node" cx="480" cy="270" r="22"/><circle cx="480" cy="270" r="6" fill="#E69F00"/><text x="480" y="310">WBTC</text><polygon class="node" points="602,310 616,286 644,286 658,310 644,334 616,334"/><circle cx="630" cy="310" r="6" fill="#CC79A7"/><text x="630" y="352">Oracle</text><rect class="node" x="264" y="377" width="52" height="46" rx="6"/><circle cx="290" cy="400" r="6" fill="#009E73"/><text x="290" y="441">wstETH/EURCV</text><circle class="node" cx="480" cy="380" r="22"/><circle cx="480" cy="380" r="6" fill="#E69F00"/><text x="480" y="420">wstETH</text><polygon class="node" points="602,420 616,396 644,396 658,420 644,444 616,444"/><circle cx="630" cy="420" r="6" fill="#CC79A7"/><text x="630" y="462">Oracle</text><polygon class="node" points="802,30 816,6 844,6 858,30 844,54 816,54"/><circle cx="830" cy="30" r="6" fill="#999999"/><text x="830" y="72">Midas RWA</text><polygon class="node" points="808,115 819,96 841,96 852,115 841,134 819,134"/><polygon class="warn-ring" points="808,115 819,96 841,96 852,115 841,134 819,134"/><circle cx="830" cy="115" r="6" fill="#CC79A7"/><text x="830" y="152">mGLOeuro/EUR</text><polygon class="node" points="808,220 819,201 841,201 852,220 841,239 819,239"/><circle cx="830" cy="220" r="6" fill="#CC79A7"/><text x="830" y="257">BTC / USD</text><polygon class="node" points="808,320 819,301 841,301 852,320 841,339 819,339"/><circle cx="830" cy="320" r="6" fill="#CC79A7"/><text x="830" y="357">EUR / USD</text><polygon class="node" points="808,420 819,401 841,401 852,420 841,439 819,439"/><circle cx="830" cy="420" r="6" fill="#CC79A7"/><text x="830" y="457">ETH / USD</text><text class="tag warn" x="830" y="167">STALE · 17,5 j</text><text class="tag crit shock-only" x="480" y="12">−30 %</text></svg>

<!--
Votre client voyait une ligne. Vous, vous voyez maintenant tout ce qu'il y a derrière, et vous savez quoi faire quand l'une de ces dépendances casse. On l'a testé sur le passé, ça marche sur vos vaults aujourd'hui, et ça tourne sans clé, sur des données publiques. Merci.
-->
