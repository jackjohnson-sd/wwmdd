import sys
import pandas as pd
from data_management import loadNBA_data
from play_by_play import generatePBP,dump_pbp
from plots import plot3, settings
import remote_main
#
# get arguments, if any
#

def getArgs():

    opponent = None

    for i in range (len(sys.argv)):  # Check for argumentsif sys.argv[i] == '?':
        print("Usage: python argparse3.py <opponent=opponentName> <plotnumber=plotnumber>")

        if (sys.argv[i].find("opponent=")>-1):
            opponent = sys.argv[i].split('=')
            opponent = opponent[1]
            # test print("opponent = ",opponent)

        plotNbrStr = ''
        if (sys.argv[i].find("plotnumber=")>-1):
            plotNbrStr = sys.argv[i].split('=')
        # test print("plotnumber = ",plotNbr)
    
    return opponent

dfs         = {}    # has everthing that was in db as dict of DateFrame by column name from DB
db_con      = None  # keep this around to get play_by_play when needed

def main():

    _TEAM       = settings.get('TEAM')      # OKC
    _START_DAY  = settings.get('START_DAY') # 2023-01-01
    _STOP_DAY   = settings.get('STOP_DAY')  # 2023-04-20
    DB_FILENAME = settings.get('DB_NAME')

    _dfs, db_con = loadNBA_data(DB_FILENAME)
    # brutal appoach to get data from the first 'cell' in a data frame
    _team_id = _dfs['team'][_dfs['team'].abbreviation == _TEAM].id.iloc[0]

    qs = f'game_date >= "{_START_DAY} 00:00:00" and game_date <= "{_STOP_DAY} 00:00:00" and team_id_home == "{int(_team_id)}"'
    games = _dfs['game'].query(qs)

    for i, game_data in games.iterrows():

        qs = f"select * from play_by_play where game_id == '{game_data.game_id}'"
        play_by_play = pd.read_sql_query(qs, db_con)

        game_data.play_by_play = play_by_play  # returns a series?
        
        our_playerstints_and_boxscore      = generatePBP(game_data, _TEAM)
        opponent_playerstints_and_boxscore = generatePBP(game_data, _TEAM, OPPONENT=True)

        plot3(_TEAM, game_data,
            our_playerstints_and_boxscore,
            opponent_playerstints_and_boxscore)

    db_con.close()


def main_csv(filename):

    df = pd.read_csv(filename, keep_default_na=False)
    df.iloc[::-1] # reverse dataframe

    event_map = {
        '2POINT'			: [1,1], 
        '2POINT_ASSIST'	    : [1,1,2], 
        '3POINT'            : [1,1],
        '3POINT_ASSIST'     : [1,2],
        'FTMAKE'            : [3,1], 
        'FTMISS'            : [3,1], 
        '2POINTMISS'        : [3,1],
        '3POINTMISS'        : [3,1],
        '2POINTMISS_BLOCK'  : [3,1,2],
        '3POINTMISS_BLOCK'  : [3,1,2],
        'REBOUND'			: [4,1],
        'STEAL'				: [5,1], 
        'TURNOVER'			: [5,2], 
        'STEAL_TURNOVER'    : [5,1,2],
        'FOUL'				: [6,1], 
        'SUB'		        : [8,1,2],  # id#, player[1,2,3] 
        'TIMEOUT'			: [None], 
        'END_GAME'			: [None], 
        'END_PERIOD'		: [None], 
        'TIP'				: [None], 
        }
    new_cols = [
        'eventmsgtype', 'period', 'pctimestring', 
        'homedescription','neutraldescription', 'visitordescription', 
        'score', 'scoremargin', 
        'player1_name', 'player1_team_abbreviation',
        'player2_name', 'player2_team_abbreviation',
        'player3_name', 'player3_team_abbreviation',
       ]

    def bethere(row):
        return event_map[row.eventmsgtype]
    
    oink = []
    for i, r in df.iterrows():
        if r.eventmsgtype in event_map.keys():
            id = event_map[r.eventmsgtype]
            
            if id[0] != None:
                a = [
                id[0],
                r.period, r.pctimestring,
                r.homedescription,
                r.neutraldescription,
                r.visitordescription,
                r.score, r.scoremargin,
                r.player1_name, r.player1_team_abbreviation,
                r.player2_name, r.player2_team_abbreviation,
                r.player3_name, r.player3_team_abbreviation]
                
                oink.extend([a])
        
    play_by_play = pd.DataFrame(
                data    = oink,           # values
                # index   = oink [1:,0],    # 1st column as index
                columns = new_cols)  
    
    home = list(play_by_play[play_by_play.homedescription != ''].player1_team_abbreviation)[0]
    away = list(play_by_play[play_by_play.homedescription == ''].player1_team_abbreviation)[0]
    game_data = {
    'season_id_home' :'',
    'team_id_home'	: '',
    'team_abbreviation_home': home,
    'team_name_home': '',
    'game_id'		: '',
    'game_date'		: '2024-10-10',
    'matchup_home'	: 'DAL @ OKC',
    'wl_home'		: 'W',
    'blk_home'		: '',
    'season_id_away': '',
    'team_id_away'	: '',
    'team_abbreviation_away': away,
    'team_name_away': '',
    'game_id_away'	: '',
    'game_date_away': '',
    'matchup_away'	: '',
    'wl_away'		: '',
    'blk_away'        : '',
    'tov_away'        : '',
    'pf_away'         : '',
    'plus_minus_away' :'',
    'play_by_play'    : play_by_play
    }

    pds_game_data = pd.Series(game_data)
    
    our_playerstints_and_boxscore      = generatePBP(pds_game_data, home)
    opponent_playerstints_and_boxscore = generatePBP(pds_game_data, home, OPPONENT=True)

    plot3(home, pds_game_data,
        our_playerstints_and_boxscore,
        opponent_playerstints_and_boxscore)

    
    """
    csvcol = 'event,period,playclock,score,scoremargin,player1,player2,player3,homedescription,visitordescription,neutraldescription'
    pbpevents = {
        'SUB_OUT': '', 
        'OREB': '', 
        'MADE_FG_ASSIST': '', 
        'FOUL': '', 
        'MISS_FREE_THROW': '', 
        'BLOCK': '', 
        'END_PERIOD': '', 
        'SUBSTITUTION': '', 
        'END_GAME': '', 
        'DREB': '', 
        'MADE_FREE_THROW': '', 
        'TURNOVER': '', 
        'TIP': '', 
        'TIMEOUT': '', 
        'MISS_FG': '', 
        'MADE_FG': '', 
        'STEAL' : ''
    }
    v = {
    'season_id_home' :'',
    'team_id_home'	: '',
    'team_abbreviation_home': 'MIN',
    'team_name_home': '',
    'game_id'		: '',
    'game_date'		: '2024-10-10',
    'matchup_home'	: 'DAL @ OKC',
    'wl_home'		: 'W',
    'blk_home'		: '',
    'season_id_away': '',
    'team_id_away'	: '',
    'team_abbreviation_away': '',
    'team_name_away': '',
    'game_id_away'	: '',
    'game_date_away': '',
    'matchup_away'	: '',
    'wl_away'		: '',
    'blk_away'        : '',
    'tov_away'        : '',
    'pf_away'         : '',
    'plus_minus_away' :'',
    'play_by_play'    : ''
    }


    return 0

"""
if __name__ == "__main__":

    data_source = settings.get('DB_NAME')

    if data_source == 'web':      remote_main.main()
    elif 'FILE:' in data_source:  main_csv (data_source.split(':')[1])
    else:                         main()