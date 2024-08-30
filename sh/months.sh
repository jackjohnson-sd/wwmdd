rm -f llm/llm_training_data/* 
rm -f .wwmdd/logs/* 
rm -f .wwmdd/.csvs/* 

./w.sh -s web -t ALL -d 2023-10-15 2023-10-31 -m csv raw stints box
./w.sh -s web -t ALL -d 2023-11-01 2023-11-30 -m csv raw stints box
./w.sh -s web -t ALL -d 2023-12-01 2023-12-31 -m csv raw stints box
./w.sh -s web -t ALL -d 2024-01-01 2024-01-31 -m csv raw stints box
./w.sh -s web -t ALL -d 2024-02-01 2024-02-28 -m csv raw stints box
./w.sh -s web -t ALL -d 2024-03-01 2024-03-31 -m csv raw stints box
./w.sh -s web -t ALL -d 2024-04-01 2024-04-30 -m csv raw stints box
./w.sh -s web -t ALL -d 2024-05-01 2024-05-30 -m csv raw stints box


ls -l llm/llm_training_data | wc -l


grep -r 'ERROR' .wwmdd/logs/* 