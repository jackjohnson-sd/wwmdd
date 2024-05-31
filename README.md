Please Read me

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






