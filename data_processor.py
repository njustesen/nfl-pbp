from enum import Enum
import pfr_scraper as scraper


class State_Type(Enum):
    NORMAL = 1
    FREE_KICK = 2
    KICK_OFF_30 = 3
    KICK_OFF_35 = 4
    EXTRA_POINT_2_YARDS = 5
    EXTRA_POINT_KICK_15_YARDS = 6
    EXTRA_POINT_CONVERSION_ATTEMPT_2_YARDS = 7


class State:

    def __init__(self, possession="", location=30, field="", down=1, togo=10, type=None, time=15*60, quarter=1, time_out_home=3, time_out_away=3, clock_ticking=False, score_home=0, score_away=0):
        self.possession = possession
        self.location = location
        self.down = down
        self.togo = togo
        self.type = type
        self.time = time
        self.quarter = quarter
        self.time_out_home = time_out_home
        self.time_out_away = time_out_away
        self.clock_ticking = clock_ticking
        self.score_home = score_home
        self.score_away = score_away
        self.field = field

    def to_goal(self):
        if self.possession == "":
            return -1

        if self.possession == self.field:
            return (50 - self.location) + 50

        return self.location


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
    TURNOVER_INTERCEPTION_FUMBLE = 13
    #TURNOVER_DOWNS = 10
    TIMEOUT_OFF = 14
    TIMEOUT_DEF = 15
    PENALTY_PLAY = 16
    PENALTY_NO_PLAY = 17
    PENALTY_FIRST_DOWN = 20
    EXTRA_POINT_GOOD = 21
    EXTRA_POINT_NO_GOOD = 22
    CONVERSION_GOOD = 23
    CONVERSION_NO_GOOD = 24
    KICK_RECOVERY = 25
    KICK_RETURN = 26


class Outcome:

    def __init__(self, outcome_type=Outcome_Type.GROUND_YARDS, yards=0, tackle=False):
        self.outcome_type = outcome_type
        self.yards = yards
        self.tackle = tackle


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
    EXTRA_POINT_ATTEMPT = 12
    CONVERSION_ATTEMPT = 13
    PENALTY_NO_PLAY = 14
    UNKNOWN = 100


class Play:

    def __init__(self, state, play_type, outcome):
        self.state = state
        self.play_type = play_type
        self.outcome = outcome

    def clock_running(self):
        if self.play_type in [Play_Type.KNEEL, Play_Type.PASS, Play_Type.RUN] and self.outcome.tackle:
            return True
        return False


def extract_state(pfr_play, prev_play, prev_pfr_play, game):

    # Is first kickoff?
    if prev_play == None:
        return State(possession= pfr_play.field,
            location=pfr_play.location,
            field=pfr_play.field,
            down=0,
            togo=0,
            type=State_Type.KICK_OFF_30 if pfr_play.location == 30 else State_Type.KICK_OFF_35,
            time=pfr_play.time,
            quarter=pfr_play.quarter,
            time_out_home=3,
            time_out_away=3,
            clock_ticking=False,
            score_home=0,
            score_away=0
        )
    else:
        clock = True
        possession = prev_play.state.possession
        state_type = State_Type.NORMAL
        timeout_home = prev_play.state.time_out_home
        timeout_away = prev_play.state.time_out_away
        location = pfr_play.location
        field = pfr_play.field

        # Half
        if prev_play.state.quarter == 2 and pfr_play.quarter == 3:
            possession = game.other_team(game.plays[0].field).short
            state_type = State_Type.KICK_OFF_30 if pfr_play.location == 30 else State_Type.KICK_OFF_35
            clock = False

        # Kick-off due to field goal, extra point or conversion attempt
        elif prev_play.outcome.outcome_type in [Outcome_Type.EXTRA_POINT_GOOD,
                                   Outcome_Type.EXTRA_POINT_NO_GOOD,
                                   Outcome_Type.FIELD_GOAL,
                                   Outcome_Type.CONVERSION_GOOD,
                                   Outcome_Type.CONVERSION_NO_GOOD]:
            state_type = State_Type.KICK_OFF_30 if pfr_play.location == 30 else State_Type.KICK_OFF_35
            clock = False

        # Turnover from kick, interception or fumble
        elif prev_play.outcome.outcome_type in [Outcome_Type.KICK_RETURN,
                                 Outcome_Type.TURNOVER_INTERCEPTION_FUMBLE]:
            possession = game.other_team(possession).short
            state_type = State_Type.NORMAL
            clock = False

        # Turnover on downs or other
        elif prev_play.state.down == 4 and pfr_play.special == "turnover":

            possession = game.other_team(possession).short
            state_type = State_Type.NORMAL
            clock = False

        # Timeout
        elif prev_play.play_type == Play_Type.TIMEOUT_OFF:
            clock = False
            if prev_play.state.possession == game.home_team.short:
                timeout_home -= 1
            elif prev_play.state.possession == game.away_team.short:
                timeout_away -= 1

        # Touchdown offense
        elif prev_play.outcome.outcome_type == Outcome_Type.TOUCHDOWN_OFF:
            clock = False
            if pfr_play.field == "":
                location = 2
                field = game.other_team(possession).short
                state_type = State_Type.EXTRA_POINT_2_YARDS
            elif pfr_play.location == 2:
                state_type = State_Type.EXTRA_POINT_CONVERSION_ATTEMPT_2_YARDS
            elif pfr_play.location == 15:
                state_type = State_Type.EXTRA_POINT_KICK_15_YARDS

        # Touchdown defense
        elif prev_play.outcome.outcome_type == Outcome_Type.TOUCHDOWN_DEF:
            clock = False
            possession = game.other_team(possession).short
            if pfr_play.field == "":
                location = 2
                field = game.other_team(possession).short
                state_type = State_Type.EXTRA_POINT_2_YARDS
            elif pfr_play.location == 2:
                state_type = State_Type.EXTRA_POINT_CONVERSION_ATTEMPT_2_YARDS
            elif pfr_play.location == 15:
                state_type = State_Type.EXTRA_POINT_KICK_15_YARDS

        # Safety defensive
        elif prev_play.outcome.outcome_type == Outcome_Type.SAFETY:
            clock = False
            state_type = State_Type.FREE_KICK

        # Safety offensive
        elif prev_play.outcome.outcome_type == Outcome_Type.SAFETY_OFF:
            clock = False
            possession = game.other_team(possession).short
            state_type = State_Type.FREE_KICK

        # Spike
        elif prev_play.outcome.outcome_type == Outcome_Type.GROUND_YARDS and prev_play.play_type == Play_Type.SPIKE:
            clock = False

        # Update rest of state
        return State(
            possession=possession,
            location=location,
            field=field,
            down=pfr_play.down,
            togo=pfr_play.togo,
            type=state_type,
            time=pfr_play.time,
            quarter=pfr_play.quarter,
            time_out_home=timeout_home,
            time_out_away=timeout_away,
            clock_ticking=clock,
            score_home=prev_pfr_play.score_home,
            score_away=prev_pfr_play.score_away
        )


def extract_play_type(pfr_play, state, game):

    if "pass" in pfr_play.description or "sacked" in pfr_play.description:
        return Play_Type.PASS

    if "right for" in pfr_play.description or "middle for" in pfr_play.description or "left for" in pfr_play.description:
        return Play_Type.RUN

    if "kicks off" in pfr_play.description:
        return Play_Type.KICK_OFF

    if "punt" in pfr_play.description:
        return Play_Type.PUNT

    if "Timeout" in pfr_play.description:
        if game.home_team.name in pfr_play.description:
            if state.possession == game.home_team.short:
                return Play_Type.TIMEOUT_OFF
        if state.possession == game.away_team.short:
            return Play_Type.TIMEOUT_OFF
        return Play_Type.TIMEOUT_DEF

    if "field goal" in pfr_play.description:
        return Play_Type.FIELD_GOAL_ATTEMPT

    if "Two Point Attempt" in pfr_play.description:
        return Play_Type.CONVERSION_ATTEMPT

    if "extra point" in pfr_play.description:
        return Play_Type.EXTRA_POINT_ATTEMPT

    if "Penalty" in pfr_play.description:
        if "Pass Interference" in pfr_play.description:
            return Play_Type.PASS
        if "Intentional Grounding" in pfr_play.description:
            return Play_Type.PASS
        if "(no play)" in pfr_play.description:
            return Play_Type.PENALTY_NO_PLAY
        raise Exception("Unknown penalty: " + pfr_play.description)

    if "kneels" in pfr_play.description:
        return Play_Type.KNEEL

    if "spike" in pfr_play.description:
        return Play_Type.SPIKE

    raise Exception("Unkown play type")


def yards_from_text(pfr_play):
    yards = 0
    if "yards" in pfr_play.description:
        x = 1
        for s in pfr_play.description.split(" yards")[:-2]:
            yards += int(s.split(" ")[-1]) * x
            x = 1 if x == -1 else -1
    return yards


def off_scored(state, pfr_play, game):
    if state.score_home < pfr_play.score_home:
        return state.possession == game.home_team.short
    if state.score_away < pfr_play.score_away:
        return state.possession == game.away_team.short
    return False


def def_scored(state, pfr_play, game):
    if state.score_home < pfr_play.score_home:
        return state.possession != game.home_team.short
    if state.score_away < pfr_play.score_away:
        return state.possession != game.away_team.short
    return False


def extract_outcome(pfr_play, next_pfr_play, play_type, state, game):

    yards = 0
    if next_pfr_play is not None:
        relative_before = pfr_play.location if state.possession == state.field else (50-pfr_play.location) + 50
        relative_after = 0
        if pfr_play.special == "score":
            relative_after = 100
        else:
            relative_after = next_pfr_play.location if state.possession == next_pfr_play.field else (50-next_pfr_play.location) + 50
        yards = relative_after - relative_before
    else:
        yards = yards_from_text(pfr_play)

    if play_type == Play_Type.PENALTY_NO_PLAY:
        return Outcome(Outcome_Type.PENALTY_NO_PLAY, yards)

    if play_type == Play_Type.CONVERSION_ATTEMPT:
        if pfr_play.special == "score":
            return Outcome(Outcome_Type.CONVERSION_GOOD, state.to_goal())
        else:
            return Outcome(Outcome_Type.CONVERSION_NO_GOOD, 0) # YARDS?

    if play_type == Play_Type.EXTRA_POINT_ATTEMPT:
        if pfr_play.special == "score":
            return Outcome(Outcome_Type.EXTRA_POINT_GOOD, state.to_goal())
        else:
            return Outcome(Outcome_Type.EXTRA_POINT_NO_GOOD, 0) # YARDS?

    if play_type == Play_Type.FIELD_GOAL_ATTEMPT:
        if pfr_play.special == "score":
            return Outcome(Outcome_Type.FIELD_GOAL, state.to_goal())
        else:
            return Outcome(Outcome_Type.FIELD_GOAL_NO_GOOD, state.to_goal()) # YARDS?

    tackle = ("tackle" in pfr_play.description)

    if play_type in [Play_Type.KICK_OFF, Play_Type.PUNT, Play_Type.FREE_KICK]:
        if next_pfr_play is not None and next_pfr_play.special == "turnover":
            return Outcome(Outcome_Type.KICK_RETURN, yards=yards, tackle=tackle)
        elif pfr_play is not None and pfr_play.special == "touchback":
            return Outcome(Outcome_Type.TOUCHBACK, yards=yards, tackle=tackle)
        elif pfr_play.special == "score":
            if def_scored(state, pfr_play, game):
                return Outcome(Outcome_Type.TOUCHDOWN_DEF, yards=yards)
            elif off_scored(state, pfr_play, game):
                return Outcome(Outcome_Type.TOUCHDOWN_OFF, yards=yards)
            raise Exception("Unknown outcome: " + pfr_play.description)
        elif next_pfr_play is None:
            return Outcome(Outcome_Type.KICK_RETURN, yards=yards_from_text(pfr_play), tackle=tackle)
        # TODO: Safety

    if next_pfr_play is not None and next_pfr_play.special == "turnover":
        if "fumble" in pfr_play.description or "interception" in pfr_play.description:
            return Outcome(Outcome_Type.TURNOVER_INTERCEPTION_FUMBLE, yards)

    if play_type == Play_Type.PASS:
        if "complete" in pfr_play.description:
            if "touchdown" in pfr_play.description:
                if off_scored(state, pfr_play, game):
                    return Outcome(Outcome_Type.TOUCHDOWN_OFF, yards=state.to_goal())
                elif def_scored(state, pfr_play, game):
                    return Outcome(Outcome_Type.TOUCHDOWN_DEF, yards=state.to_goal())
                raise Exception("Unknown scoring team" + pfr_play.description)
            elif ("interception" in pfr_play.description or "fumble" in pfr_play.description) and next_pfr_play == "turnover":
                return Outcome(Outcome_Type.TURNOVER_INTERCEPTION_FUMBLE, yards=yards)
            return Outcome(Outcome_Type.COMPLETION_YARDS, yards=yards, tackle=tackle)
        elif "incomplete" in pfr_play.description:
            return Outcome(Outcome_Type.INCOMPLETE, yards=0)
        elif "sacked" in pfr_play.description:
            return Outcome(Outcome_Type.GROUND_YARDS, yards=yards)
    elif play_type == Play_Type.RUN:
        if "touchdown" in pfr_play.description:
            if state.score_home < pfr_play.score_home:
                if state.possession == game.home_team.short:
                    return Outcome(Outcome_Type.TOUCHDOWN_OFF, yards=state.to_goal())
                else:
                    return Outcome(Outcome_Type.TOUCHDOWN_DEF, yards=state.to_goal())
            elif state.score_away < pfr_play.score_away:
                if state.possession == game.away_team.short:
                    return Outcome(Outcome_Type.TOUCHDOWN_OFF, yards=state.to_goal())
                else:
                    return Outcome(Outcome_Type.TOUCHDOWN_DEF, yards=state.to_goal())
        elif ("interception" in pfr_play.description or "fumble" in pfr_play.description) and next_pfr_play.special == "turnover":
            return Outcome(Outcome_Type.TURNOVER_INTERCEPTION_FUMBLE, yards=yards, tackle=tackle)
        return Outcome(Outcome_Type.GROUND_YARDS, yards=yards, tackle=tackle)

    if play_type == Play_Type.TIMEOUT_OFF:
        return Outcome(Outcome_Type.TIMEOUT_OFF)
    if play_type == Play_Type.TIMEOUT_DEF:
        return Outcome(Outcome_Type.TIMEOUT_DEF)

    if "Penalty" in pfr_play.description:
        if "(no play)" in pfr_play.description:
            return Outcome(Outcome_Type.PENALTY_NO_PLAY, yards=yards)
        elif "irst down" in pfr_play.description:
            return Outcome(Outcome_Type.PENALTY_FIRST_DOWN, yards=yards)
        return Outcome(Outcome_Type.PENALTY_PLAY, yards=yards)

    # TODO: Safety

    raise Exception("Unknown outcome: " + pfr_play.description)


def process(game):

    plays = []

    prev_play = None
    prev_pfr_play = None
    prev_state = None
    idx = 0
    for pfr_play in game.plays:
        state = extract_state(pfr_play, prev_play, prev_pfr_play, game)
        next_pfr_play = None
        if len(game.plays) > idx+1 and game.plays[idx+1].quarter == pfr_play.quarter:
            next_pfr_play = game.plays[idx+1]
        play_type = extract_play_type(pfr_play, state, game)
        outcome = extract_outcome(pfr_play, next_pfr_play, play_type, state, game)
        play = Play(state, play_type, outcome)
        idx += 1
        plays.append(play)
        prev_play = play
        prev_state = state
        prev_pfr_play = pfr_play

    # Clone last state and add it

    game.processed_plays = plays

for game in scraper.get_games(1995, 1, max=1):
    process(game)
    print("Yay")
