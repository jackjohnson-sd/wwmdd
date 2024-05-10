import pandas as pd
import numpy as np

def create_games_by_team(_dfs, db_con, START_DATE, TEAMS, web=False):

    _gamesByTeam = {}

    #for nickName in _dfs['team'].abbreviation:
    for nickName in TEAMS if TEAMS != [] else _dfs['team'].abbreviation:

        _games = getGames(_dfs['team'], _dfs['game'], nickName, 'Regular Season', START_DATE)
        seasons = list(set(_games.season_id))
        seasons.sort()
        #print(nickName, end = ' ')
        _gamesBySeason = {}
        for season in seasons:
            seasonGames = _games.query(f'season_id == "{season}"')
            
            _gamesByDate = {}
            badBunny = 0
            for index, _game in seasonGames.iterrows():
                gameDay = _game.game_date.split(' ')[0] # trims the h:m:s part off
                if web :
                    from remote_data import get_play_by_play
                    print(season,_game.game_date)
                    pbps = get_play_by_play(_game.game_id)
                else:
                    qs = f"select * from play_by_play where game_id == '{_game.game_id}'"
                    pbps = pd.read_sql_query(qs, db_con)

                if pbps.shape[0] == 0:
                    badBunny += 1
                    if _game.play_by_play[0].shape[0] != 0:
                        print('BADBAD', _game.game_date, _game.game_id)
                    #print('BB ',gameDay,season,game.game_id)
                else:
                    _dfs['game'].loc[index, 'play_by_play'] = [pbps]
                    _game.play_by_play = [pbps]
                    #print(index,gameDay,pbps.shape)
                _gamesByDate[gameDay] = _game

            #print(f' {season}:{len(_gamesByDate)}:{badBunny} ',end='')
            _gamesBySeason[season] = _gamesByDate
        #print()
        
        _gamesByTeam[nickName] = _gamesBySeason      

    return _gamesByTeam       
  
def getGames(teams, games, teamNickName, seasonType, startDate):
    teamID = teams.query(f'abbreviation == "{teamNickName}"').id.values[0] 
    # return games.query(f'season_id >= "{startDate}" and season_type == "{seasonType}" and (team_id_home == "{teamID}" or team_id_away == "{teamID}")')
    return games.query(f'game_date >= "{startDate}" and season_type == "{seasonType}" and (team_id_home == "{teamID}" or team_id_away == "{teamID}")')

def filterGamesByDateRange(start, stop, games):
   
    def x_X(x):
        if start <= x <= stop:
            return x
        else:
            return None

    z = list(map(lambda x:x_X(x),games))
    z2 = {key: value for key, value in games.items() if start <= key <= stop}
    return z2
    return  {key: value for key, value in games.items() if start <= key <= stop}

# Index(['season_id', 'team_id', 'team_abbreviation', 'team_name', 'game_id',
#        'game_date', 'matchup', 'wl', 'min', 'pts', 'fgm', 'fga', 'fg_pct',
#        'fg3m', 'fg3a', 'fg3_pct', 'ftm', 'fta', 'ft_pct', 'oreb', 'dreb',
#        'reb', 'ast', 'stl', 'blk', 'tov', 'pf', 'plus_minus', 'season_type',
#        'play_by_play'],
#       dtype='object')