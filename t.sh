./w.sh -s web -t OKC -d 2023-01-30 -m plot csv stints box img -p stints  -f tests/bads/test_data/web -w 2 -json tests/bads/web_save.json
./w.sh -s csv -f tests/bads/test_data/web/_W_DBG_OKCvGSW20230130.csv -m plot stints box img -p boxscore stints -w 1 -json tests/bads/csv_save.json
exit




./w.sh -s web -t OKC -d 2023-01-30 -m plot stints csv box img -p stints -f tests/bads/test_data -json tests/bads/debug_on.json -w 2
./w.sh -s csv -f tests/bads/test_data/web/DBG_OKCvGSW20230130.csv -m plot box -p stints -w 2
exit
./w.sh -s web -t OKC -d 2023-01-30 -m plot stints csv box img -p boxscore stints -f tests/bads/test_data -w 10