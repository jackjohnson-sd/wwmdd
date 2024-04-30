# JackA JackB JackC BruceD
import sys
from datetime import datetime,timedelta

from data_management import loadNBA_data
from play_by_play import generatePBP 
from box_score import box_score
from plots import plot3
from games_by_team import create_games_by_team,filterGamesByDateRange


#
# get arguments, if any
# 
# this is test for vs code/git collaboration test
# check below for gittest

def  getArgs():
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

# gitest
# main starts below
#

dfs = {}            # has everthing that was in db as dict of DateFrame by column name from DB
gamesByTeam = {}    # gamesByTeam[NICK_NAME][SEASON][DATE]  ['OKC']['2022']['2022-12-01']
db_con = None       # keep this around to get play_by_play when needed

def loadNBA():

    START_SEASON = '2020-01-01'
    DB_FILENAME = "nba.sqlite"

    global db_con

    _dfs, db_con = loadNBA_data(DB_FILENAME)

    _gamesByTeam = create_games_by_team(_dfs, db_con, START_SEASON, ['OKC'])    

    return _dfs, _gamesByTeam   
  
def getTestData(_games):

    _START_DAY = '2023-01-10'
    _STOP_DAY = '2023-04-10'
    _TEAM = 'OKC'
    _SEASON = '2022'

    results = filterGamesByDateRange( _START_DAY, _STOP_DAY, _games[_TEAM][_SEASON])
    return results, _START_DAY, _STOP_DAY, _TEAM, _SEASON

def main():

    global dfs 
    global gamesByTeam

    # gamesByTeam['OKC']['2022]['2023-01-03']  -- gets game via team,year,game_date
    # Get arguments, if any
    # more gittest
    print("START WWMDD")

    opponent, plotNbr = getArgs()        
    #print("opponent - ", opponent)      # test code, comment to run  
    #print("plotnumber - ", plotNbr)     # test code, comment to run 
    #sys.exit(1)                         # test code, comment to run 

    dfs,gamesByTeam = loadNBA()

    test_data, _START_DAY, _STOP_DAY, _TEAM, _SEASON = getTestData(gamesByTeam)
    
    our_player_stints_by_date = generatePBP(test_data, _TEAM)
    opponent_player_stints_by_date = generatePBP(test_data, _TEAM, OPPONENT=True)

    for date in our_player_stints_by_date:     
        game_data = gamesByTeam[_TEAM][_SEASON][date]
        play_by_play = test_data[date].play_by_play[0]

        plot3(
           our_player_stints_by_date[date], 
           game_data, 
           _TEAM, 
           play_by_play, 
           opponent_player_stints_by_date[date])    

    """
    tests(test_data)
    t = pd.DataFrame(test_data[0]).T
    plot1(t)
    #input("Press Enter to continue...")
    plot2(t)
    #input("Press Enter to continue...")
    """

if __name__ == "__main__":
    main()

print("END WWMDD")

