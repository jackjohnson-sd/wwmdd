import argparse

# before anything else happens, likely too cheesy and won't servive long
parser = argparse.ArgumentParser()

helpme = \
"For example, 'sh w.sh -s web -t OKC -d 2024-03-04 -make cvs raw'\n " + \
"displays a plot from the OKC game on the date and \n" + \
"saves csv files in a RAW (as is, i.e. unmodified) format and \n" + \
"one without a RAW prefix and expanded player subtitution information.\n\n"

parser = argparse.ArgumentParser(
                    prog ='wwmdd',
                    description='Mangles and displays BB game event data',
                    epilog = helpme)
                    
parser.add_argument('-make','-m', nargs='+', 
                    metavar='stuff',
                    choices = ['plot','csv','raw','img','stints', 'overlaps'],   
                    help='What to do, -make plot csv')
parser.add_argument('-source','-s',
                    choices = ['web','csv'],          
                    help='where to get the data')
parser.add_argument('-with ',                help='which AI to use')
parser.add_argument('-file','-f',            help='where to save or get file(s)')
parser.add_argument('-team','-t',            help='team to use in game searh')
parser.add_argument('-date','-d', nargs='+', help='date or date range')
parser.add_argument('-subplots','-p',  nargs ='+',  
                    choices= ['all','tools', 'stints', 'events', 'score', 'margin', 'periodscores', 'boxscore',"legend","img"],
                    help ='select one or more sub plots to display')
parser.add_argument('-colors',       help='new plot colors file. defaults is colors.json ')
parser.add_argument('-json',         help='specify json file for app config. default is settings.json')
parser.add_argument('-test_players', help='DEBUG in testing normally []')

args = parser.parse_args()

import settings

settings.defaults = settings.default(args.json if args.json else None)

if args.file            != None: settings.defaults.set('FILE',                  args.file)
if args.team            != None: settings.defaults.set('TEAM',                  args.team)

if args.colors          != None: settings.defaults.set('COLOR_DEFAULTS',        args.colors)
if args.subplots        != None: settings.defaults.set('SUB_PLOTS',             args.subplots)
if args.test_players    != None: settings.defaults.set('TEST_PLAYERS',          args.test_players)
if args.date != None:
    start = args.date[0]
    try: 
        stop  = args.date[1]
    except: 
        stop = args.date[0]
        
    settings.defaults.set('START_DAY',start)
    settings.defaults.set('STOP_DAY',stop)
    
from logger import log
import main_web
import main_csv
import main_db
import claude
import gemini
import sys

if __name__ == '__main__':

    if args.make != None:
        stints = 'stints' in args.make
        olaps = 'overlaps' in args.make
        plot = 'plot'  in args.make
        csv_save = 'csv' in args.make
        raw_save = 'raw' in args.make
        img  = 'img' in args.make
        
        if plot: settings.defaults.set('SHOW_PLOT', True)
        settings.defaults.set('SAVE_PLOT_IMAGE', img)
        
        # no plot
        if not plot and stints or olaps:
            settings.defaults.set('PLAY_TIME_CHECK_ONLY',True)

        if olaps :
            if args.team != None:
                oteam = '' if args.team == None else args.team 
                settings.defaults.set('SHOW_OVERLAP',oteam)
        
        if stints: 
            settings.defaults.set('PLAY_TIME_CHECK_SHOW',True)
     
        do_web = 'web' in args.source
        do_csv = 'csv' in args.source
                    
        if do_web: 
            
            if args.date == None: print('-date required')
            if args.team == None : print('-team required')

            if None in [args.team,args.date]: sys.exit()

            settings.defaults.set('SOURCE','WEB')       
            settings.defaults.set('SAVE_RAW_GAME_AS_CSV',raw_save)
            settings.defaults.set('SAVE_GAME_AS_CSV', True if raw_save else csv_save)

            start = args.date[0]
            try:   stop  = args.date[1]
            except: stop = args.date[0]
        
            main_web.main(team=args.team, start=start, stop=stop)
            
        elif do_csv:

            if args.file == None : print('-file required')
            if None in [args.file]: sys.exit()

            settings.defaults.set('SOURCE','CSV')
            main_csv.main(args.file)

    else:

        data_source = settings.defaults.get('SOURCE')

        # get games and play by play from nba_api. get teams and dates from settings.json
        if 'WEB:' in data_source:
            main_web.main()
        # read play by play from file we or claude created.  file or directory name
        elif 'FILE:' in data_source:
            main_csv.main(data_source.split(':')[1])
        # send play_by_play files to claude and have him make one
        elif 'CLAUDE:' in data_source:
            claude.main(data_source.split(':')[1])
        elif 'GEMINI:' in data_source:
            gemini.main(data_source.split(':')[1])
        elif 'TOKENS:' in data_source:
            gemini.do_tokens(data_source.split(':')[1])

        # get games and play_by_play from kaggle sourced nba_sqlite DB.  date END spring 2023 !!!!!
        else:
            main_db.main()

        # modify launch.json  add this to use alternate json file
        # 'args': ['--json', 'settings2.json']