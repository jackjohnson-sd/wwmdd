import sys
import argparse

import settings
from loguru import logger

# before anything else happens, likely too cheesy and won't servive long

def start_logger(args):

    logger.remove()
    
    try:
        log_ret = settings.defaults.get("LOG_RETENTION")
        log_rot = settings.defaults.get("LOG_ROTATION")
        log_level = settings.defaults.get("LOG_LEVEL")
        log_colorize = settings.defaults.get("LOG_COLORIZE")
        log_filename = settings.defaults.get("LOG_FILE")
    except:
        # in the event of disaster
        log_ret = "1 week"
        log_rot = "1 hour"
        log_level = "DEBUG"
        log_colorize = []
        log_filename = ".wwmdd/logs/DISASTER.log"

    log_format = "<green>{time:YY-MM-DD HH:mm:ss}</green> <level>{level: <8}</level> <magenta>{file: >10} {line: <4}</magenta> {message}"
    log_format_error = "<red>{time:YYYY-MM-DD HH:mm:ss}</red> <level>{level: <8}</level> <magenta>{file: >10} {line: <4}</magenta> {message}"

    logger.add(
        log_filename,
        format=log_format,
        level=log_level,
        rotation=log_rot,
        retention=log_ret,
        colorize="wwmdd.log" in log_colorize,
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        sys.stdout,
        # format=log_format,
        level=log_level,
        colorize="sys.stdout" in log_colorize,
        backtrace=True,
        diagnose=True,
    )

    logger.enable("")  # explicitly enable, assume default is on
    logger.disable("")  # explicity disable. what are doing this to?

    if args == None:
        if settings.defaults.get("LOG"):
            logger.enable("")
    else:
        if args.log:    logger.enable("")
        if args.nolog:  logger.disable("")

        if not args.log and not args.nolog:
            if settings.defaults.get("LOG"):
                logger.enable("")
            else:
                logger.disable("")

BS_EXIT_ = '#!#exit'
BS_COMMENT_ = '#!#'


def get_args():

    parser = argparse.ArgumentParser(
        prog="wwmdd",
        description="Mangles and displays BB game event data",
        epilog="For example, './w.sh -s web -t OKC -d 2024-03-04 -make plot -p plot",
    )

    parser.add_argument("-log", action="store_true")
    parser.add_argument("-nolog", action="store_true")

    parser.add_argument(
        "-make","-m",
        nargs="+",
        metavar = "stuff",
        choices=[
            "plot", 
            "log",      "nolog",
            "csv",      "raw",
            "stints",   "overlaps",
            "box",      "img",],
            
        help = "What to do?  ",
    )
    parser.add_argument("-source", "-s", default='web',choices=["web", "csv"], help="where to get the data")
    parser.add_argument("-file", "-f", metavar='file',help="where to save or get file(s)")
    parser.add_argument("-team","-t", nargs="+", metavar='team', help="team to use in game search")
    parser.add_argument("-date","-d", metavar='date(s)', nargs="+", help="date or date range")
    parser.add_argument("-subplots","-p",
        nargs="+",
        choices = [
            "all",      "tools",
            "stints",   "events",
            "score",    "margin",
            "periodscores",
            "legend",   "boxscore", ],
        help="select one or more sub plots to display",)
    
    parser.add_argument("-json", help="configuration update. default is settings.json")
    parser.add_argument("-colors", help="plot colors update. default is colors.json")

    # debug and other stuff we don't tell about
    parser.add_argument("-with", help=argparse.SUPPRESS)
    parser.add_argument("-wait", "-w", nargs=1, help=argparse.SUPPRESS)
    parser.add_argument("-combo", "-cb", nargs="+", help=argparse.SUPPRESS)
    parser.add_argument("-trim", help=argparse.SUPPRESS)
    parser.add_argument("-console", help=argparse.SUPPRESS)
    parser.add_argument("-DBG", help=argparse.SUPPRESS)
    parser.add_argument("-test_players", help=argparse.SUPPRESS)
    parser.add_argument("-bs", nargs=1, help=argparse.SUPPRESS)
    parser.add_argument("-it", nargs=1, choices=["pdf", "png", "jpg"], help=argparse.SUPPRESS)

    try:
        args = parser.parse_args()
    except SystemExit:
        logger.error("Argument parsing error")
        return None, "Error"

    return args, parser

def get_argset(args, parser):
    
    argset = []
    
    if args.bs == None:
        # use command line auguments
        argset = [[args, sys.argv[1:]]]

    else:
        # use each line from this file as a cmmd line for the app
        try:
            # try and open the file and read it
            with open(args.bs[0]) as f:
                lines = f.readlines()

        except:
            logger.error(f"problem reading {args.bs[0]} file.")
            
        for i,line in enumerate(lines):

            if BS_EXIT_ in line:
                argset.extend([[None, line.strip()]])
                break

            if BS_COMMENT_ in line:
                argset.extend([[None, line.strip()]])
                continue

            line = line.replace("\n", "")
            line = line.strip()
            line = line.split(" ")
            if "" in line:
                line.remove("")

            if len(line) != 0:
                try:
                    aargs = parser.parse_args(line)
                    argset.extend([[aargs, line]])
                except SystemExit:
                    logger.error(f"-bs {args.bs[0]} line {i+1} parsing error ")
                    logger.error((" ").join(line))
        
    return argset

def set_args(args):
    
    if args.log:    logger.enable("")
    if args.nolog:  logger.disable("")

    if args.json            != None:
        logger.debug(f"updating settings {args.json}")
        settings.defaults.update(args.json)

    if args.colors          != None:
        logger.debug(f"updating colors {args.colors}")
        settings.defaults.update_colors(args.colors)
        
    if args.DBG             != None:    settings.defaults.set("DBG", args.DBG)
    if args.trim            != None:    settings.defaults.set("TRIM", args.trim)
    if args.console         != None:    settings.defaults.set("CONSOLE", args.console)
    if args.it              != None:    settings.defaults.set("SAVE_IMAGE_TYPE", args.it[0])
    if args.test_players    != None:    settings.defaults.set("TEST_PLAYERS", args.test_players)
    if args.wait            != None:    settings.defaults.set("PLOT_WAIT", int(args.wait[0]))
    
    if args.team            != None:    settings.defaults.set("TEAM", args.team)
    if args.subplots        != None:    settings.defaults.set("PARTS", args.subplots)

    if args.combo           != None:

        try:
            settings.defaults.set(
                "OVERLAP_GROUP", list(map(lambda x: int(x), args.combo[0].split(" ")))
            )
        except:
            logger.error(
                f"problem in combo parameter {args.combo}. combo paramater ignored"
            )

    if args.date            != None:

        start = args.date[0]
        stop = start if len(args.date) == 1 else args.date[1]

        settings.defaults.set("START_DAY", start)
        settings.defaults.set("STOP_DAY", stop)


args, parser = get_args()

# I apologize for the complexity of this
settings.defaults = settings.default()

cfn = settings.defaults.get("COLOR_DEFAULTS")
settings.colors = settings.default(cfn,cfd=True)

import json
with open('.wwmdd/patch.json', "r") as f:
    settings.patches = json.load(f)
  
start_logger(args)
logger.info("wwmdd begins! ")


if __name__ == "__main__":

    if args != None:

        argset = get_argset(args, parser)

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

            if args == None:
                
                if type(_args[1]) == type('a'):
                    
                    logger.info(_args[1])
                
                    if BS_EXIT_ in _args[1]: break
                    if BS_COMMENT_ in _args: continue
                    
                else:
                    logger.error('argument error not a string.')
            else:  
                  
                set_args(args)

                logger.info((" ").join(_args[1]))
                
                if args.make != None:

                    stints      = "stints" in args.make
                    olaps       = "overlaps" in args.make
                    plot        = "plot" in args.make
                    csv_save    = "csv" in args.make
                    raw_save    = "raw" in args.make
                    box         = "box" in args.make
                    img         = "img" in args.make
                    log         = "log" in args.make
                    nolog       = "nolog" in args.make

                    if nolog:
                        logger.warning("Logging disabled.")
                        logger.disable("")

                    if log:
                        logger.enable("")
                        logger.warning("Loggging enabled.")

                    if plot:
                        settings.defaults.set("SHOW_PLOT", True)

                    if box:
                        settings.defaults.set("SAVE_BOX_SCORE", True)
                        
                    if img:
                        settings.defaults.set("SAVE_IMAGE", img)

                    # no plot
                    if not plot and stints or olaps:
                        settings.defaults.set("PLAY_TIME_CHECK_ONLY", True)

                    if olaps:
                        settings.defaults.set("SAVE_OVERLAP", True)

                    if stints:
                        settings.defaults.set("SAVE_STINTS", True)

                    if args.colors != None:
                        settings.defaults.update_colors(args.colors)

                    do_web = "web" in args.source
                
                    do_csv = "csv" in args.source

                    if not do_csv:
                        do_web = True

                    if do_web:

                        if args.date == None: logger.error("-date required")
                        
                        if args.team == None: 
                            settings.defaults.set("SAVE_GAME", args.team)
                            #  logger.error("-team required")

                        if None in [ args.date]: continue

                        settings.defaults.set("SAVE_RAW", raw_save)
                        settings.defaults.set("SAVE_GAME", csv_save)

                        if args.file:
                            settings.defaults.set("SAVE_DIR", args.file)

                        start = args.date[0]
                        stop = start if len(args.date) == 1 else args.date[1]

                        settings.defaults.set("SOURCE", 'WEB')
                        main_web.main(team=args.team, start=start, stop=stop)

                    elif do_csv:

                        settings.defaults.set("SOURCE", 'CSV')
                        if args.file == None: logger.error("-file required")
                        
                        if None in [args.file]: continue
                        
                        main_csv.main(args.file)

            settings.defaults.stuff = original_stuff
            settings.colors.stuff = original_colors

    if len(sys.argv) == 1:

        logger.info("no args - default settings")
        data_source = settings.defaults.get("SOURCE")

        # get games and play by play from nba_api. get teams and dates from settings.json
        if "WEB:" in data_source:
            main_web.main()

        # read play by play from file we or claude created.  file or directory name
        elif "FILE:" in data_source:
            main_csv.main(data_source.split(":")[1])

        # send play_by_play files to claude and have him make one
        elif "CLAUDE:" in data_source:
            claude.main(data_source.split(":")[1])

        elif "GEMINI:" in data_source:
            gemini.main(data_source.split(":")[1])

        elif "OPEN_AI:" in data_source:
            gpt.main(data_source.split(":")[1])

        elif "TOKENS:" in data_source:
            gemini.do_tokens(data_source.split(":")[1])

        elif "DB:" in data_source:
            main_db.main()
        # get games and play_by_play from kaggle sourced nba_sqlite DB.  date END spring 2023 !!!!!

        elif "TESTPARTSCALE:" in data_source:
            import main_TestPlotScale

            main_TestPlotScale.main()

        else:
            logger.error("NO SOURCE specified in .wwmdd/setttings.json.")

    logger.info("wwmdd ends.")
