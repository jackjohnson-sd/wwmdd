import nba_api.stats.library.data as nba_static
import pandas as pd

from plots import plot3, settings
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

def reformat(d):
    t = d.split('-')
    return '/'.join([f'{t[1]}',f'{t[2]}',f'{t[0]}'])

def get_games_game_id(team_id, _start, _stop):
    KEY = str(team_id) + _start + _stop
    if KEY in nba_games_by_team.keys():
        return nba_games_by_team[KEY]
    else:
        # Query for games where we are playing
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable = team_id,
            
            date_from_nullable = reformat(_start),
            date_to_nullable =  reformat(_stop)
        )

        the_games = gamefinder.get_data_frames()[0]
        
        convert_column_names(the_games,'')
        nba_games_by_team[KEY] = the_games
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

def _get_opp_game(g, teams):

    mu = g.matchup.split(' ')
    # _mu = HOME_TEAM
    _mu = mu[0] if mu[1] != '@' else mu[2]

    opp_team_id = getTeamID(teams, _mu)

    if opp_team_id == None: return None

    opp_msg = '_away' if g.team_abbreviation == _mu else '_home'

    opp_game = get_games_game_id(opp_team_id, g.game_date, g.game_date)

    # opp_game = opp_games.query(f'GAME_DATE == "{g.game_date}"')
    convert_column_names(opp_game, opp_msg)
    return opp_game

def main():

    _TEAM       = settings.get('TESTDATA_TEAM')      # OKC
    _START_DAY  = settings.get('TESTDATA_START_DAY') # 2023-01-01
    _STOP_DAY   = settings.get('TESTDATA_STOP_DAY')  # 2023-04-20

    _dfs = {}
    _dfs['team'] = get_teams()

    _team_id = getTeamID(_dfs['team'],_TEAM)

    _dfs['game'] = get_games_game_id(_team_id, _START_DAY, _STOP_DAY)

    for i, game_data in _dfs['game'].iterrows():

        _opp = _get_opp_game(game_data,_dfs['team'])
        play_by_play = get_play_by_play(game_data.game_id)
        game_data.play_by_play = [play_by_play]

        td = {game_data.game_date:game_data}  # to keep things woroking with DB sourced data
        our_player_stints_by_date      = generatePBP(td, _TEAM)
        opponent_player_stints_by_date = generatePBP(td, _TEAM, OPPONENT=True)
          
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
        _date = list(our_player_stints_by_date.keys())[0]
        plot3(
            our_player_stints_by_date[_date], 
            game_data, 
            _TEAM, 
            play_by_play, 
            opponent_player_stints_by_date[_date])    
  
    # GET TEAM_ID FROM NAME
    # GET DATE RANGE
    # GET GAMES FOR TEAM AND DATE RANGE
    # FOR EACH GAME IN GAMES
    #   GET GAME RECORD
    #   GET OPPONENT GAME RECORD
    #   GET PBP FOR GAME RECORD
    #   MAKE BOX SCORE FROM ROSTER
    #   MAKE STINTS FROM PPBP
    #   FIX COLUM NAMES IN GAME RECORDs AND PBP
    #   MERGE OPPONENT AND OUR GAME RECORD
    #   DETERMINE HOME AWAY WINNER LOSER
    return 

