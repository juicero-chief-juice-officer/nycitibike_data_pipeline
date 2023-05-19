from datetime import datetime
import re
import os
import pandas as pd
from pathlib import Path
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
import zipfile
from urllib.request import urlopen
from urllib.error import HTTPError
import shutil
import json 

@task(retries=0)
def fetch_data(url: str, filename: str) -> pd.DataFrame: # returns None if no file available
    """Pull data from web; return dataframe"""
    # dataset_out_file_name = 'data/' + filename + '.csv'
    found_file: bool
    tmp_folder = 'data/tmp'

    # Make new directory if none exists:
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)

    # We try two different file extensions, as they have changed in the past.
    try:
        file_extension = '.csv.zip'
        zip_file_name = f"{tmp_folder}/{filename}{file_extension}"
        full_url = url + file_extension
        print(f'Attempting to access file: {full_url}')
        with urlopen(full_url) as response:
            print(f'Accessed file: {full_url}')
            with open(zip_file_name, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        found_file = True
    except:
        try: #try alternative file extension
            file_extension = '.zip'
            zip_file_name = f"{tmp_folder}/{filename}{file_extension}"
            full_url = url + file_extension
            print(f'[Attempt 2] Attempting to access file: {full_url}')
            print(urlopen(full_url).getcode())
            with urlopen(full_url) as response, open(zip_file_name, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            found_file = True

        except Exception as ee:
            print("FOUND FILE?")
            print(found_file)
            if type(ee) == HTTPError:
                found_file = False
            else:
                raise
            
    if found_file:
        zf = zipfile.ZipFile(zip_file_name,'r')
        df = pd.read_csv(zf.open(zf.namelist()[0]),compression='infer',dtype={"started_at":str,"ended_at":str,"start_station_name":str,"start_station_id":float,"end_station_name":str},parse_dates=parspd.to_datetime)
        return df
    else: 
        return None
    
    

@task
def clean_dfs(df) -> pd.DataFrame:
    is_old_col_format = 'Gender' in df.columns

    old_format_rename = {
        'Trip Duration':'trip_duration',
        'Start Time':'started_at',
        'Stop Time':'ended_at',
        'Start Station ID':'start_station_id',
        'Start Station Name':'start_station_name',
        'Start Station Latitude':'start_lat',
        'Start Station Longitude':'start_lng',
        'End Station ID':'end_station_id',
        'End Station Name':'end_station_name',
        'End Station Latitude':'end_lat',
        'End Station Longitude':'end_lng',
        'Bike ID':'bike_id',
        'User Type':'is_member',
        'Birth Year':'birth_year',
        'Gender':'gender',
        'member_casual':'is_member',
        'rideable_type': 'is_classic_bike'
    }

    col_dtypes = {
        'start_station_name':'str',
        'start_station_id':'str',
        'end_station_name':'str',
        'end_station_id':'str',
        'start_lat':'float',
        'start_lng':'float',
        'end_lat':'float',
        'end_lng':'float',
        # new cols
        'ride_id':'str',
        # old cols
        'trip_duration':'int',
        'bike_id':'str',
        'birth_year':'int',
        'gender':'int'

    }

    df.rename(columns=old_format_rename,inplace=True,errors='ignore')

    df['started_at'] = pd.to_datetime(df['started_at'])
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    
    if is_old_col_format:
        df['ride_id'] = df['started_at'].astype(str) + '-' + df['start_station_id'].astype(str) + '-' + df['bike_id'].astype(str)
        df['is_member'] = df['is_member'] == 'Subscriber'
        df['rideable_type'] = None
    else:
        df[['gender','birth_year']] = None
        df['trip_duration'] = (df['ended_at'] - df['started_at']).dt.total_seconds()
        df['is_member'] =   df['is_member'] == 'member'
        df['bike_id'] = None
    df = df.astype(col_dtypes,errors='ignore')

    return df

# @task
# def write_df_as_parquet_locally(df:pd.DataFrame , file: str) -> Path:
#     """Write dataframe as parquet locally"""
#     path = Path(f"../data/{file}")
#     df.to_parquet(path,compression='gzip')
#     return path

@flow
def write_parquet_to_gcs(df, file_name, year, month) -> None: #path: Path, 
    """Send df to GCS as parquet file"""
    gcs_block = GcsBucket.load("sbh-nycitibike-pipeline-p-pfct--blk-gcs-dlb") #name of GCS Bucket Block from Prefect; there is a typo in mine which I left (--).
    gcs_path = f"data/{year}/{month:02}/{file_name}.parquet"
    gcs_block.upload_from_dataframe(df,to_path = gcs_path,serialization_format = 'parquet_gzip')

@flow
def el_extract(year:int, month:int) -> None:
    """Main EL Function"""

    dataset_file_name = f"{year}{month:02}-citibike-tripdata"
    dataset_url = f"https://s3.amazonaws.com/tripdata/{dataset_file_name}"

    df = fetch_data(dataset_url, dataset_file_name)
    if df is None:
        print('No File was Found during fetch')
    else: 
        df = clean_dfs(df)
        write_parquet_to_gcs(df,dataset_file_name,year,month) #local_path, 

# While prefect does allow passing variables and parameters, it's easier to just run this for the last month based on datetime
# For the initial run, we could use list comprehension as follows: 
#       # import sys
#       # years = sys.argv[1].split(',') # Alternative years = list(range(2013,2023))
#       # months = sys.argv[2].split(',') # Alternative: months = list(range(1,13))
        # for yr in years:
        #   for mo in months:
        #       el_extract(year = yr, month = mo)

@flow 
def el_parent_flow():
    yr = datetime.today().year
    mo = datetime.today().month - 1
    el_extract(year = yr, month = mo)

if __name__ == '__main__':
     el_parent_flow()
