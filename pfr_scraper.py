import urllib
import datetime
import teams
import moment

website = "https://www.pro-football-reference.com"
url_week = website + "/years/{year}/week_{week}.htm"


class Weather:
    def __init__(self, temperature=60, humidity=30, rainfall=0, snowfall=0, wind=4):
        self.temperature = temperature
        self.humidity = humidity
        self.rainfall = rainfall
        self.snowfall = snowfall
        self.wind = wind

    def out(self):
        print("TEMP: " + str(self.temperature))
        print("HUMI: " + str(self.humidity))
        print("RAIN: " + str(self.rainfall))
        print("SNOW: " + str(self.snowfall))
        print("WIND: " + str(self.wind))


class PFR_Team:
    def __init__(self, name, short, record):
        self.name = name
        self.short = short
        self.record = record

    def out(self):
        print(self.name + " (" + self.short + ") [" + str(self.record[0]) + "," + str(self.record[1]) + "]")


class PFR_Game:
    def __init__(self, date, season, week, stadium, roof, surface, vegas_line, over_under, weather, home_team, away_team, home_score, away_score, attendance):
        self.date = date
        self.season = season
        self.week = week
        self.stadium = stadium
        self.roof = roof
        self.surface = surface
        self.vegas_line = vegas_line
        self.over_under = over_under
        self.weather = weather
        self.home_team = home_team
        self.home_score = home_score
        self.away_score = away_score
        self.away_team = away_team
        self.attendance = attendance
        self.plays = []

    def out(self):
        print("---------------------------")
        print("DATE: " + str(self.date))
        print("SEASON: " + str(self.season))
        print("WEEK: " + str(self.week))
        print("LOCATION: " + str(self.stadium))
        print("ROOF: " + str(self.roof))
        print("SURFACE: " + str(self.surface))
        print("VEGAS LINE: " + str(self.vegas_line))
        print("OVER UNDER: " + str(self.over_under))
        print("ATTENDANCE: " + str(self.attendance))
        print("......... WEATHER ..........")
        if self.weather != None:
            self.weather.out()
        print("######## HOME TEAM #########")
        self.home_team.out()
        print(str(self.home_score))
        print("###### VISITING TEAM #######")
        self.away_team.out()
        print(str(self.away_score))
        print("########## PLAYS ###########")
        print("QRT" + "\t" + "TIME" + "\t" + "LOC" + "\t" + "FIEL" + "\t" + "SITU" + "\t" + "DOWN" + "\t" + "TOGO" + "\t" + "SPEC" + "\t" + "HOME" + "\t" + "VISI" + "\t" + "WINP")
        for play in self.plays:
            play.out()
        print("---------------------------")

    def other_team(self, short):
        if short == self.home_team.short:
            return self.away_team
        return self.home_team


class PFR_Play:
    def __init__(self, quarter=0, time=15*60, location=35, field="", situation="", down=0, togo=0, description="", special="", score_home=0, score_away=0, win_percentage_home=0):
        self.quarter = quarter
        self.time = time
        self.location = location
        self.situation = situation
        self.field = field
        self.down = 0
        self.togo = 0
        self.description = description
        self.special = special
        self.score_home = score_home
        self.score_away = score_away
        self.win_percentage_home = win_percentage_home

    def out(self):
        print(str(self.quarter) + "\t" + str(self.time) + "\t" + str(self.location) + "\t" + str(self.field) + "\t" + str(self.situation) + "\t" + str(self.down) + "\t" + str(self.togo) + "\t" + self.special + "\t" + str(self.score_home) + "\t" + str(self.score_away) + "\t" + str(self.win_percentage_home))
        print(self.description)


def get_page(url):
    f = urllib.urlopen(url)
    return f.read()


def get_game_urls(year, week):
    urls = []
    u = url_week.replace("{year}", str(year)).replace("{week}", str(week))
    page = get_page(u)
    for line in page.split("\n"):
        if "Final</a>" in line:
            url = line.split("href=\"")[1].split("\"")[0]
            urls.append(url)
    return urls


def text(cell):
    #inside = ''.join(str(e) for e in cell.split("</td>")[0].split(">")[1:])
    string = ""
    ignore = False
    for c in cell:
        if c == '<':
            ignore = True
        elif c == '>':
            ignore = False
        elif not ignore:
            string += c
    return string


def get_rows(table):
    rows = []
    tr = table.split("<tr")
    for r in tr:
        if r != "" and r != " ":
            rows.append("<tr" + r.split("</tr>")[0] + "</tr>")
    return rows


def get_cells(row):
    cells = []
    td = row.replace("<tr >", "").replace("</tr>", "").split("<td")
    for t in td:
        if t != "" and t != " ":
            cells.append("<td" + t.split("</td>")[0] + "</td>")
    return cells


def get_team(page, home=True):

    scorebox = page.split("class=\"scorebox\"")[1].split("class=\"linescore_wrap\"")[0]
    name_a = scorebox.split("itemprop=\"name\">")[1].split("</a>")[0]
    score_a = int(scorebox.split("<div class=\"score\">")[1].split("</div>")[0])
    record_a = scorebox.split("<div class=\"score\">")[1].split("</div>")[1].split("<div>")[1].split("</div>")[0].split("-")

    name_b = scorebox.split("itemprop=\"name\">")[2].split("</a>")[0]
    score_b = int(scorebox.split("<div class=\"score\">")[2].split("</div>")[0])
    record_b = scorebox.split("<div class=\"score\">")[2].split("</div>")[1].split("<div>")[1].split("</div>")[0].split("-")

    away_short = page.split("\" data-stat=\"vis_stat\"")[0].split("<th aria-label=\"")[-1]
    home_short = page.split("\" data-stat=\"home_stat\"")[0].split("<th aria-label=\"")[-1]
    record = []

    if home:
        name = teams.teams[home_short]
        short = home_short
    else:
        name = teams.teams[away_short]
        short = away_short

    if name == name_a:
        score = score_a
        record = record_a
    elif name == name_b:
        score = score_b
        record = record_b

    return PFR_Team(name=name, short=short, record=list(map(int, record))), score


def get_date(page):
    datestring = page.split("<div class=\"scorebox_meta\">")[1].split("<div>")[1].split("</div>")[0]
    m = moment.date(datestring, 'dddd MMM D, Y').locale("US/Central")
    return m


def get_time_hours(page):
    timestring = page.split("<strong>Start Time</strong>")[1].split("</td>")[0].split("<")[0].replace(":","").replace(" ", "")
    h = timestring.replace("pm", "").replace("am", "")
    if "pm" in timestring:
        return int(h) + 12
    return int(h)


def get_week(page):
    return int(page.split("<div class=\"game_summaries compressed\">")[1].split("</a>")[0].split(">")[-1].split(" ")[1])


def get_stadium(page):
    return page.split("<strong>Stadium</strong>")[1].split("</a>")[0].split(">")[1].replace(":","")


def get_roof(page):
    return page.split("Roof")[1].split("</td>")[0].split(">")[-1]


def get_surface(page):
    return page.split("Surface")[1].split("</td>")[0].split(">")[-1].replace(":","")


def get_vegas_line(page):
    return page.split("Vegas Line")[1].split("</td>")[0].split(">")[-1].replace(":","")


def get_over_under(page):
    return page.split("Over/Under")[1].split("</td>")[0].split("</b>")[0].replace("<b>","").split(">")[-1].replace(":","")


def get_attendance(page):
    return int(page.split("Attendance")[1].split("</td>")[0].split("</a>")[0].split(">")[-1].replace(",", ""))


def get_game(url):

    page = get_page(website + url)
    print(page)

    homeTeam, homeScore = get_team(page, True)
    awayTeam, awayScore = get_team(page, False)

    date = get_date(page)
    hours = get_time_hours(page)
    date.add(hours=hours)
    week = get_week(page)
    stadium = get_stadium(page)
    roof = get_roof(page)
    surface = get_surface(page)
    vegas_line = get_vegas_line(page)
    over_under = get_over_under(page)
    attendance = get_attendance(page)

    game = PFR_Game(date=date.date, season=int(date.format("YYYY")), week=week, stadium=stadium, roof=roof, surface=surface, vegas_line=vegas_line, over_under=over_under, weather=None, home_team=homeTeam, away_team=awayTeam, home_score=homeScore, away_score=awayScore, attendance=attendance)

    # Get plays
    pbp_table_body = page.split("<table class=\"sortable stats_table\" id=\"pbp\"")[1].split("</table>")[0].split("<tbody>")[1].split("</tbody>")[0]
    pbp_rows = get_rows(pbp_table_body.replace("\n", ""))

    plays = []
    field = ""
    last_time = ""
    for row in pbp_rows:
        row = row.replace("<th", "<td").replace("</th", "</td")

        play = PFR_Play()
        if "thead" in row.split(">")[0]:
            continue
        elif "divider" in row.split(">")[0]:
            play.special = "turnover"
        elif "penalty" in row.split(">")[0]:
            play.special = "penalty"
        elif "score" in row.split(">")[0]:
            play.special = "score"
        elif "score" in row.split(">")[0]:
            play.special = "score"

        for cell in get_cells(row):
            print(cell)
            if "data-stat=\"quarter\"" in cell:
                q = text(cell)
                if q == "OT":
                    q = "5"
                play.quarter = int(q)
            elif "data-stat=\"qtr_time_remain\"" in cell:
                time = text(cell)
                if time == "":
                    play.time = -1
                else:
                    play.time = int(time.split(":")[0]) * 60 + int(time.split(":")[1])
            elif "data-stat=\"down\"" in cell:
                d = text(cell)
                if d != "" and d != " ":
                    play.down = int(d)
            elif "data-stat=\"yds_to_go\"" in cell:
                tg = text(cell)
                if tg != "" and tg != " ":
                    play.togo = int(tg)
            elif "data-stat=\"location\"" in cell:
                l = text(cell)
                if l != "" and l != " ":
                    team = l.split(" ")[0]
                    real_team = teams.real_short(team)
                    yard = int(l.split(" ")[1])
                    play.location = yard
                    play.field = real_team
                else:
                    play.location = 0
                    play.field = ""
            elif "data-stat=\"detail\"" in cell:
                play.description = text(cell)
            elif "data-stat=\"pbp_score_aw\"" in cell:
                play.score_away = int(text(cell))
            elif "data-stat=\"pbp_score_hm\"" in cell:
                play.score_home = int(text(cell))
            elif "data-stat=\"home_wp\"" in cell:
                wp = text(cell)
                if wp != "":
                    play.win_percentage_home = float(wp)
                else:
                    play.win_percentage_home = -1

        plays.append(play)

    game.plays = plays
    return game


def get_games(year, week, max=10000000):
    games = []
    game_urls = get_game_urls(year, week)
    for url in game_urls:
        game = get_game(url)
        game.out()
        games.append(game)
        if len(games) >= max:
            break
    return games
