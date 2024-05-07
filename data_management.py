
import sqlite3
import pandas as pd

# NOT USED FOR NOW
def loadFromCSV():
    
    import glob
    import os

    pth = os.path.join("./csv", "*.csv")  # Replace with your directory path
    all_files = glob.glob(pth)

    dfFromCSV = {}
    for filename in all_files:
        print(filename)
        df = pd.read_csv(filename, index_col=None, header=0)
        print(df.shape)
        __fn = os.path.split(filename)[1].split('.')[0]
        dfFromCSV[__fn] = df

gamesByTeam = {}    # reorganized game data is in gamesByTeam

def loadNBA_data(_filename_):

    _dfs = {}            # has everthing that was in db as dict of DateFrame by column name

    db_con = sqlite3.connect(_filename_)
    db_cursor = db_con.cursor()

    db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = db_cursor.fetchall()

    DoNotUseTableNames = ['play_by_play']
    table_names = [k[0] for k in table_names if k[0] not in DoNotUseTableNames]
 
    for i, table_name in enumerate(table_names):

        query = f"SELECT * FROM {table_name}"
        chunk_size = 100000
        count = 0
        chunks = []
        
        indexCol = None

        for chunk in pd.read_sql_query(query, db_con, chunksize=chunk_size,index_col= indexCol):
            chunks.append(chunk)
            count += chunk_size

        _dfs[table_name] = pd.concat(chunks)

    # strip leading digit from season, its signifies pre, post and regular season
    _dfs['game']['season_id'] = _dfs['game']['season_id'].apply(lambda x:x[1:])
    #place to save play by play dataframe
    _dfs['game']['play_by_play'] = [[pd.DataFrame([])]] * len(_dfs['game'])

    return _dfs,db_con      
 