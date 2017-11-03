
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
