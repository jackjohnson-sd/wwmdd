rm -f llm/llm_training_data/* 
rm -f .wwmdd/logs/* 
rm -f .wwmdd/.csvs/* 

echo "  --  CANARY -- FAILS when PHX_0305 works
ORL-SAC 2OT fails with fix for PHX_0305, 
works when players PCO at the end of each period"
./w.sh -s web -t SAC -d 2024-01-03  -m plot raw stints box

echo "   -- THIS IS PHX_0305 
Aaron Gordon needs 5 min for OT with no events to work"
./w.sh -s web -t PHX -d 2024-03-05  -m plot raw stints box

echo "   -- SAME ISSUE AS PHX_0305
Beasley shouldn't get full OT credit"
./w.sh -s web -t CHI -d 2023-12-11  -m plot raw stints box

echo "   -- SAME ISSUE AS PHX_0305
Derrick White needs 5 min for OT wuth no events in work"
./w.sh -s web -t MIN -d 2024-01-10  -m plot raw stints box

echo "  -- SAME ISSUE AS PHX_0305
Grayson Allen and Watanabe need OT minutes without events"
./w.sh -s web -t PHX -d 2023-11-08  -m plot raw stints box


echo " -- FIXED  2OT game 
... don't know what was wrong"
./w.sh -s web -t POR -d 2024-03-02  -m plot raw stints box

echo " -- FIXED  2OT game 
... don't know what was wrong"
./w.sh -s web -t SAS -d 2024-01-20  -m plot raw stints box

echo "   -- FIXED 
techincal foul adh0c naming"
./w.sh -s web -t PHI -d 2024-01-29  -m plot raw stints box

echo "   -- FIXWED
Bobby Portis gett JMP ball as plaer 3 missed"
./w.sh -s web -t IND -d 2024-04-26  -m plot raw stints box

echo " FIXED
This is a D'Angelo Russel ASSIST between a SUB OUT and SUB IN in the same period
It works if we change the app so the event between valid in period IN-OUTs are ignored
Unknow what this migh break"
./w.sh -s web -t LAL -d 2024-04-12  -m plot raw stints box

echo " FIXED
Double Technical unique name"
./w.sh -s web -t MIA -d 2024-02-23  -m plot raw stints box

ls -l llm/llm_training_data | wc -l

grep -r 'ERROR' .wwmdd/logs/* 