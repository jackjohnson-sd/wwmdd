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

    df = pd.read_csv(filename)
    df.iloc[::-1] # reverse dataframe

    event_map = {
        'MADE_FG'			: [1,1], 
        'MADE_FG_ASSIST'	: [1,2], 
        'SUBSTITUTION'		: [8,2],  # id#, player[1,2,3] 
        'SUB_OUT'			: [8,1], 
        'MISS_FG'			: [2,1], 
        'BLOCK' 			: [2,2],
        'MADE_FREE_THROW'	: [3,1], 
        'MISS_FREE_THROW'	: [3,1], 
        'DREB'				: [4,1], 
        'OREB'				: [4,1], 
        'STEAL'				: [5,1], 
        'TURNOVER'			: [5,1], 
        'FOUL'				: [6,1], 
        'TIMEOUT'			: [None], 
        'END_GAME'			: [None], 
        'END_PERIOD'		: [None], 
        'TIP'				: [None], 
        }

    new_cols = [
        'eventmsgtype',  
        'period', 
        'pctimestring', 
        'homedescription', 
        'neutraldescription', 
        'visitordescription', 
        'score', 
        'scoremargin', 
        'player1_name', ''
        'player2_name', 
        'player3_name'
       ]

    def bethere(row):
        return event_map[row.event]
    
    oink = []
    for i, r in df.iterrows():
        id = bethere(r)
        if id[0] != None:
            a = [
            r.period, 
            r.playclock,
            id[0],
            r.homedescription,
            r.neutraldescription,
            r.visitordescription,
            r.score,
            r.scoremargin,
            r.player1,
            r.player2,
            r.player3]
            oink.extend([a])
        
    play_by_play = pd.DataFrame(
                data    = oink,           # values
                # index   = oink [1:,0],    # 1st column as index
                columns = new_cols)  
    
    print(play_by_play.shape)

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
    pbp = [
        'game_id', 
        'eventnum', 'eventmsgtype', 'eventmsgactiontype', 
        'period', 'wctimestring', 'pctimestring', 
        'homedescription', 'neutraldescription', 'visitordescription', 
        'score', 'scoremargin', 
       
        'person1type', 'player1_id', 'player1_name', 
        'player1_team_id', 'player1_team_city',
           'player1_team_nickname', 'player1_team_abbreviation', 
       
           'person2type','player2_id', 'player2_name', 
           'player2_team_id', 'player2_team_city',
           'player2_team_nickname', 'player2_team_abbreviation',
        
           'person3type', 'player3_id', 'player3_name', 
           'player3_team_id','player3_team_city',
           'player3_team_nickname', 'player3_team_abbreviation',
           'video_available_flag']
      
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


if __name__ == "__main__":

    data_source = settings.get('DB_NAME')

    if data_source == 'web':      remote_main.main()
    elif 'FILE:' in data_source:  main_csv (data_source.split(':')[1])
    else:                         main()
