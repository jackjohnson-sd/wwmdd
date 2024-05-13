import pandas as pd
import numpy as np

def create_games_by_team(_dfs, db_con, START_DATE, TEAMS, web=False):

    _gamesByTeam = {}

    #for nickName in _dfs['team'].abbreviation:
    for nickName in TEAMS if TEAMS != [] else _dfs['team'].abbreviation:

        _games = getGames(_dfs['team'], _dfs['game'], nickName, 'Regular Season', START_DATE)
        seasons = list(set(_games.season_id))
        seasons.sort()
        _gamesBySeason = {}
        for season in seasons:
            seasonGames = _games.query(f'season_id == "{season}"')
            
            _gamesByDate = {}
            badBunny = 0
            for _idx, _game in seasonGames.iterrows():
                gameDay = _game.game_date.split(' ')[0] # trims the h:m:s part off
                if web :
                    from remote_main import get_play_by_play
                    pbps = get_play_by_play(_game.game_id)
                else:
                    qs = f"select * from play_by_play where game_id == '{_game.game_id}'"
                    pbps = pd.read_sql_query(qs, db_con)

                if pbps.shape[0] == 0:
                    badBunny += 1
                    if _game.play_by_play[0].shape[0] != 0:
                        print('BAD NO PBP', _game.game_date, _game.game_id)
                else:
                    _dfs['game'].loc[_idx, 'play_by_play'] = [pbps]
                    _game.play_by_play = [pbps]
                _gamesByDate[gameDay] = _game

            _gamesBySeason[season] = _gamesByDate
        
        _gamesByTeam[nickName] = _gamesBySeason      

    return _gamesByTeam       
  
def getGames(teams, games, teamNickName, seasonType, startDate):
    teamID = teams.query(f'abbreviation == "{teamNickName}"').id.values[0] 
    # if type(seasonType) != type([]):
    #     if seasonType == 'ALL':
    #         seasonType = ['Pre Season','Regular Season', 'All Star', 'Playoffs', 'Pre Season'] 
    #     else:
    #         seasonType = [seasonType]


    # season_type_filter =  games.season_type.isin(seasonType)
    # date_filter = games.game_date >= startDate
    # team_id_h = games.team_id_home == str(teamID)
    # team_id_a = games.team_id_away == str(teamID)

    # us = games[season_type_filter & date_filter & (team_id_h | team_id_a)]
    # return us
    return games.query(f'game_date >= "{startDate}" and season_type == "{seasonType}" and (team_id_home == "{teamID}" or team_id_away == "{teamID}")').copy()

def filterGamesByDateRange(start, stop, games):
    z2 = {key: value for key, value in games.items() if start <= key <= stop}
    return z2
