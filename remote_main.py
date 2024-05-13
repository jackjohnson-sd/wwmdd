import nba_api.stats.library.data as nba_static
import pandas as pd

from plots import plot3, settings
from games_by_team import create_games_by_team, filterGamesByDateRange
from play_by_play import generatePBP 

def getTeamID(nba, team_abbreviation):
    # return '1610612760'
    # nba = get_teams()
    teams = nba[nba.abbreviation == team_abbreviation]
    try:
        return list(teams['id'])[0]
    except:
        return None

def get_teams():
    nba_teams = nba_static.teams
    nba = pd.DataFrame(nba_teams)
    nba.columns = ['id', 'abbreviation', 'nickname', 'year_founded', 'city', 'full_name', 'state','ch_years']
    return nba

from nba_api.stats.endpoints import leaguegamefinder
def get_games(team_id):

    # Query for games we are playing
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    # The first DataFrame of those returned is what we want.
    return gamefinder.get_data_frames()[0]

nba_games_by_team = {}

def get_games_game_id(team_id):
    if team_id in nba_games_by_team.keys():
        return nba_games_by_team[team_id]
    else:
        # Query for games where we are playing
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            # date_from_nullable = start,
            # date_to_nullable =  stop,
        )

        the_games = gamefinder.get_data_frames()[0]
        nba_games_by_team[team_id] = the_games
        return the_games

from nba_api.stats.endpoints import playbyplayv2
def get_play_by_play(game_id):

    pbp = playbyplayv2.PlayByPlayV2(game_id)
    pbp = pbp.get_data_frames()[0]
    convert_column_names(pbp,'')
    return pbp

def convert_column_names(_df, txt_append):
    cur_col_names = _df.columns 
    for a in cur_col_names:
        la = a.lower()
        _df.rename(columns={f'{a}':f'{la}{txt_append}'},inplace=True)
    return _df.columns

def load_NBA_Remote(g_start,g_end):

    _dfs = {}
    _dfs['team'] = get_teams()

    _team_id = getTeamID(_dfs['team'],'OKC')
   
    _dfs['game'] = get_games_game_id(_team_id)
    _dfs['game'] = _dfs['game'][(_dfs['game'].GAME_DATE >= g_start)  &  (_dfs['game'].GAME_DATE <= g_end)] 

    convert_column_names(_dfs['game'],'')
    
    # create season_type column
    _xt = { 5:'Pre Season', 2:'Regular Season', 3:'All Star', 4:'Playoffs', 1:'Pre Season'}
    _dfs['game']['season_type'] = _dfs['game']['season_id'].apply(lambda x:_xt[int(x[0])])

    # strip leading digit from season, its signifies pre, post and regular season
    _dfs['game']['season_id'] = _dfs['game']['season_id'].apply(lambda x:x[1:])

    # place to save play by play dataframe
    _dfs['game']['play_by_play'] = [[pd.DataFrame([])]] * len(_dfs['game'])

    def _id_home(matchup, _hw):
        mu = matchup.split(' ')
        home = mu[2] if (mu[1] == '@') == _hw else mu[0] 
        try: return str(getTeamID(_dfs['team'],home))
        except: return None
 
    _dfs['game']['team_id_home'] = _dfs['game']['matchup'].apply(lambda x:_id_home(x,True))
    _dfs['game']['team_id_away'] = _dfs['game']['matchup'].apply(lambda x:_id_home(x, False))
   
    def _get_opp_game(g):

        mu = g.matchup.split(' ')
        # _mu = HOME_TEAM
        _mu = mu[0] if mu[1] != '@' else mu[2]

        opp_team_id = getTeamID(_dfs['team'], _mu)
   
        if opp_team_id == None: return None

        opp_msg = '_away' if g.team_abbreviation == _mu else '_home'

        opp_games = get_games_game_id(opp_team_id)
        opp_game = opp_games.query(f'GAME_DATE == "{g.game_date}"')
        convert_column_names(opp_game, opp_msg)
        return opp_game
    
    opponents = _dfs['game'].apply(_get_opp_game, axis=1)

    return _dfs, opponents

def main():

    _SEASON     = settings.get('TESTDATA_SEASON')    # 2022
    _TEAM       = settings.get('TESTDATA_TEAM')      # OKC

    def getTestData(_games):

        _START_DAY  = settings.get('TESTDATA_START_DAY') # 2023-01-01
        _STOP_DAY   = settings.get('TESTDATA_STOP_DAY')  # 2023-04-20
        _SEASON     = settings.get('TESTDATA_SEASON')    # 2022

        results = filterGamesByDateRange( _START_DAY, _STOP_DAY, _games[_TEAM][_SEASON])
        return results, _START_DAY, _STOP_DAY, _TEAM, _SEASON

    START_DATE = settings.get('DATA_BEGIN_DATE')
    END_DATE = settings.get('DATA_END_DATE')

    _dfs, opponents = load_NBA_Remote(START_DATE,END_DATE)

    _gamesByTeam = create_games_by_team(_dfs, None, START_DATE, [_TEAM], web=True)    

    test_data, _START_DAY, _STOP_DAY, _TEAM, _SEASON = getTestData(_gamesByTeam)
    
    our_player_stints_by_date      = generatePBP(test_data, _TEAM)
    opponent_player_stints_by_date = generatePBP(test_data, _TEAM, OPPONENT=True)

    for date in our_player_stints_by_date:  

        game_data = _gamesByTeam[_TEAM][_SEASON][date]
        play_by_play = test_data[date].play_by_play[0]

        _opp = None
        # find the opponent for this game_date  
        for x in opponents:
            # splits first column name to find our what we now call it
            hw = x.keys()[0].split('_')[2]
            if x[f'game_date_{hw}'][x.index[0]] == game_data.game_date:
                _opp = x
                break
        
        if type(_opp) == type(None): print('Trouble no opponent',game_data.matchup)
        else:
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

            plot3(
                our_player_stints_by_date[date], 
                game_data, 
                _TEAM, 
                play_by_play, 
                opponent_player_stints_by_date[date])    

    return 
    
