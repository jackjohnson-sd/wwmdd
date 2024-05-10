import nba_api.stats.library.data as nba_static
import pandas as pd

from plots import plot3, settings
from games_by_team import create_games_by_team, filterGamesByDateRange
from play_by_play import generatePBP 


def getTeamID(nba, team_abbreviation):
    # return '1610612760'
    # nba = get_teams()
    teams = nba[nba.abbreviation == team_abbreviation]
    return list(teams['id'])[0]

def get_teams():
    nba_teams = nba_static.teams
    nba = pd.DataFrame(nba_teams)
    nba.columns = ['id', 'abbreviation', 'nickname', 'year_founded', 'city', 'full_name', 'state','ch_years']
    return nba

from nba_api.stats.endpoints import leaguegamefinder
def get_games(team_id):

    # Query for games where the Celtics were playing
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    # The first DataFrame of those returned is what we want.
    return gamefinder.get_data_frames()[0]

def get_games_game_id(team_id):
        
    # Query for games where the Celtics were playing
    gamefinder = leaguegamefinder.LeagueGameFinder(
        team_id_nullable=team_id,
        # date_from_nullable = start,
        # date_to_nullable =  stop,
    )
    return gamefinder.get_data_frames()[0]

from nba_api.stats.endpoints import playbyplayv2
def get_play_by_play(game_id):
    pbp = playbyplayv2.PlayByPlayV2(game_id)
    pbp = pbp.get_data_frames()[0]

    cur_col_names = pbp.columns 
    for a in cur_col_names:
        la = a.lower()
        pbp.rename(columns={f'{a}':f'{la}'},inplace=True)

    return pbp

    
def load_NBA_Remote():

    _dfs = {}
    _dfs['team'] = get_teams()
    _team_id = getTeamID(_dfs['team'],'OKC')
    _dfs['game'] = get_games(_team_id)
    
    cur_col_names = _dfs['game'].columns 
    for a in cur_col_names:
        la = a.lower()
        _dfs['game'].rename(columns={f'{a}':f'{la}'},inplace=True)
    
    # print(cur_col_names)
    # print(_dfs['game'].columns)

    def _xt(id):
        _xt_map = {5:'Pre Season',
                   2:'Regular Season',
                   3:'All Star',
                   4:'Playoffs',
                   1:'Pre Season'
                   }
        return _xt_map[int(id[0])]
        
    _dfs['game']['season_type'] = _dfs['game']['season_id'].apply(lambda x:_xt(x))
      # strip leading digit from season, its signifies pre, post and regular season
    _dfs['game']['season_id'] = _dfs['game']['season_id'].apply(lambda x:x[1:])
    #place to save play by play dataframe
    _dfs['game']['play_by_play'] = [[pd.DataFrame([])]] * len(_dfs['game'])

    def _id_home(matchup):
        mu = matchup.split(' ')
        home = mu[2] if mu[1] == '@' else mu[0] 
        try: return str(getTeamID(_dfs['team'],home))
        except: return None

    def _id_away(matchup): 
        mu = matchup.split(' ')
        away = mu[2] if mu[1] != '@' else mu[0] 
        try: return str(getTeamID(_dfs['team'],away))
        except: return None
    
    _dfs['game']['team_id_home'] = _dfs['game']['matchup'].apply(lambda x:_id_home(x))
    _dfs['game']['team_id_away'] = _dfs['game']['matchup'].apply(lambda x:_id_away(x))
   
    _dfs_opp = {}

    def _away(g):

        mu = g.matchup.split(' ')
        if mu[1] != '@':
            away = mu[2] 
            home = mu[0]
        else:
            away = mu[0] 
            home = mu[2]
   
        opp_team_id = g.team_id_home if g.team_id == g.team_id_away else g.team_id_away 
        opp_away_msg = '_home' if g.team_id == g.team_id_away else '_away'
        if opp_team_id in _dfs_opp.keys():
            opp_game = _dfs_opp[opp_team_id]
        else:    
            opp_game = get_games_game_id(opp_team_id)
            _dfs_opp[opp_team_id] = opp_game 
        p = opp_game.query(f'GAME_DATE == "{g.game_date}"')    
        #    teamID = teams.query(f'abbreviation == "{teamNickName}"').id.values[0]     
        cur_col_names = list(p.columns) 
        for a in cur_col_names:
            la = a.lower()
            p.rename(columns={f'{a}':f'{la}{opp_away_msg}'},inplace=True)

        return p
    
    b = _dfs['game'].apply(_away, axis=1)

    # _dfs['game']['play_by_play'] = _dfs['game']['game_id'].apply(
    # lambda x:get_play_by_play(x))

    return _dfs


def tester():

    _SEASON     = settings.get('TESTDATA_SEASON')    # 2022

    def getTestData(_games):

        _START_DAY  = settings.get('TESTDATA_START_DAY') # 2023-01-01
        _STOP_DAY   = settings.get('TESTDATA_STOP_DAY')  # 2023-04-20
        _TEAM       = settings.get('TESTDATA_TEAM')      # OKC
        _SEASON     = settings.get('TESTDATA_SEASON')    # 2022

        results = filterGamesByDateRange( _START_DAY, _STOP_DAY, _games[_TEAM][_SEASON])
        return results, _START_DAY, _STOP_DAY, _TEAM, _SEASON

    _dfs = load_NBA_Remote()

    START_DATE = settings.get('DATA_BEGIN_DATE')
    DB_FILENAME = settings.get('DB_NAME')

    _gamesByTeam = create_games_by_team(_dfs, None, START_DATE, ['OKC'], web=True)    
    # _gamesByTeam = create_games_by_team(_dfs, None, START_DATE, ['OKC'], web=True)    

    test_data, _START_DAY, _STOP_DAY, _TEAM, _SEASON = getTestData(_gamesByTeam)
    
    our_player_stints_by_date      = generatePBP(test_data, _TEAM)
    opponent_player_stints_by_date = generatePBP(test_data, _TEAM, OPPONENT=True)

    for date in our_player_stints_by_date:     
        game_data = _gamesByTeam[_TEAM][_SEASON][date]
        play_by_play = test_data[date].play_by_play[0]

        plot3(
            our_player_stints_by_date[date], 
            game_data, 
            _TEAM, 
            play_by_play, 
            opponent_player_stints_by_date[date])    


    return 
    # OKC_id = getTeamID('OKC')
    # OKC_games = get_games(OKC_id)
    # p = OKC_games['GAME_ID'][0]
    # OKC_play_by_play = get_play_by_play(p)
    # return OKC_games, OKC_play_by_play
    # print('OK')
    
