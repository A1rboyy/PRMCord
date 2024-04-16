
patchnotes = (
    
    "**Version 1.3**\n"
    "- Mit !shop (anzahl pulls) kann man nun für je 2 prm-coins einen neuen Pull kaufen.\n"
    "- Beim Pullen kann man nun entscheiden gegen welche Position man den gezogenen Spieler austauscht.\n"

        "**Version 1.2**\n"
    "- Jedes Team kann nun bis zu 2 Bankspieler auf einmal haben. Du kannst deinen Bankspieler austauschen mit !swap b1/b2.\n"
    "- Du kannst deine Bankspieler jederzeit entlassen mit !release/!entlassen b1/b2.\n"
    "- Der Transfermarkt ist offen und verfügbar mit !transfermarkt oder !tm.\n"
    "- Wenn du einen Platz auf der Bank frei hast kannst du einen Spieler kaufen mit !buy/!kaufen und der Id des Spieler auf dem Markt.\n"
    "- Pro Tag kannst du 3 Spieler/Coaches von dir auf dem Transfermarkt anbieten mit !sell/!verkaufen b1/b2 und dem Preis in prm-coins.\n"
    "- Alle 25 Spiele erhälst du jetzt nicht einen zusätzlichen Pull, sonder ein prm-coin.\n"
    "- Wenn du willst ob jemand anderes einen Spieler hat den du willst kannst du das mit !search (spielername) tun.\n"
    
    "**Version 1.1**\n"
    "- Der Assistant Coach verstärkt nun eine Position deiner Wahl. Einstellbar mit !Assistant (position)\n"
    "- Abhängig von der Liga des Assistant verstärkt er die ausgewählte Position um bis zu 40%!\n"
    
    "**Version 1.0**\n"
    "- Viele neue Coaches wurden hinzugefügt\n"
    "- Du kannst nun nicht mehr deinem eigenen Turnier beitreten.\n"
    "- Der maximale Eintrittspreis von einem Turnier ist nun die Hälfte deiner Elo.\n"
    "- Die Turnierfunktion wurde von Bugs bereinigt.\n"
    "- Die maximale Elo die aus einem Match verloren werden kann beträgt 30.\n"
              
            )


explain_spieler = (
    "Jeder Spieler hat eine Stärke je nach Div(Liga) in der er spielt.\n"
    "Gleichstarke Spieler haben eine 50% Wahrscheinlichkeit gegeneinander zu gewinnen.\n"
    "Ein Spieler einer höheren Liga ist doppelt so stark wie der Spieler der Liga dadrunter.\n"
    "Die Chance für diesen Spieler zu gewinnen liegen bei 66,66%.\n"
    "Gegen einen Spieler aus 2 liegen darunter zu gewinne liegt die Chance bei 80%. Für 3 Ligen ca.90%."
)

einfluss_coaches = (
    "Der Headcoach beeinflusst die Stärke von jedem Spieler.\n"
    "Er multipliziert die Stärke von jedem Spieler abhängig von der Division(Liga) des Coaches.\n"
    "Liga 1: 100%, Liga 2: 75%, Liga 3: 50%, Liga 4: 25%.\n"
    "Das bedeutet, bei zwei Spieler der selben Division gegeneinander, der eine mit einem Liga 1 Headcoach, der andere mit einem Liga 2 Headcoach \n"
    "hat der erste Spieler eine Gewinnchance von 53,33%, bei Headcoach von Liga 1 und 3 ist die Chance 57,14%.\n"
    "Der Assistant Coach kann einer Position zugewiesen werden und verbessert einen **einzelnen** Spieler um bis zu 40%(Liga 1: 40%, Liga 2: 30%...)\n"
    "Wenn beide Spieler die gleiche Situation haben bis auf den Assistant Coach heißt das (mit Liga 1 AC) eine Gewinnchance von 58,33%."
)

chances_pulls = (
    "Beim Ziehen von Spielern hat jeder Spieler die gleiche Wahrscheinlichkeit gezogen zu werden, unabhängig von der Division.\n"
    "Bei ca.2000 Spielern ist die Chance einen bestimmten Spieler oder Coach zu ziehen also immer 1/2000.\n"
    "Auch bei den Teams ist es ähnlich. Bei ca.400 Teams ist die Chance einen Spieler/Coach aus einem bestimmten Team ziehen ca. 1/400 auch wenn nicht jedes Team einen Coach hat \n"
    "und dadurch die Chancen leicht verändert sind."
)

synergies = (
    "Es gibt 3 unterschiedliche Synergien, welche die Spieler in deinem Team verstärken können.\n"
    "1. Wenn Mid/Jgl das gleiche PRM Team haben bekommt jeder von ihnen 25% Stärke dazu.\n"
    "2. Gleiches gilt für ADC/Sup aus dem gleichen PRM Team, 25% Stärke.\n"
    "3. Wenn alle Spieler aus dem Team (nicht Coaches) das gleiche PRM Team haben, erhalten sie 50% Stärke zusätzlich. Andere Buffs entfallen.\n"
    "25% Stärke gibt bei gleichen anderen Verhältnissen 55,55% Siegchance. 50% Bringt 60% Siegchance."
)