
Kill Period 5 problem for nick

Please Read

Aug 09   -- 10 errors from 1200 games. most seem OT exit issues
            see .wwmdd/errors.txt
            stoped getting files twice for ALL type requests 
            implemented OKCvGSW type teams -> OKC and GSW play in the game
            summer league does not work.
            grep and line count examples in snippet_helpers.txt
            and months.sh

Aug 08   -- ALL as team selector, 3 52/53 errors in 1015 - 1231
Aug-07   -- LAL 0229, BOS 0110, MIA 0223, 
            POR 0302 0129            
            3 errors look the same,
            OKC 0204 is Scottie Barnes entering at OT2, 3:45 (ish)
            having NO events in OT1. NBA.com says he played the OT period
Aug-06   -- OKC 0204,CHI 1211,1108, GSW,DAL,NYK None, 
            OT works in all data files!,
            ** NO OT ** events displayed on graph
Aug-03   -- OKC 0204, NYK NONE, 1211,1108,  ALL OT Games
Aug-02   -- added GSW web and CSV no failures 
Aug-01   -- only errors for NYK,OKC 23-24 season is OKC 2OT 0204 game with TOR
July-29  -- PBP decode failues WEB 02/04  21600 20880 NOK
July-29  -- PBP decode failues CSV 02/04,04/21,12/14

July 20 -- a word about the stints and overlap data sets. see below ...
July 19 -- continued work on STINT,OVERLAY,BOX,PBP in CSV format
July 17 -- added BOX,STINT,OVERLAY as CSV file output
July 16 -- fixed issue with runnong slow, hanging we saw with Bruce
           fixed issues with .csv having 0 vs 0-0 as score
           SUB event now 'Starts/Stops playing'. vs begin/end etc
           data in world_tour placed in test_data, test_data added to .gitignore 
July 16 -- log now logs to file and console
July 14 -- log is back,stored in .wwmdd\logs, 
           -log,-nolog on cmdline else from settings.json
July 13 -- added -bs for batch, -it to set image type and -w to set wait in cmd line
July 11 -- added command line how-to's in readme.md
July 9 -- save img NOW WORKS. dpi and image type set in settings.json
July 8 -- save to pdf or jpg DOES NOT work. its all black
July 8 -- moved settings.json and colors.json to .wwmdd sub directory
July 8 -- added legend and tools to subplots, tested a bit
July 8 -- reworked command line again, fixed issues with CVS and RAW at same time 
July 7 -- ran WEB then FILE for OKC 23-24 season ~ 92 games
       --  ATL 11/06, BOS 04/03, TOR 02/04 fail play time check on WEB 
       --  ATL 11/06, BOS 04/03, TOR 02/04, SAC 12/14, NOP 04/21 failed FILE
July 7 -- added most all wwmdd.json entries to command line override
July 7 -- re-orged project, moved bunch of stuff into llm subdirectory
July 7 -- squashed all prior git commits -- might have been stupid
Jult 7 -- broke off wwmdd_colors.json from wwmdd.json
July 6 -- added overlap.py
July 5 -- some testing on OKC v BOS 2024-04-03?


Stints and Overlaps

OFF - is the number of points the 'TEAM' scored during the stint. 
DEF - is the number of points the 'TEAM, allowed during the stint.
±   -   is the difference in home - away scores from the start to end of the stint.
        i.e. a positive ± means ... IDK
        its normlized to 1 period. i.e. 1 point in 1 minutes is 1 12. 12 points 
        in one minute is a 12. 

PTS,REBS, etc. are all counts of what occured during the stint.

Overlaps can have 2 to 5 players. They show up in PLAYER1 ... PLAYER5 columns.
Overlaps are for the moment just between team members.

**Or not.**
# cmd line note∫
sh w.sh args ==>  python3 main.py args
(fyi -- if don't think the sh or the .sh is needed but yet to achieve this, with limited effort)

args 
-log    starts logger
-nolog  stops logger

-bs file ==> file is a list command line arguments
-it [jpg,pdf,png]  ==> sets image of save plot images
-w N ==> show image N seconds and then proceed
-s,-source [web,csv,db] ==> select one as source of data, web (NBA api), csv (files), or db (data base )
    if no source specifed uses source declared in .wwmdd/settngs.json

-d,-date YYYY-MM-DD [YYYY-MM-DD] ==> date or date range for 'web' sourced games, 1 entry date, 2 entries date range

-t,-team [TEAM]  ==> team i.e. [NYK, OKC, LAL, etc], select game(s) for this team (TODO support teams)

-f,-file [file or dirctory] ==> file or directory used for 'csv' source

-m,-make [plot,csv,raw,img,stint,overlap,box] ==> one or more things to make: 
    plot, csv - enhneced play by play, raw - unchanged play by play, stints by player, overlap by players
    img - png,jpg formatted image of plot, box score by player 

-p, -subplot [all,tools,stints,events,score,margin,periodscores,boxscore,legend] ==>
    one or more of things to place on plots

-j, -json [settings_file]  ==> i.e. -j oursetting.json, uses new oursettings.json file
    anthing done on the command line can be done via a modified settings.json 
    i.e no command line paramaters means use the json file

-c,-color [colors_file] ==> specify new colors for plots
    replaces .wwmdd/colors.json with this file.

    sh w.sh   
    -> runs the app based on whats in the .wwmdd/setting.json and colors.json file

    sh w.sh -s web -t OKC -d 2023-01-30 -m plot csv -p stints
    -> get data from NBA site for OKC on 2023-01-30 and show and save an enhanced play by play file, and show an plot with stints only
    
    sh w.sh -s web -t OKC -d 2023-01-01  2023-01-03 -m plot csv -p stints
    -> same as above but get all games that occured between 2023-01-01 and 2023-01-30

    sh w.sh -s csv -f OKCvGSW20230130.csv -m plot
    -> display plot for this file, .wwmdd/settings.json determines whats on plot

    sh w.sh -s csv -f llm\llm_training_data -m plot -p all
    -> display plot with all features data for csv files in llm\llm_training_data directory

    sh w.sh -j test_colors.json -s csv -f OKCvGSW20230130.csv -m plot
    -> same as above with terrible colors

# Data Source
    1. NBA API
    2. DB from Kaggle
    3. CSV files derived from 1 and 2 above
    4. JSON and cmd line applicaition control
    5. LLMs play by plays and analasys

# Intermediate data structures
    1. NBA API play by play format
    2. Text based play by play version with unused feilds deleted  12 kept, 25 deleted
    3. Players and teams
    4. Player IOs  i.e. IN and Out, Enter and Exit, Start and End 
    5. Player Events other than IOs
    6. IOs plus Events -> Stints i.e. (player, play time start, play time end, computed duration)
    7. Box score data collection and display  - min,pts,foul,block,assist,rebound O/D,3-2-FT makes and misses
    8. Box score summarry
    6. Plot data by player and team
            stints lines and markers
            events letters as markers
            event legend
            running score
            margins
            headlines
            score for periods
            shooting percentage

# Outputs
    1. Plots
    2. Box Score
    2. Console Diagnostics / log files
    3. Play by play updates to cvs files and dbs
    4. Interactions with LLMs (IN PROGRESS)
    6. player overlap
    5. pdfs, jpgs of plots

## data_flow

    get game_data if available or build from play_by_play
    get game_play_by_play web/DB/File

    web_data and Kaggle DB data get enhanceed player IO's by breaking SUB events into
    IN and OUT events and determing starting 5, ending 5, and players who 
    left or entered the game unanounced at mid period breaks.  These substityutions do not 

    CVS files are saved with the SUB emhancements and do not need this 
    Enhancment.

    WISH - On initial read of play by play, events are used to create markers, text and lines for plots, entries in the box score structure for each event.


get teams  -  Us and Opponent

prep history for each team                 --  PYTHON APP          
    last N games play_by_play for each team
    last F games play by play head to head
    last X games summary players and team

until no progress do:

    H2H_PBP.1 = LLM generates anticipated head to head play by play  - HUMAN Assisted

    H2H_PBP.1_eval = evaluated H2H_PBP.1  -- HUMAN 1

    H2H_PBP.2 = LLM uses H2H_PBP.1_eval generate second head to head play by play

    H2H_PBP.2_eval = evaluated H2H_PBP.2  -- HUMAN 2

    H2H_PBP.1_eval_eval = evaluated H2H_PBP.1_eval 

    happy = H2H_PBP.2_eval > lowest entry in leader board

    no progress = H2H_PBP.2_eval ! >  H2H_PBP.1_eval

if happy:
    place Effort in leader boad 


Current status  

    Summary data creatation  semi_automated
    LLM opus creating weak PBPs
    anticipated LLM production semi-automated
    LLM eval done by HUMAN, 
    LLM_eval eval done by HUMAN, 

Next Steps





***PAIRS***

PAIRS is the idea of using more than one AI in an application.

PAIRS start with the basic system information we've been using, 
i.e. csv formatted play by play, Event definition (SUB, FOULS, SCORES, etc),
stints, overlap, game time, playing time. 

It then adds the game in question.

We start by asking AI_1 a question from our question and  answer list. AI-2 
evaluates AI_1's response against our answer list.  If we 'like' the answer it's on to the next question, if its not we ask a secondary question. We repeat this process till we have no more helpers we then ask for its reasoning and halt. We log prompts, questions and answeres.

Our PAIRS answer file looks kinda like this:

Q: What teams played in this game?
A: OKC, GSW
H: Team names appear in the player1_team_abbreaviation colummn.
H: There can be only two teams in a game
Q: Who played the most for OCK?
A: OKC, GSW
H: Calculate minutes played by  .....
H: Who played the most means who played the most minutes.
Q: .....
A: .....
H: 

