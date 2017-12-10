from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from collections import namedtuple
import os
import shutil

def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

base_url = 'https://profootballapi.com'
api_key = 'IAjuDOn1QRaE5hlHgWrNTxkeKqU0YPwf'


def call_api(path, arguments):
    try:
        url = base_url + path + '?api_key=' + api_key + arguments
        post_fields = {}
        request = Request(url, urlencode(post_fields).encode())
        json = urlopen(request).read().decode()
        return json
    except Exception:
        print("Failed: " + url)
        raise Exception()
    return ""


def get_game(game_id):
    return call_api('/game', '&game_id=' + str(game_id))


def get_schedule(year):
    return call_api('/schedule', '&year=' + str(year))


def stringify_keys(string):
    for i in range(100):
        string = string.replace('"'+str(i)+'":', '"drive'+str(i)+'":')
    return string


def remove_stats(string):
    home = string.split(',"stats":')[0] + "}"
    away = '"away":' + string.split('"away":')[1].split(',"stats":')[0] + "}"
    game = '"day":' + string.split('"day":')[1]
    return home + ',' + away + ',' + game


def save_games(year, dir):

    schedule_json = get_schedule(year)
    schedule = json2obj(schedule_json)

    ids = []
    for game in schedule:
        ids.append(game.id)

    for id in ids:

        try:
            game_json = get_game(id)
        except Exception:
            continue

        game_json = stringify_keys(game_json);
        game_json = remove_stats(game_json)
        print(game_json)
        game = json2obj(game_json)
        filename = str(year) + '_' + game.season_type + '_' + str(game.week) + '_' + game.home.team + '_' + game.away.team + '.json'
        with open(dir + filename, 'w') as file:
            file.write(game_json)
            print(filename + " saved.")

for i in [2016, 2017, 2015]:
    save_games(i, '/Users/noju/Documents/nfl_games/')
