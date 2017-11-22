from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from collections import namedtuple
import os
import shutil
import glob
from enum import Enum

def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

dir = '/Users/noju/Documents/nfl_games/'


class Play_Type(Enum):
    RUN = 1
    PASS = 2
    PUNT = 3
    FIELD_GOAL_ATTEMPT = 4
    KNEEL = 5
    FREE_KICK = 6
    KICK_OFF = 7
    ONSIDE_KICK = 8
    SPIKE = 9
    TIMEOUT_OFF = 10
    TIMEOUT_DEF = 11
    TIMEOUT_OTHER = 12
    EXTRA_POINT_ATTEMPT = 13
    CONVERSION_ATTEMPT = 14
    PENALTY_NO_PLAY = 15
    END_OF_QUARTER = 16
    TWO_MINUTE_WARNING = 17
    PENALTY_DELAY_OF_GAME = 17
    UNKNOWN = 100


class Outcome_Type(Enum):
    GROUND_YARDS = 1
    COMPLETION_YARDS = 2
    SACK = 3
    INCOMPLETE = 4
    TOUCHDOWN_OFF = 5
    TOUCHDOWN_DEF = 6
    FIELD_GOAL = 8
    FIELD_GOAL_NO_GOOD = 9
    TOUCHBACK = 10
    SAFETY = 11
    SAFETY_OFF = 12
    TURNOVER_FUMBLE = 13
    TURNOVER_INTERCEPTION = 14
    #TURNOVER_DOWNS = 10
    TIMEOUT = 15
    PENALTY_PLAY = 17
    PENALTY_NO_PLAY = 18
    PENALTY_FIRST_DOWN = 19
    EXTRA_POINT_GOOD = 20
    EXTRA_POINT_NO_GOOD = 21
    CONVERSION_GOOD = 22
    CONVERSION_NO_GOOD = 23
    KICK_RECOVERY = 24
    KICK_RETURN = 25
    NONE = 100


class Play:

    def __init__(self, play, next_play, drive_id):
        self.drive_id = drive_id
        self.quarter = play.quarter
        self.down = play.down
        self.time = play.time
        self.yrdln = play.yrdln
        self.ydstogo = play.ydstogo
        self.ydsnet = play.ydsnet
        self.posteam = play.posteam
        self.opponent = play.opponent
        self.description = play.description
        self.no_huddle = False
        self.shotgun = False
        self.note = play.note
        self.extract_play_type()
        self.extract_outcome_type(next_play)
        self.extract_yards_on_play(next_play)

    def extract_yards_on_play(self, next_play):
        return 1

    def extract_outcome_type(self, next_play):

        tackle = ("yards (" in self.description)

        if self.play_type == Play_Type.PENALTY_DELAY_OF_GAME:
            self.outcome_type = Outcome_Type.PENALTY_PLAY
        elif self.play_type in [Play_Type.TWO_MINUTE_WARNING, Play_Type.END_OF_QUARTER]:
            self.outcome_type = Outcome_Type.NONE
        elif self.play_type in [Play_Type.TIMEOUT_DEF, Play_Type.TIMEOUT_OTHER, Play_Type.TIMEOUT_OFF]:
            self.outcome_type = Outcome_Type.TIMEOUT
        elif self.play_type == Play_Type.CONVERSION_ATTEMPT:
            if self.note == "2P":
                self.outcome_type = Outcome_Type.CONVERSION_GOOD
            else:
                self.outcome_type = Outcome_Type.CONVERSION_NO_GOOD
        elif self.play_type == Play_Type.EXTRA_POINT_ATTEMPT:
            if self.note == "XP":
                self.outcome_type = Outcome_Type.EXTRA_POINT_GOOD
            else:
                self.outcome_type = Outcome_Type.EXTRA_POINT_NO_GOOD
        elif self.play_type == Play_Type.FIELD_GOAL_ATTEMPT:
            if self.note == "FG":
                self.outcome_type = Outcome_Type.FIELD_GOAL
            elif self.note == "FGM":
                self.outcome_type = Outcome_Type.FIELD_GOAL_NO_GOOD
            else:
                raise Exception("Field goal outcome unknown: " + self.description)
        elif self.play_type in [Play_Type.KICK_OFF, Play_Type.PUNT, Play_Type.FREE_KICK]:
            if (next_play != None and next_play.posteam != self.posteam) or self.note == "PUNT":
                self.outcome_type = Outcome_Type.KICK_RETURN
            elif (next_play != None and next_play.posteam == self.posteam) and (self.note == "ONSIDE" or self.note == "FUMBLE"):
                self.outcome_type = Outcome_Type.KICK_RECOVERY
            elif "Touchback" in self.description:
                self.outcome_type = Outcome_Type.TOUCHBACK
            elif self.note == "TD":
                raise Exception("Unknown touchdown return outcome: " + self.description)
            elif next_play is None:
                self.outcome_type = Outcome_Type.KICK_RETURN
            elif self.note == "SAFETY":
                raise Exception("Unknown safety on return outcome: " + self.description)
        elif self.note == "FUMBLE" and next_play is None:
            self.outcome_type = Outcome_Type.TURNOVER_FUMBLE
        elif self.note == "INT" and next_play is None:
            self.outcome_type = Outcome_Type.TURNOVER_INTERCEPTION
        elif self.play_type == Play_Type.PASS:
            if "pass short" in self.description or "pass deep" in self.description:
                if self.note == "TOUCHDOWN":
                    if next_play is not None and self.posteam == next_play.posteam:
                        self.outcome_type = Outcome_Type.TOUCHDOWN_OFF
                    elif next_play is not None and self.posteam != next_play.posteam:
                        self.outcome_type = Outcome_Type.TOUCHDOWN_DEF
                    raise Exception("Unknown scoring team" + self.description)
                elif "scrambles" in self.description:
                    self.outcome_type = Outcome_Type.GROUND_YARDS
                else:
                    self.outcome_type = Outcome_Type.COMPLETION_YARDS
            elif "incomplete" in self.description:
                self.outcome_type = Outcome_Type.INCOMPLETE
            elif "sacked" in self.description:
                self.outcome_type = Outcome_Type.SACK
        elif self.play_type == Play_Type.RUN or self.play_type == Play_Type.KNEEL:
            if self.note == "TOUCHDOWN":
                if next_play is not None and self.posteam == next_play.posteam:
                    self.outcome_type = Outcome_Type.TOUCHDOWN_OFF
                elif next_play is not None and self.posteam != next_play.posteam:
                    self.outcome_type = Outcome_Type.TOUCHDOWN_DEF
                raise Exception("Unknown scoring team" + self.description)
            else:
                self.outcome_type = Outcome_Type.GROUND_YARDS
        elif self.play_type == Play_Type.TIMEOUT_OFF:
            self.outcome_type = Outcome_Type.TIMEOUT_OFF
        elif self.play_type == Play_Type.TIMEOUT_DEF:
            self.outcome_type = Outcome_Type.TIMEOUT_DEF
        elif self.note == "PENALTY":
            if ("Defensive Holding" in self.description or "Illegal Use of Hands") and (next_play is not None and next_play.posteam == self.posteam):
                self.outcome_type = Outcome_Type.PENALTY_FIRST_DOWN
            elif "No Play" in self.description:
                self.outcome_type = Outcome_Type.PENALTY_NO_PLAY
            else:
                self.outcome_type = Outcome_Type.PENALTY_PLAY
        else:
            raise Exception("Unknown outcome: " + self.description + ", play type: " + str(self.play_type))
        # TODO: Safety

    def extract_play_type(self):

        self.no_huddle = ("no huddle" in self.description)
        self.shotgun = ("Shotgun" in self.description)

        if "Two-Minute Warning" in self.description:
            self.play_type = Play_Type.TWO_MINUTE_WARNING
        elif "END QUARTER" in self.description or "END GAME" in self.description:
            self.play_type = Play_Type.END_OF_QUARTER
        elif "pass" in self.description or "sacked" in self.description or "scrambles" in self.description:
            self.play_type = Play_Type.PASS
        elif "right tackle" in self.description \
                or "up the middle" in self.description \
                or "left tackle" in self.description \
                or "left end" in self.description \
                or "right end" in self.description \
                or "left guard" in self.description \
                or "right guard" in self.description:
            self.play_type = Play_Type.RUN
        elif self.note == "KICKOFF" or "kicks" in self.description:
            self.play_type = Play_Type.KICK_OFF
        elif "punt" in self.description:
            self.play_type = Play_Type.PUNT
        elif self.note == "TIMEOUT":
            if self.posteam in self.description:
                self.play_type = Play_Type.TIMEOUT_OFF
            elif self.posteam in self.description:
                self.play_type = Play_Type.TIMEOUT_OFF
            else:
                self.play_type = Play_Type.TIMEOUT_OTHER
        elif self.note == "Timeout":
             self.play_type = Play_Type.TIMEOUT_OTHER
        elif "field goal" in self.description:
            self.play_type = Play_Type.FIELD_GOAL_ATTEMPT
        elif "Two Point Attempt" in self.description:
            self.play_type = Play_Type.CONVERSION_ATTEMPT
        elif "extra point" in self.description:
            self.play_type = Play_Type.EXTRA_POINT_ATTEMPT
        elif "PENALTY" in self.note or "Penalty" in self.description:
            if "Pass Interference" in self.description:
                self.play_type = Play_Type.PASS
            elif "Intentional Grounding" in self.description:
                self.play_type = Play_Type.PASS
            elif "Delay of Game" in self.description:
                self.play_type = Play_Type.PENALTY_DELAY_OF_GAME
            elif "No Play" in self.description:
                self.play_type = Play_Type.PENALTY_NO_PLAY
            else:
                raise Exception("Unknown penalty: " + self.description)
        elif "kneels" in self.description:
            self.play_type = Play_Type.KNEEL
        elif "spike" in self.description:
            self.play_type = Play_Type.SPIKE
        else:
            raise Exception("Unknown play type: " + self.description)

plays = []
def process(game):
    for drive in game.home.drives:
        i = 0
        for play in drive.plays:
            next_play = None
            if len(drive.plays) > i+1:
                next_play = drive.plays[i+1]
            p = Play(play, next_play, drive.drive_id)
            plays.append(p)



for filename in glob.glob(dir + '*'):

    with open(filename, 'r') as myfile:
        data = myfile.read()
        game = json2obj(data)
        process(game)