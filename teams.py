
cities = {
    "CIN": "Cincinnati",
    "IND": "Indianapolis",
    "GB": "Indianapolis",
    "KC": "Kansas City",
    "NYJ": "New York Jets",
    "ARI": "Arizona",
    "PHI": "Philadelphia",
    "DAL": "Dallas",
    "NE": "New England",
    "BAL": "Baltimore",
    "MIN": "Minnesota",
    "DEN": "Denver",
    "CHI": "Chicago",
    "DET": "Detroit",
    "NO": "New Orleans",
    "SD": "San Diego",
    "BUF": "Buffalo",
    "TEN": "Tennessee",
    "WAS": "Washington",
    "ATL": "Atlanta",
    "CLE": "Cleveland",
    "HOU": "Houston",
    "MIA": "Miami",
    "JAC": "Jacksonville",
    "NYG": "New York Giants",
    "CAR": "Carolina",
    "STL": "Saint Louis",
    "OAK": "Oakland",
    "PIT": "Pittsburgh",
    "SEA": "Seattle",
    "SF": "San Francisco",
    "TB": "Tampa Bay",
    "JAX": "Jacksonville"

}

teams = {
    "CIN": "Cincinnati Bengals",
    "IND": "Indianapolis Colts"
}

synonyms = {
    "CLT": "IND"
}


def real_short(short):
    if short in synonyms.keys():
        return synonyms[short]
    return short


def get_short(name):
    for short in teams.keys():
        if teams[short] == name:
            return short
    raise Exception("Team not found: " + name)
