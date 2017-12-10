import preproces
from preproces import Outcome_Type


class Game_Stats:

    def __init__(self):
        self.home_team_pass_yards = 0
        self.home_team_ground_yards = 0
        self.home_team_penalty_yards = 0
        self.home_team_score = 0
        self.away_team_pass_yards = 0
        self.away_team_ground_yards = 0
        self.away_team_penalty_yards = 0
        self.away_team_score = 0

    def home_team_total_yards(self):
        return self.home_team_ground_yards + self.home_team_pass_yards

    def away_team_total_yards(self):
        return self.away_team_ground_yards + self.away_team_pass_yards

    def out(self):
        print("-- HOME --")
        print("SCORE: " + str(self.home_team_score))
        print("YARDS: " + str(self.home_team_pass_yards + self.home_team_ground_yards) + " [P: " + str(self.home_team_pass_yards) + ", R: " + str(self.home_team_ground_yards) + "]")
        print("PENALTY: " + str(self.home_team_penalty_yards))
        print("-- AWAY --")
        print("SCORE: " + str(self.away_team_score))
        print("YARDS: " + str(self.away_team_pass_yards + self.home_team_pass_yards) + " [P: " + str(self.away_team_pass_yards) + ", R: " + str(self.away_team_ground_yards) + "]")
        print("PENALTY: " + str(self.away_team_penalty_yards))

    def apply_play(self, game, play):
        if play.outcome_type in [preproces.Outcome_Type.TOUCHDOWN_OFF]:
            if play.posteam == game.home.team:
                self.home_team_score += 6
            elif play.posteam == game.away.team:
                self.away_team_score += 6
        if play.outcome_type in [preproces.Outcome_Type.TOUCHDOWN_DEF]:
            if play.posteam == game.home.team:
                self.away_team_score += 6
            elif play.posteam == game.away.team:
                self.home_team_score += 6
        elif play.outcome_type in [preproces.Outcome_Type.FIELD_GOAL]:
            if play.posteam == game.home.team:
                self.home_team_score += 3
            elif play.posteam == game.away.team:
                self.away_team_score += 3
        elif play.outcome_type in [preproces.Outcome_Type.EXTRA_POINT_GOOD]:
            if play.posteam == game.home.team:
                self.home_team_score += 1
            elif play.posteam == game.away.team:
                self.away_team_score += 1
        elif play.outcome_type in [preproces.Outcome_Type.CONVERSION_GOOD]:
            if play.posteam == game.home.team:
                self.home_team_score += 2
            elif play.posteam == game.away.team:
                self.away_team_score += 2
        elif play.outcome_type in [preproces.Outcome_Type.SAFETY_OFF]:
            if play.posteam == game.home.team:
                self.home_team_score += 2
            elif play.posteam == game.away.team:
                self.away_team_score += 2
        elif play.outcome_type in [preproces.Outcome_Type.SAFETY]:
            if play.posteam == game.home.team:
                self.away_team_score += 2
            elif play.posteam == game.away.team:
                self.home_team_score += 2

        if play.play_type in [preproces.Play_Type.KNEEL, preproces.Play_Type.RUN] or \
                play.outcome_type in [preproces.Outcome_Type.SACK, preproces.Outcome_Type.GROUND_YARDS]:
            if play.posteam == game.home.team:
                self.home_team_ground_yards += play.yards
            elif play.posteam == game.away.team:
                self.away_team_ground_yards += play.yards
        elif play.outcome_type == preproces.Outcome_Type.COMPLETION_YARDS or (play.play_type == preproces.Play_Type.PASS and play.outcome_type == Outcome_Type.TOUCHDOWN_OFF):
            if play.posteam == game.home.team:
                self.home_team_pass_yards += play.yards
            elif play.posteam == game.away.team:
                self.away_team_pass_yards += play.yards

games = preproces.get_processed_games(limit=3)


def simulate_game(game):
    stats = Game_Stats()
    for play in game.plays:
        stats.apply_play(game.game, play)
    return stats

#def stats_same(game, stats):


for game in games:
    stats = simulate_game(game)
    #if not stats_same(game, stats):
    #stats.out()
    print("## GAME ##")
    print("Home score: " + str(game.game.home_score) + " | " + str(stats.home_team_score))
    print("Home p yds: " + str(game.game.home.pyds) + " | " + str(stats.home_team_pass_yards))
    print("Home r yds: " + str(game.game.home.ryds) + " | " + str(stats.home_team_ground_yards))
    print("Home t yds: " + str(game.game.home.totyds) + " | " + str(stats.home_team_total_yards()))

    print("Away score: " + str(game.game.away_score) + " | " + str(stats.away_team_score))
    print("Away p yds: " + str(game.game.away.pyds) + " | " + str(stats.away_team_pass_yards))
    print("Away r yds: " + str(game.game.away.ryds) + " | " + str(stats.away_team_ground_yards))
    print("Away t yds: " + str(game.game.away.totyds) + " | " + str(stats.away_team_total_yards()))
