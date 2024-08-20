import pandas as pd
from loguru import logger
import nba_web_api as nba

from plots import plot3, defaults
from play_by_play import generatePBP
from utils import make_cache_fn,fn_root
import main_csv
from settings import ommisions

def _get_opp_game(g, teams):

    #  matchup = away @ home or home vs. away
    #  us = g.abbrev...
    #  them = not us
    mup = g.matchup.split(" ")
    us = g.team_abbreviation

    them = mup[2] if mup[0] == us else mup[0]
    home = mup[2] if mup[1] == "@" else mup[0]
    away = mup[0] if mup[1] == "@" else mup[2]

    opp_msg = "_away" if home == us else "_home"

    try:

        opp_team_id = nba.getTeamID(teams, them)
        if opp_team_id == None:
            return None

        opp_game = nba.get_games_game_id(opp_team_id, g.game_date, g.game_date)
        nba.convert_column_names(opp_game, opp_msg)

        if opp_game.shape != (1, 28):
            logger.error(f"data wrong shape for {them} {g.game_date} {g.matchup}")
            return None

        return opp_game

    except:

        logger.error(f"opponent data retrieval {g.game_date} {g.matchup}")
        return None

def insert_row(new_row,old_df):

    from pandas import DataFrame, concat

    test_cols = [ 'eventmsgtype','period', 'pctimestring',
        'neutraldescription',
        'score', 'scoremargin',
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation'
    ]
   
    new_row = new_row.split(',')
    
    period = new_row[1]
    pctime = new_row[2]
    s = f'period == {period} & pctimestring == "{pctime}"'
        
    us = old_df.query(s) 
    index = us.index.tolist()
    values = us.values.tolist()
    insert_point = index[-1]
    new_insert = values[-1]
    df_cols = us.columns.tolist()
    for j,c in enumerate(df_cols):
        if c in test_cols:
            i = test_cols.index(c)
            new_insert[j] = new_row[i]     
        
    line = DataFrame([new_insert], columns=df_cols)
    df2 = concat([old_df.iloc[0:insert_point], line, old_df.iloc[insert_point:]]).reset_index(drop=True)
    return df2

def main(team=None, start=None, stop=None):

    if team != None:
        defaults.set("TEAM", team)
        
    if start != None:
        defaults.set("START_DAY", start)
        
    if stop != None:
        defaults.set("STOP_DAY", stop)

    _TEAMS = defaults.get("TEAM")  # OKC
    _START_DAY = defaults.get("START_DAY")  # 2023-01-01
    _STOP_DAY = defaults.get("STOP_DAY")  # 2023-04-20

    teams = nba.get_teams()
    NBA_TEAMS = teams.abbreviation.tolist()
    NBA_TEAMS.sort()

    if _TEAMS == ["ALL"]:
        _TEAMS = NBA_TEAMS

    games_weve_did = {}

    for team in _TEAMS:

        opp_team = None

        if "v" in team:
            opp_team = team.split("v")
            team = opp_team[0]
            opp_team = opp_team[1]

            if opp_team not in NBA_TEAMS:
                logger.error(f"no opposing team named {team}")
                continue

        if team not in NBA_TEAMS:

            logger.error(f"no team named {team}")

        else:

            try:

                _team_id = nba.getTeamID(teams, team)
                games = nba.get_games_game_id(_team_id, _START_DAY, _STOP_DAY)

            except:
                logger.error(f"{team} not in NBA? or timeout problem?")
                continue

            prev = None
            for i, game_data in games.iterrows():

                fn, cwd, isfile = make_cache_fn(game_data)
                if isfile:
                    #  logger.error(f'{game_data.matchup} lets do this with csv')
                     defaults.push()
                     defaults.set('SOURCE','CSV')
                     main_csv.main(fn)
                     defaults.pop()
                     continue
                # else:
                #     print(f'not in cache {fn}')
                # make a key as T1.T2.DATE TI.T2 alpha sorted
                # so we don't do this twice
                # team names are sorted so WAS ends up having 0
                # the sorting is so we can tell how far we've progressed
                # the key it self keeps uf from getting the game twice when w're doing groups

                if opp_team != None:
                    if opp_team not in game_data.matchup:
                        continue

                ttd = game_data.matchup.split(" ")
                ttd.sort()

                for x in ['@','vs.']:
                    while x in ttd:
                        ttd.remove(x)
              
                ttd.extend([game_data.game_date])
                ttd = ".".join(ttd)

                if ttd in games_weve_did.keys():
                    continue

                games_weve_did[ttd] = True

                if type(prev) != type(None):

                    if game_data.game_date == prev.game_date:
                        logger.error(f"2 games for {team } on {game_data.game_date}")
                        continue

                prev = game_data

                try:

                    _opp = _get_opp_game(game_data, teams)

                    if _opp is None:
                        continue

                except:
                    logger.warning(f"opponent not in NBA? or timeout problem?")
                    continue

                opp_columns = _opp.keys()
                _our_HA = "home" if "blk_away" in opp_columns else "away"

                # we're combining the home and away game record
                # append _away or _home.  This keeps compatibility
                # with Kaggle data set ( which keep our older stuff working)
                # def format_and_exclude(x,not_these):
                def fne(x, not_these):
                    return x if x in not_these else f"{x.lower()}_{_our_HA}"

                our_col_names = list(
                    map(lambda x: fne(x, ["game_id", "game_date"]), game_data.keys())
                )
                game_data = pd.Series(data=game_data.to_list(), index=our_col_names)

                # merge us and opponents column names  ones _home, the other _away
                our_col_names.extend(opp_columns.to_list())

                # values for both us and opponent
                new_values = list(game_data.values)
                new_values.extend(list(_opp.values[0]))

                game_data = pd.Series(new_values, index=our_col_names)

                try:
                    game_data.play_by_play = nba.get_play_by_play(game_data.game_id)
                except:
                    logger.error(
                        f"data retreival {game_data.game_date} {game_data.matchup_away}"
                    )
                    continue

                if game_data.play_by_play.shape[0] != 0:

                    ommisions_key = fn_root(game_data) 
                    if ommisions_key in ommisions.keys():
                        game_data.play_by_play = insert_row(ommisions[ommisions_key], game_data.play_by_play)
                        logger.debug(f'ommisions applied to this game, {ommisions_key}')
                    our_playerstints_and_boxscore = generatePBP(
                        game_data, team, get_opponent_data=False
                    )
                    opp_playerstints_and_boxscore = generatePBP(
                        game_data, team, get_opponent_data=True
                    )

                    plot3(
                        team,
                        game_data,
                        our_playerstints_and_boxscore,
                        opp_playerstints_and_boxscore,
                    )
                else:
                    logger.error(
                        f"Bad news! No play_by_play data. {game_data.game_date} {game_data.matchup_away} "
                    )

    return
