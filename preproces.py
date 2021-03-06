from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
from collections import namedtuple
import os
import shutil
import glob
from enum import Enum
import numpy as np
import teams

def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

dir = '/Users/noju/Documents/nfl_games/'


class Play_Type(Enum):
    NONE = 0
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
    PENALTY_DELAY_OF_GAME = 18
    ABORTED = 19
    UNKNOWN = 100


class Run_Type(Enum):
    LEFT_TACKLE = 1
    RIGhT_TACKLE = 2
    LEFT_END = 3
    RIGHT_END = 4
    LEFT_GUARD = 5
    RIGHT_GUARD = 6
    REVERSE = 7


class Pass_Type(Enum):
    FLEA_FLICKER = 1    # flea-flicker


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
    KICK_OUT_OF_BOUNDS = 26
    KICK_FAIR_CATCH = 27
    SPIKE = 28
    NONE = 100


class Challenge_Type(Enum):
    NO_CHALLENGE = 1
    CHALLENGE_OFF_UNSUCCESSFUL = 2
    CHALLENGE_OFF_SUCCESSFUL = 3
    CHALLENGE_DEF_UNSUCCESSFUL = 4
    CHALLENGE_DEF_SUCCESSFUL = 5


class Play:

    def __init__(self, play, next_play, drive_id):
        self.drive_id = drive_id
        self.quarter = play.quarter
        self.down = play.down
        self.time = play.time
        self.yrdln = play.yrdln
        if self.yrdln == '' and next_play is not None:
            self.yrdln = next_play.yrdln
        self.ydstogo = play.ydstogo
        if self.ydstogo == '' and next_play is not None:
            self.ydstogo = next_play.ydstogo
        self.ydsnet = play.ydsnet
        if self.ydsnet == '' and next_play is not None:
            self.ydsnet = next_play.ydsnet
        self.posteam = play.posteam
        if self.posteam == '' and next_play is not None:
            self.posteam = next_play.posteam
        self.opponent = play.opponent
        if self.opponent == '' and next_play is not None:
            self.opponent = next_play.opponent
        self.description = play.description
        self.note = play.note
        self.shotgun = "Shotgun" in self.description
        self.wildcat = "Wildcat" in self.description
        self.penalty = "PENALTY" in self.description
        self.fumble = "FUMBLES" in self.description
        self.interception = "INTERCEPTED" in self.description
        self.no_huddle = "No Huddle" in self.description
        self.togoal = self.to_goal()
        self.scramble = "scrambles" in self.description
        self.qb_switch = "in at Quarterback" in self.description
        self.play_type = self.get_play_type()
        self.outcome_type = self.get_outcome_type(next_play)
        self.yards = self.yards_on_play(next_play)
        self.clock = self.clock_stopped()
        self.challenge_type = self.challenge_on_play()

    def out(self):
        print(self.description)
        print(self.play_type)
        print("Possession: " + str(self.posteam))
        print("Down: " + str(self.down))
        print("Togo: " + str(self.ydstogo))
        print("To goal: " + str(self.togoal))
        print("Shotgun: " + str(self.shotgun))
        print("No huddle: " + str(self.no_huddle))
        print("Wildcat: " + str(self.wildcat))
        print("Scramble: " + str(self.scramble))
        print("->")
        print(self.outcome_type)
        print(self.challenge_type)
        print("Yards: " + str(self.yards))
        print("Clock: " + str(self.clock))
        print("----------------")

    def challenge_on_play(self):
        if self.posteam in ['', None] or self.opponent in ['', None]:
            return Challenge_Type.NO_CHALLENGE
        if teams.cities[self.posteam] + " challenged" in self.description:
            if "Upheld" in self.description:
                return Challenge_Type.CHALLENGE_OFF_UNSUCCESSFUL
            else:
                return Challenge_Type.CHALLENGE_OFF_SUCCESSFUL
        elif teams.cities[self.opponent] + " challenged" in self.description:
            if "Upheld" in self.description:
                return Challenge_Type.CHALLENGE_DEF_UNSUCCESSFUL
            else:
                return Challenge_Type.CHALLENGE_DEF_SUCCESSFUL

        return Challenge_Type.NO_CHALLENGE

    def fix_yards(self, next_play):
        if next_play is not None:
            if self.posteam == next_play.posteam:
                self.yards = self.togoal - next_play.togoal
            else:
                self.yards = next_play.togoal - (100 - self.togoal)

    def is_challenge_successful(self):
        return self.challenge_type in [Challenge_Type.CHALLENGE_DEF_SUCCESSFUL, Challenge_Type.CHALLENGE_OFF_SUCCESSFUL]

    def to_goal_field_yrd(self, field, yrdln):
        if yrdln == "50" or yrdln == "":
            return 50
        yard = int(yrdln)
        if field == self.posteam:
            return 100 - yard
        return yard

    def to_goal(self):
        if self.yrdln == "50" or self.yrdln == "":
            return 50
        return self.to_goal_field_yrd(self.yrdln.split(" ")[0], self.yrdln.split(" ")[1])

    def clock_stopped(self):
        if self.play_type == Play_Type.RUN:
            return self.outcome_type == Outcome_Type.GROUND_YARDS and "pushed ob" not in self.description

        if self.play_type == Play_Type.PASS:
            return self.outcome_type == Outcome_Type.COMPLETION_YARDS and "pushed ob" not in self.description

        return self.outcome_type == Outcome_Type.COMPLETION_YARDS and "ran ob" not in self.description

    def yards_on_play(self, next_play):

        if self.outcome_type in [Outcome_Type.TOUCHDOWN_OFF, Outcome_Type.EXTRA_POINT_GOOD, Outcome_Type.CONVERSION_GOOD, Outcome_Type.FIELD_GOAL, Outcome_Type.SAFETY_OFF]:
            return self.togoal
        if self.outcome_type in [Outcome_Type.TOUCHDOWN_DEF, Outcome_Type.SAFETY]:
            return self.togoal - 100
        if self.outcome_type in [Outcome_Type.EXTRA_POINT_NO_GOOD, Outcome_Type.FIELD_GOAL_NO_GOOD, Outcome_Type.INCOMPLETE, Outcome_Type.TIMEOUT, Outcome_Type.NONE]:
            return 0
        if self.outcome_type == Outcome_Type.TOUCHBACK:
            return self.togoal - 20
        if self.play_type in [Play_Type.TIMEOUT_DEF, Play_Type.TIMEOUT_OTHER, Play_Type.TIMEOUT_OFF]:
            return 0

        # Extract from description
        try:

            field = ""
            real_field = ""
            yard = ""
            next = ""
            for word in self.description.split(" "):
                if next == "field" and word == "the":
                    next = ""
                elif word in ["to", "at"]:
                    next = "field"
                elif next == "field":
                    if word == "50":
                        yard = "50"
                        next = ""
                    elif word == "40-yard":
                        yard = "40"
                        next = ""
                    elif word in [self.posteam, self.opponent]:
                        field = word
                        next = "yard"
                    else:
                        next = ""
                elif next == "yard" and "#" not in word and ")" not in word and "-" not in word and "due" not in word and "bench" not in word:
                    try:
                        if "." in word or "," in word or ";" in word:
                            if "." in word and "," in word:
                                word = word[:-2]
                            else:
                                word = word[:-1]
                        int(word)
                        yard = word
                        real_field = field
                    except Exception as err:
                        pass
                    next = ""
                else:
                    next = ""

            to = self.to_goal_field_yrd(real_field, yard)
            return self.togoal - to
        except Exception as err:
            print(str(err) + ": " + self.description)
        return 0

    def in_description(self, word):
        return word in self.description

    def get_fumble_recovering_team(self):
        return self.description.split("RECOVERED by ")[-1].split("-")[0]

    def get_outcome_type(self, next_play):

        if self.play_type == Play_Type.UNKNOWN:
            return Outcome_Type.NONE

        if self.qb_switch:
            return Outcome_Type.NONE

        description = self.description

        if "challenged" in self.description and "REVERSED" in self.description:
            description = self.description.split("REVERSED.")[1]

        if self.play_type in [Play_Type.TWO_MINUTE_WARNING, Play_Type.END_OF_QUARTER]:
            return Outcome_Type.NONE
        elif self.play_type in [Play_Type.TIMEOUT_DEF, Play_Type.TIMEOUT_OTHER, Play_Type.TIMEOUT_OFF]:
            return Outcome_Type.TIMEOUT
        elif self.play_type == Play_Type.CONVERSION_ATTEMPT:
            if self.note == "2P":  # or "ATTEMPT SUCCEEDS" in self.description
                return Outcome_Type.CONVERSION_GOOD
            else:
                return Outcome_Type.CONVERSION_NO_GOOD
        elif self.play_type == Play_Type.EXTRA_POINT_ATTEMPT:
            if self.note == "XP":
                return Outcome_Type.EXTRA_POINT_GOOD
            else:
                return Outcome_Type.EXTRA_POINT_NO_GOOD
        elif self.play_type == Play_Type.FIELD_GOAL_ATTEMPT:
            if self.note == "FG":
                return Outcome_Type.FIELD_GOAL
            elif self.note == "FGM" or "BLOCKED" in self.description:
                return Outcome_Type.FIELD_GOAL_NO_GOOD
            elif "PENALTY" in description and "No Play" in description:
                return Outcome_Type.PENALTY_NO_PLAY
            else:
                raise Exception("Field goal outcome unknown: " + description)
        elif self.play_type in [Play_Type.KICK_OFF, Play_Type.PUNT, Play_Type.FREE_KICK]:
            if "Touchback" in description:
                return Outcome_Type.TOUCHBACK
            elif "out of bounds" in description and ((next_play is not None and next_play.posteam != self.posteam) or self.note == "PUNT"):
                return Outcome_Type.KICK_OUT_OF_BOUNDS
            elif "fair catch" in self.description:
                return Outcome_Type.KICK_FAIR_CATCH
            elif (next_play is not None and next_play.posteam != self.posteam) or self.note == "PUNT":
                return Outcome_Type.KICK_RETURN
            elif (next_play is not None and next_play.posteam == self.posteam) and (self.note == "ONSIDE" or self.fumble):
                return Outcome_Type.KICK_RECOVERY
            elif self.note == "TD":
                if not self.fumble:
                    return Outcome_Type.TOUCHDOWN_DEF
                else:
                    recover_team = self.get_fumble_recovering_team()
                    if recover_team == self.posteam:
                        return Outcome_Type.TOUCHDOWN_OFF
                    return Outcome_Type.TOUCHDOWN_DEF
            elif next_play is None:
                return Outcome_Type.KICK_RETURN
            elif self.note == "SAFETY":
                raise Exception("Unknown safety on return outcome: " + description)
        elif self.note == "PENALTY":
            if ("Defensive Holding" in description or "Illegal Use of Hands" in description) and (next_play is not None and next_play.posteam == self.posteam):
                return Outcome_Type.PENALTY_FIRST_DOWN
            elif "No Play" in description:
                return Outcome_Type.PENALTY_NO_PLAY
            else:
                return Outcome_Type.PENALTY_PLAY
        elif self.note == "FUMBLE" and next_play is None:
            return Outcome_Type.TURNOVER_FUMBLE
        elif self.note == "INT" and next_play is None:
            return Outcome_Type.TURNOVER_INTERCEPTION
        elif self.play_type == Play_Type.PASS:
            if "pass short" in description or "pass deep" in description:
                if self.note == "TOUCHDOWN" or self.note == "TD":
                    if next_play is not None and self.posteam == next_play.posteam:
                        return Outcome_Type.TOUCHDOWN_OFF
                    elif next_play is not None and self.posteam != next_play.posteam:
                        return Outcome_Type.TOUCHDOWN_DEF
                    elif self.interception and not self.fumble:
                        return Outcome_Type.TOUCHDOWN_DEF
                    elif not self.fumble and not self.interception:
                        return Outcome_Type.TOUCHDOWN_OFF
                    elif self.fumble:
                        recover_team = self.get_fumble_recovering_team()
                        if recover_team == self.posteam:
                            return Outcome_Type.TOUCHDOWN_OFF
                        return Outcome_Type.TOUCHDOWN_DEF
                    else:
                        raise Exception("Unknown scoring team" + description)
                elif "scrambles" in description:
                    return Outcome_Type.GROUND_YARDS
                else:
                    return Outcome_Type.COMPLETION_YARDS
            elif "incomplete" in description:
                return Outcome_Type.INCOMPLETE
            elif "sacked" in description:
                if next_play is None and (self.note == "TOUCHDOWN" or self.note == "TD") and "FUMBLES" in description:
                    recover_team = self.get_fumble_recovering_team()
                    if recover_team == self.posteam:
                        return Outcome_Type.TOUCHDOWN_OFF
                    return Outcome_Type.TOUCHDOWN_DEF
                return Outcome_Type.SACK
        elif self.play_type == Play_Type.RUN or self.play_type == Play_Type.KNEEL:
            if self.note == "TOUCHDOWN" or self.note == "TD":
                if next_play is not None and self.posteam == next_play.posteam:
                    return Outcome_Type.TOUCHDOWN_OFF
                elif next_play is not None and self.posteam != next_play.posteam:
                    return Outcome_Type.TOUCHDOWN_DEF
                elif self.fumble:
                    recover_team = self.get_fumble_recovering_team()
                    if recover_team == self.posteam:
                        return Outcome_Type.TOUCHDOWN_OFF
                    return Outcome_Type.TOUCHDOWN_DEF
                else:
                    raise Exception("Unknown scoring team" + description)
            else:
                return Outcome_Type.GROUND_YARDS
        elif self.play_type == Play_Type.TIMEOUT_OFF:
            return Outcome_Type.TIMEOUT_OFF
        elif self.play_type == Play_Type.TIMEOUT_DEF:
            return Outcome_Type.TIMEOUT_DEF
        elif "Aborted" in description:
            if self.note == "FUMBLE" and next_play != None:
                return Outcome_Type.TURNOVER_FUMBLE
            else:
                return Outcome_Type.GROUND_YARDS
        elif self.play_type == Play_Type.SPIKE and self.note == "":
            return Outcome_Type.SPIKE
        elif self.play_type == Play_Type.PENALTY_DELAY_OF_GAME and "declined" in self.description or "Personal Foul on " in self.description:
            return Outcome_Type.PENALTY_NO_PLAY
        else:
            raise Exception("Unknown outcome: " + description + ", play type: " + str(self.play_type) + ", note: " + self.note)
        # TODO: Safety

    def get_play_type(self):

        if self.qb_switch:
            return Play_Type.NONE

        if "Two Point Attempt" in self.description or "TWO-POINT CONVERSION ATTEMPT" in self.description:
            return Play_Type.CONVERSION_ATTEMPT

        if "Two-Minute Warning" in self.description:
            return Play_Type.TWO_MINUTE_WARNING
        if "END QUARTER" in self.description or "END GAME" in self.description or "End of quarter" in self.description or "End of half" in self.description:
            return Play_Type.END_OF_QUARTER
        if "pass" in self.description or "sacked" in self.description or "scrambles" in self.description or "ran ob" in self.description:
            return Play_Type.PASS
        if "right tackle" in self.description \
                or "up the middle" in self.description \
                or "left tackle" in self.description \
                or "left end" in self.description \
                or "right end" in self.description \
                or "left guard" in self.description \
                or "right guard" in self.description:
            return Play_Type.RUN
        elif self.note == "KICKOFF" or "kicks" in self.description:
            return Play_Type.KICK_OFF
        elif "punt" in self.description:
            return Play_Type.PUNT
        elif self.note == "TIMEOUT":
            if self.posteam == None:
                return Play_Type.TIMEOUT_OTHER
            elif self.posteam in self.description:
                return Play_Type.TIMEOUT_OFF
            elif self.posteam in self.description:
                return Play_Type.TIMEOUT_OFF
            else:
                return Play_Type.TIMEOUT_OTHER
        elif self.note == "Timeout":
             return Play_Type.TIMEOUT_OTHER
        elif "field goal" in self.description:
            return Play_Type.FIELD_GOAL_ATTEMPT
        elif "extra point" in self.description:
            return Play_Type.EXTRA_POINT_ATTEMPT
        elif ("PENALTY" in self.note or "Penalty" in self.description) and "declined" not in self.description:
            if "Pass Interference" in self.description:
                return Play_Type.PASS
            elif "Intentional Grounding" in self.description:
                return Play_Type.PASS
            elif "Delay of Game" in self.description:
                return Play_Type.PENALTY_DELAY_OF_GAME
            elif "No Play" in self.description:
                return Play_Type.PENALTY_NO_PLAY
            else:
                raise Exception("Unknown penalty: " + self.description)
        elif "kneels" in self.description:
            return Play_Type.KNEEL
        elif "spike" in self.description:
            return Play_Type.SPIKE
        elif "Aborted" in self.description:
            return Play_Type.ABORTED
        elif (" to " + self.posteam in self.description or " to " + self.opponent in self.description) and self.description.split(" ")[2] == "to":
            return Play_Type.RUN 
        elif (self.in_description(" to " + self.posteam) or self.in_description(" to " + self.opponent)):
            return Play_Type.RUN
        elif "(Run formation)" in self.description:
            return Play_Type.RUN
        elif "(Punt formation)" in self.description:
            return Play_Type.PUNT
        elif "Personal Foul on " in self.description:
            return Play_Type.PENALTY_NO_PLAY
        elif "Intentional Grounding" in self.description:
            return Play_Type.PASS
        elif "BLANK PLAY" in self.description:
            return Play_Type.UNKNOWN
        else:
            raise Exception("Unknown play type: " + self.description)


class Game:

    def __init__(self, game, plays):
        self.game = game
        self.plays = plays


def sorted_drives(game):
    drives = game.home.drives + game.away.drives
    out = []
    id = 1
    x = 0
    while x != id:
        x = id
        for drive in drives:
            if drive.drive_id == id:
                out.append(drive)
                id += 1
    return out


def get_plays(game):
    plays = []
    try:
        drives = sorted_drives(game)
    except Exception as err:
        print(err)
        return []
    for drive in drives:
        i = 0
        for play in drive.plays:
            next_play = None
            if len(drive.plays) > i+1:
                next_play = drive.plays[i+1]
            if "End of game" not in play.description and len(play.description.split(" ")) > 1:
                try:
                    p = Play(play, next_play, drive.drive_id)
                    plays.append(p)
                except Exception as err:
                    print("ERROR: " + str(err) + " [" + play.description + "]")
                    raise err
            i += 1
    return plays


def fix_yards(plays):

    i = 0
    for play in plays:
        next_play = None
        if len(plays) > i+1:
            next_play = plays[i+1]
        if play.penalty or play.is_challenge_successful():
            play.fix_yards(next_play)
        i += 1


def get_processed_games(limit=0):
    games = []
    i = 0
    for filename in glob.glob(dir + '*'):

        with open(filename, 'r') as myfile:
            data = myfile.read()
            game = json2obj(data)
            plays = get_plays(game)
            fix_yards(plays)
            if len(plays) > 0:
                games.append(Game(game, plays))
            i += 1

        if len(games) == limit:
            return games

    return games

get_processed_games(limit=1)