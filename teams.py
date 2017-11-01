
teams = {
    "CIN": "Cincinnati Bengals",
    "IND": "Indianapolis Colts"
}

def get_short(name):
    for short in teams.keys():
        if teams[short] == name:
            return short
    raise Exception("Team not found: " + name)
