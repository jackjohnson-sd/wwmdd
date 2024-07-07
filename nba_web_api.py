import nba_api.stats.library.data as nba_static
import pandas as pd

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

# serves as cache for saving gets for team games
nba_games_by_team = {}

# nba needs mm/dd/yyyy vs. our yyyy-mm-dd  ... so change ours
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
