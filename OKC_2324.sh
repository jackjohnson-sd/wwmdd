echo "----------- GETTING DATA FROM WEB ---------"
sh wwmdd.sh --web OKC --start 2023-10-20 --stop 2024-06-15 --noplot ON
echo "----------- Checking files from WEB -------"
sh wwmdd.sh --show llm_training_data --noplot ON 
