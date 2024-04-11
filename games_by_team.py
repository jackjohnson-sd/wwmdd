import pandas as pd
import numpy as np

def create_games_by_team(_dfs, db_con, SEASON, TEAMS):

    _gamesByTeam = {}
    #for nickName in _dfs['team'].abbreviation:
    for nickName in TEAMS:

        _games = getGames(_dfs['team'], _dfs['game'], nickName, 'Regular Season', SEASON)
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
    return games.query(f'season_id >= "{startDate}" and season_type == "{seasonType}" and (team_id_home == "{teamID}" or team_id_away == "{teamID}")')

def filterGamesByDateRange(start, stop, games):
    return  {key: value for key, value in games.items() if start <= key <= stop}
