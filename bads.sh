rm -f llm/llm_training_data/* 
rm -f .wwmdd/logs/* 
rm -f .wwmdd/.csvs/* 

./w.sh -s web -t CHI -d 2023-12-11  -m plot raw stints box
./w.sh -s web -t IND -d 2024-04-26  -m plot raw stints box
./w.sh -s web -t LAL -d 2024-04-12  -m plot raw stints box
./w.sh -s web -t MIA -d 2024-02-23  -m plot raw stints box
./w.sh -s web -t MIN -d 2024-01-10  -m plot raw stints box
./w.sh -s web -t PHI -d 2024-01-29  -m plot raw stints box
./w.sh -s web -t PHX -d 2023-11-08  -m plot raw stints box
./w.sh -s web -t PHX -d 2024-03-05  -m plot raw stints box
./w.sh -s web -t POR -d 2024-03-02  -m plot raw stints box
./w.sh -s web -t SAS -d 2024-01-20  -m plot raw stints box


ls -l llm/llm_training_data | wc -l


grep -r 'ERROR' .wwmdd/logs/* 