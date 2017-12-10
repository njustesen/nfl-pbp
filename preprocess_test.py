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

        if play.outcome_type in [Outcome_Type.TURNOVER_INTERCEPTION, Outcome_Type.TURNOVER_FUMBLE]:
            return

        if play.play_type in [preproces.Play_Type.KNEEL, preproces.Play_Type.RUN] or \
                play.outcome_type == preproces.Outcome_Type.GROUND_YARDS or play.scramble:
            if play.posteam == game.home.team:
                self.home_team_ground_yards += play.yards
            elif play.posteam == game.away.team:
                self.away_team_ground_yards += play.yards
        elif play.outcome_type == preproces.Outcome_Type.COMPLETION_YARDS or (play.play_type == preproces.Play_Type.PASS and play.outcome_type == Outcome_Type.TOUCHDOWN_OFF):
            if play.posteam == game.home.team:
                self.home_team_pass_yards += play.yards
            elif play.posteam == game.away.team:
                self.away_team_pass_yards += play.yards


games = preproces.get_processed_games(limit=0)


def simulate_game(game):
    stats = Game_Stats()
    for play in game.plays:
        stats.apply_play(game.game, play)
    return stats

for game in games:

    stats = simulate_game(game)
    assert game.game.home_score == stats.home_team_score
    assert game.game.away_score == stats.away_team_score
