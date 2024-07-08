import argparse

# "args": ["--web","GSW","--start","2023-01-30","--stop","2023-01-30"],
# wwmdd --web GSW --start 2023-01-30 --stop 2023-01-30

# before anything else happens, likely too cheesy and won't servive long
parser = argparse.ArgumentParser()

parser.add_argument("--json",   help="specify json file. default is settings.json")
parser.add_argument("--tokens", help="report on tokens per file in a directory")
parser.add_argument("--show",   help="plot display file file in a directory")
parser.add_argument("--gemini", help="call gemini to get game for files in a directory")
parser.add_argument("--web",    help="show games via nba")
parser.add_argument("--start",  help="start date required for nba")
parser.add_argument("--stop",   help="stop date required for nba")
parser.add_argument("--noplot", help="do not plot just process play by play")

parser.add_argument("--show_plots",          help="which of the sub plots to display")
parser.add_argument("--save_game",           help="save game as CSV file.")
parser.add_argument("--play_time_check_only", help="do play time sanity check, no plot")
parser.add_argument("--play_time_check_show", help="show results of play time check, stints by player")
parser.add_argument("--show_overlap",         help="show simlutaneous playtimes for players")
parser.add_argument("--overlap_group",        help="overlay group size, one or more of [5,4,3,2]")
parser.add_argument("--save_game_dir",        help="where to save csv files")
parser.add_argument("--save_plot_as_pdf",    help="save plot as pdf file")
parser.add_argument("--save_plot_dir",       help="where to save plots")
parser.add_argument("--show_plot",           help="ON/OFF to show plots")
parser.add_argument("--team",                help="team to use in game searh")
parser.add_argument("--colors_json",         help="set json file to control colors")

parser.add_argument("--test_players",        help="DEBUG in testing normally []")
parser.add_argument("--save_subs",           help="DEBUG save SUB events only")
parser.add_argument("--save_raw_game",       help="DEBUG save raw game. No SUB Event expansion.")

args = parser.parse_args()

import settings
settings.defaults = settings.default(args.json if args.json else None)

if args.colors_json          != None: settings.defaults.set("COLOR_DEFAULTS",        args.colors_json)
if args.show_plots           != None: settings.defaults.set("SHOW_PLOTS",            args.show_plots)
if args.test_players         != None: settings.defaults.set("TEST_PLAYERS",          args.test_players)
if args.save_game            != None: settings.defaults.set("SAVE_GAME_AS_CSV",      args.save_game)
if args.save_game_dir        != None: settings.defaults.set("SAVE_GAME_DIR",         args.save_game_dir)
if args.save_raw_game        != None: settings.defaults.set("SAVE_RAW_GAME_AS_CSV",  args.save_raw_game)
if args.play_time_check_only != None: settings.defaults.set("PLAY_TIME_CHECK_ONLY",  args.play_time_check_only)
if args.play_time_check_show != None: settings.defaults.set("PLAY_TIME_CHECK_SHOW",  args.play_time_check_show)
if args.show_overlap         != None: settings.defaults.set("SHOW_OVERLAP",          args.show_overlap)
if args.overlap_group        != None: settings.defaults.set("OVERLAP_GROUP",         args.overlap_group)

if args.save_plot_as_pdf    != None: settings.defaults.set("SAVE_PLOT_AS_PDF",      args.save_plot_as_pdf)
if args.show_plot           != None: settings.defaults.set("SHOW_PLOT",             args.show_plot)
if args.start               != None: settings.defaults.set("START_DAY",             args.start)
if args.stop                != None: settings.defaults.set("STOP_DAY",              args.stop)
if args.team                != None: settings.defaults.set("TEAM",                  args.team)
if args.noplot              != None: settings.defaults.set("PLAY_TIME_CHECK_ONLY", args.noplot)

from logger import log
import main_web
import main_csv
import main_db
import claude
import gemini
import sys

if __name__ == "__main__":


    if args.show != None:
        settings.defaults.set("SOURCE", args.show)
        main_csv.main(args.show)

    elif args.gemini != None: gemini.main(args.gemini)
    elif args.tokens != None: gemini.do_tokens(args.tokens)
    elif args.web != None:
        if args.start == None:
            print("--start required")
            sys.exit()
        if args.stop == None:
            print("--stop required")
            sys.exit()
        # main_web.main(team=args.web, start=args.start, stop=args.stop)
        main_web.main(team=args.web, start=args.start, stop=args.stop)

    else:

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
        elif "TOKENS:" in data_source:
            gemini.do_tokens(data_source.split(":")[1])
        # get games and play_by_play from kaggle sourced nba_sqlite DB.  date END spring 2023 !!!!!
        else:
            main_db.main()

        # modify launch.json  add this to use alternate json file
        # "args": ["--json", "settings2.json"]
