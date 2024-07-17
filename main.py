import sys
import argparse

import settings
from loguru import logger

# before anything else happens, likely too cheesy and won't servive long

def get_args():
    
    parser = argparse.ArgumentParser(
                        prog='wwmdd',
                        description='Mangles and displays BB game event data',
                        epilog="For example, './w.sh -s web -t OKC -d 2024-03-04 -make plot -p plot"
                        )
                        
    parser.add_argument('-log', action='store_true')
    parser.add_argument('-nolog', action='store_true')

    parser.add_argument('-make','-m', nargs='+', 
                        metavar='stuff',
                        choices = ['plot','csv','raw','img','stints', 'overlaps','log','nolog'],   
                        help='What to do, -make plot csv')
    parser.add_argument('-source','-s',
                        choices = ['web','csv'],          
                        help='where to get the data')
    parser.add_argument('-with ',                help='which AI to use')
    parser.add_argument('-file','-f',            help='where to save or get file(s)')
    parser.add_argument('-team','-t',            help='team to use in game searh')
    parser.add_argument('-date','-d', nargs='+', help='date or date range')
    parser.add_argument('-subplots','-p',  nargs ='+',  
                        choices= ['all','tools', 'stints', 'events', 'score', 'margin', 'periodscores', 'boxscore',"legend"],
                        help ='select one or more sub plots to display')
    parser.add_argument('-json',         help='specify json file for app config. default is settings.json')
    parser.add_argument('-colors',       help='new plot colors file. defaults is colors.json')

    # debug and other stuff we don't tell about
    parser.add_argument('-wait','-w',    nargs=1, help=argparse.SUPPRESS)
    parser.add_argument('-combo','-cb',  nargs='+', help=argparse.SUPPRESS)
    parser.add_argument('-trim',         help=argparse.SUPPRESS)
    parser.add_argument('-console',      help=argparse.SUPPRESS)
    parser.add_argument('-DBG',          help=argparse.SUPPRESS)
    parser.add_argument('-test_players', help=argparse.SUPPRESS)
    parser.add_argument('-bs', nargs=1,    help=argparse.SUPPRESS)
    parser.add_argument('-it', nargs=1, choices= ['pdf', 'png','jpg'],   help=argparse.SUPPRESS)

    try:
        args = parser.parse_args()
    except SystemExit:
        logger.error('Argument parsing error')
        return None,'Error'
    
    return args, parser

def start_logger(args):   
     
    logger.remove()
    try:    
        log_ret = settings.defaults.get('LOG_RETENTION')
        log_rot = settings.defaults.get('LOG_ROTATION')
        log_level = settings.defaults.get('LOG_LEVEL')
        log_colorize = settings.defaults.get('LOG_COLORIZE')
        log_filename = settings.defaults.get('LOG_FILE')
    except:
        # in the event of disaster
        log_ret = '1 week'
        log_rot = '1 hour'
        log_level = 'DEBUG'
        log_colorize = []
        log_filename = '.wwmdd/logs/DISASTER.log'
        
    log_format = "<green>{time:YY-MM-DD HH:mm:ss}</green> <level>{level: <8}</level> <magenta>{file: >10} {line: <4}</magenta> {message}"
    log_format_error = "<red>{time:YYYY-MM-DD HH:mm:ss}</red> <level>{level: <8}</level> <magenta>{file: >10} {line: <4}</magenta> {message}"

    logger.add(log_filename,
               format=log_format,
               level=log_level,
               rotation=log_rot, 
               retention=log_ret,
               colorize= 'wwmdd.log' in log_colorize,
               backtrace=True,
               diagnose=True)
    
    logger.add(sys.stdout,
               format=log_format,
               level=log_level,
               colorize='sys.stdout' in log_colorize,
               backtrace=True,
               diagnose=True)
    
    logger.enable('')   # explicitly enable, assume default is on 
    logger.disable('')  # explicity disable. what are doing this to?

    if args == None:
        if settings.defaults.get('LOG'): logger.enable('')
    else:    
        if args.log:   logger.enable('')
        if args.nolog: logger.disable('')

        if not args.log and not args.nolog:
            if settings.defaults.get('LOG'): logger.enable('')
            else: logger.disable('')

def get_argset(args, parser):
    argset = []
    if args.bs != None:
        # use each line from this file as a cmmd line for the app 
        try:
            # try and open the file and read it            
            with open(args.bs[0]) as f: lines = f.readlines()
            
            for line in lines:
                
                if '##exit' in line:
                    argset.extend([[None,line.strip().split(' ')]])
                    break
                
                if '##' in line:
                    logger.info(line.strip())
                    continue
                        
                line = line.replace('\n','')
                line = line.strip()
                line = line.split(' ')
                if '' in line: line.remove('')
                
                if len(line) != 0:
                    try:
                        aargs = parser.parse_args(line)
                        argset.extend([[aargs,line]])
                    except SystemExit:
                        logger.error(f'-bs {args.bs[0]} line parsing Error ')
                        logger.error((' ').join(line))
                        # logger.error(e)
        except:
            logger.error(f'ERROR -- Problem reading {args.bs[0]} file.')
    else:
        # use command line as auguments
        argset = [[args,sys.argv[1:0]]]
    return argset

def set_args(args):
    # things we don't tell about
    # settings.defaults.set('LOG', args.log)
    if args.log: logger.enable('')
    if args.nolog: logger.disable('')
    
    if args.DBG             != None: settings.defaults.set('DBG',       args.DBG)
    if args.trim            != None: settings.defaults.set('TRIM',      args.trim)
    if args.console         != None: settings.defaults.set('CONSOLE',   args.console)
    if args.wait            != None: settings.defaults.set('SHOW_PAUSE',  int(args.wait[0]))
    if args.it              != None: settings.defaults.set('SAVE_PLOT_TYPE', args.it[0])
    
    if args.combo           != None: 
        
        try:
            settings.defaults.set('OVERLAP_GROUP', list(map(lambda x:int(x),args.combo[0].split(' '))))
        except:
            logger.error(f'Problem in combo parameter {args.combo}. combo paramater ignored')
        
    if args.test_players    != None: settings.defaults.set('TEST_PLAYERS', args.test_players)

    if args.file            != None: settings.defaults.set('FILE', args.file)

    if args.team            != None: settings.defaults.set('TEAM', args.team)
       
    if args.subplots        != None: settings.defaults.set('SUB_PLOTS', args.subplots)
    
    if args.date            != None:
        
        start = args.date[0]
        stop = start if len(args.date) == 1 else args.date[1]
            
        settings.defaults.set('START_DAY',start)
        settings.defaults.set('STOP_DAY',stop)

args, parser = get_args()

settings.defaults = settings.default()

cfn = settings.defaults.get('COLOR_DEFAULTS')
settings.colors = settings.default(cfn)

start_logger(args)
logger.info('wwmdd begins! ')

if args != None:

    if args.json != None: 
        settings.defaults.update(args.json)

    if args.colors != None: 
        logger.debug(f'Updating colors {args.colors}') 
        settings.defaults.update_colors(args.colors)

if __name__ == '__main__':

    if args != None:
            
        argset = get_argset(args,parser)

        import main_web
        import main_csv
        import main_db
        import llm_api.open_ai as gpt
        import llm_api.claude as claude
        import llm_api.gemini as gemini

        for _args in argset:
            
            original_stuff = settings.defaults.stuff.copy()
            original_colors = settings.colors.stuff.copy()
           
            args = _args[0]
            logger.info((' ').join(_args[1]))
            
            if args == None: break
            
            set_args(args)
            
            if args.make != None:
                stints = 'stints' in args.make
                olaps = 'overlaps' in args.make
                plot = 'plot'  in args.make
                csv_save = 'csv' in args.make
                raw_save = 'raw' in args.make
                img  = 'img' in args.make
                log  = 'log' in args.make
                nolog = 'nolog' in args.make
                
                if nolog:
                    logger.warning('Logging disabled.')
                    logger.disable('')

                if log:
                    logger.enable('')
                    logger.warning('Loggging enabled.')
                
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
                
                if args.colors          != None:
                    logger.info(f'Color update via {args.colors}.')
                    settings.defaults.update_colors(args.colors)
        
                do_web = 'web' in args.source
                do_csv = 'csv' in args.source
                            
                if do_web: 
                    if args.date == None: logger.error('-date required')
                    if args.team == None : logger.error('-team required')

                    if None in [args.team,args.date]: continue
                    else:
                        settings.defaults.set('SOURCE','WEB')       
                        settings.defaults.set('SAVE_RAW_GAME_AS_CSV',raw_save)
                        settings.defaults.set('SAVE_GAME_AS_CSV', True if raw_save else csv_save)

                        if args.file: 
                            settings.defaults.set('SAVE_GAME_DIR',args.file)
                            settings.defaults.set('SAVE_PLOT_DIR',args.file)

                        start = args.date[0]
                        stop = start if len(args.date) == 1 else args.date[1]
                        
                        main_web.main(team=args.team, start=start, stop=stop)
                    
                elif do_csv:

                    if args.file == None : log.error('-file required')
                    if None in [args.file]: continue
                    else:

                        settings.defaults.set('SOURCE','CSV')
                        main_csv.main(args.file)

            settings.defaults.stuff = original_stuff
            settings.colors.stuff = original_colors

    if len(sys.argv) == 1:

        logger.error('settings taken from defaults')    
        data_source = settings.defaults.get('SOURCE')

        # get games and play by play from nba_api. get teams and dates from settings.json
        if 'WEB:' in data_source: main_web.main()

        # read play by play from file we or claude created.  file or directory name
        elif 'FILE:' in data_source: main_csv.main(data_source.split(':')[1])

        # send play_by_play files to claude and have him make one
        elif 'CLAUDE:' in data_source: claude.main(data_source.split(':')[1])

        elif 'GEMINI:' in data_source: gemini.main(data_source.split(':')[1])

        elif 'OPEN_AI:' in data_source: gpt.main(data_source.split(':')[1])

        elif 'TOKENS:' in data_source: gemini.do_tokens(data_source.split(':')[1])

        elif 'DB:' in data_source: main_db.main()
        # get games and play_by_play from kaggle sourced nba_sqlite DB.  date END spring 2023 !!!!!

        else: logger.error('NO SOURCE specified in .wwmdd/setttings.json.')
            
    logger.info('wwmdd ends.')
