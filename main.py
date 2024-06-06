import argparse
import settings

# before anything else happens, likely too cheesy and won't servive long
parser = argparse.ArgumentParser()
parser.add_argument("--json", help="specify json file. default is settings.json")
parser.add_argument("--tokens", help="report on tokens per file in a directory")
args = parser.parse_args()

settings.defaults = settings.default(args.json if args.json else None)

import main_web
import main_csv
import main_db
import claude
import gemini

if __name__ == "__main__":
    
    if args.tokens != None:
        gemini.do_tokens(args.tokens)
    else:

        data_source = settings.defaults.get('SOURCE')

        # get games and play by play from nba_api. get teams and dates from settings.json
        if   'WEB:'  in data_source:  main_web.main()
        # read play by play from file we or claude created.  file or directory name
        elif 'FILE:' in data_source:  main_csv.main(data_source.split(':')[1])
        # send play_by_play files to claude and have him make one
        elif 'CLAUDE:' in data_source:  claude.main(data_source.split(':')[1])
        elif 'GEMINI:' in data_source:  gemini.main(data_source.split(':')[1])
        elif 'TOKENS:' in data_source:  gemini.do_tokens(data_source.split(':')[1])
        # get games and play_by_play from kaggle sourced nba_sqlite DB.  date END spring 2023 !!!!!
        else: main_db.main()  
        
        # modify launch.json  add this to use alternate json file 
        # "args": ["--json", "settings2.json"]
