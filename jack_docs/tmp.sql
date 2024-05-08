SELECT
  eventmsgtype
  , score
  , player1_name
  , player2_name
  , player3_name
  , homedescription
  , visitordescription
FROM play_by_play
WHERE game_id == '0022200562'
  AND eventmsgtype == 2