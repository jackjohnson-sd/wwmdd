import pandas as pd
from loguru import logger

from plots import plot3, defaults, quitGame
from play_by_play import generatePBP, dump_pbp
import nba_web_api as nba


def _get_opp_game(g, teams):

    #  matchup = away @ home or home vs. away
    #  us = g.abbrev...
    #  them = not us
    mup = g.matchup.split(' ')
    us   = g.team_abbreviation
    them = mup[2] if mup[0] == us else mup[0]
    home = mup[2] if mup[1] == '@' else mup[0]
    away = mup[0] if mup[1] == '@' else mup[2]
    opp_msg = '_away' if home == us else '_home'

    # print(g.matchup,' us:',us,' them:',them,'home:',home,'away:',away,'msg append:',opp_msg)
    opp_team_id = nba.getTeamID(teams, them)

    if opp_team_id == None: return None

    opp_game = nba.get_games_game_id(opp_team_id, g.game_date, g.game_date)

    # opp_game = opp_games.query(f'GAME_DATE == "{g.game_date}"')
    nba.convert_column_names(opp_game, opp_msg)
    return opp_game

def main(team=None,start=None,stop=None):
    
    if team != None: defaults.set('TEAM',team)
    if start != None: defaults.set('START_DAY',start)
    if stop != None: defaults.set('STOP_DAY',stop)
        
    _TEAM       = defaults.get('TEAM')      # OKC
    _START_DAY  = defaults.get('START_DAY') # 2023-01-01
    _STOP_DAY   = defaults.get('STOP_DAY')  # 2023-04-20

    teams = nba.get_teams()

    if team not in teams.abbreviation.tolist():
        
        logger.error(f'invalid team name {team}')

    else:      
        _team_id = nba.getTeamID(teams,_TEAM)

        games = nba.get_games_game_id(_team_id, _START_DAY, _STOP_DAY)

        prev = None
        for i, game_data in games.iterrows():
            
            if type(prev) != type(None):
                if game_data.game_date == prev.game_date:
                    logger.error(f'2 games for {_TEAM } on {game_data.game_date}')
                    break 
                
            prev = game_data
                
            _opp = _get_opp_game(game_data, teams)

            opp_columns = _opp.keys()
            _our_HA = 'home' if 'blk_away' in opp_columns else 'away'

            # we're combining the home and away game record
            # append _away or _home.  This keeps compatibility 
            # with Kaggle data set ( which keep our older stuff working)
            # def format_and_exclude(x,not_these):
            def fne(x,not_these):
                return x if x in not_these else f'{x.lower()}_{_our_HA}'

            our_col_names = list(map(lambda x:fne(x,['game_id','game_date']), game_data.keys()))
            game_data = pd.Series(data = game_data.to_list(), index = our_col_names)

            # merge us and opponents column names  ones _home, the other _away
            our_col_names.extend(opp_columns.to_list())

            # values for both us and opponent
            new_values = list(game_data.values)
            new_values.extend(list(_opp.values[0]))

            game_data = pd.Series(new_values,index=our_col_names)
            game_data.play_by_play = nba.get_play_by_play(game_data.game_id)
            
            if game_data.play_by_play.shape[0] != 0:
                
                our_playerstints_and_boxscore = generatePBP(game_data, _TEAM, get_opponent_data = False)
                opp_playerstints_and_boxscore = generatePBP(game_data, _TEAM, get_opponent_data = True)

                plot3(_TEAM, game_data,
                    our_playerstints_and_boxscore, 
                    opp_playerstints_and_boxscore)    
            else:
                logger.error(f'Bad news! No play_by_play data. {game_data.game_date} {game_data.matchup_away} ')

    return 

