import sys
import pandas as pd
from data_management import loadNBA_data
from play_by_play import generatePBP 
from plots import plot3, settings
import remote_main
#
# get arguments, if any
# 

def getArgs():
  opponent = "ANY"
  plotNbr = 13

  for i in range (len(sys.argv)):  # Check for arguments
    if sys.argv[i] == '?':
      print("Usage: python argparse3.py <opponent=opponentName> <plotnumber=plotnumber>")
      sys.exit(1) 

    if (sys.argv[i].find("opponent=")>-1):
      opponent = sys.argv[i].split('=')
      opponent = opponent[1] 
      # test print("opponent = ",opponent)

    if (sys.argv[i].find("plotnumber=")>-1):
      plotNbrStr = sys.argv[i].split('=')
      plotNbr = int(plotNbrStr[1]) 
      # test print("plotnumber = ",plotNbr)
    
  return(opponent, plotNbr)

dfs         = {}    # has everthing that was in db as dict of DateFrame by column name from DB
gamesByTeam = {}    # gamesByTeam[NICK_NAME][SEASON][DATE]  ['OKC']['2022']['2022-12-01']
db_con      = None  # keep this around to get play_by_play when needed

def main():

    _TEAM       = settings.get('TESTDATA_TEAM')      # OKC
    _START_DAY  = settings.get('TESTDATA_START_DAY') # 2023-01-01
    _STOP_DAY   = settings.get('TESTDATA_STOP_DAY')  # 2023-04-20
    DB_FILENAME = settings.get('DB_NAME')
    
    _dfs, db_con = loadNBA_data(DB_FILENAME)

    _team_id = _dfs['team'][_dfs['team'].abbreviation == _TEAM].id.iloc[0]

    qs = f'game_date >= "{_START_DAY} 00:00:00" and game_date <= "{_STOP_DAY} 00:00:00" and team_id_home == "{int(_team_id)}"'
    games = _dfs['game'].query(qs)
    
    for i, game_data in games.iterrows():

        qs = f"select * from play_by_play where game_id == '{game_data.game_id}'"
        play_by_play = pd.read_sql_query(qs, db_con)

        game_data.play_by_play = [play_by_play]
        td = {game_data.game_date:game_data}
        our_player_stints_by_date      = generatePBP(td, _TEAM)
        opponent_player_stints_by_date = generatePBP(td, _TEAM, OPPONENT=True)
          
        _date = list(our_player_stints_by_date.keys())[0]
        plot3(
            our_player_stints_by_date[_date], 
            game_data, 
            _TEAM, 
            play_by_play, 
            opponent_player_stints_by_date[_date])    

    db_con.close()

if __name__ == "__main__":

    if settings.get('DB_NAME') =='web':
      remote_main.main()
    else: main()
    