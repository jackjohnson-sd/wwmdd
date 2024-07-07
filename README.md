Please Read me

Or not.

Data Source
    1. NBA API
    2. DB from Kaggle
    3. CSV files derived from 1 and 2 above
    4. JSON and cmd line applicaition control
    5. LLMs play by plays and analasys

Intermediate data structures
    1. NBA API play by play format
    2. Text based play by play version with unused feilds deleted  12 kept, 25 deleted
    3. Players and teams
    4. Player IOs  i.e. IN and Out, Enter and Exit, Start and End 
    5. Player Events other than IOs
    6. IOs plus Events -> Stints i.e. (player, play time start, play time end, computed duration)
    7. Box score data collection and display  - min,pts,foul,block,assist,rebound O/D,3-2-FT makes and misses
    8. Box score summarry
    6. Plot data by player and team
        a. stints lines and markers
        b. events letters as markers
        c. event legend

        d. running score
        d. margins
        e. headlines
        g. score for periods
        h. shooting percentage

Outputs
    1. Plots
    2. Box Score
    2. Console Diagnostics / log files
    3. Play by play updates to cvs files and dbs
    4. Interactions with LLMs (IN PROGRESS)
    5. pdfs, jpgs of plots

data_flow

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






