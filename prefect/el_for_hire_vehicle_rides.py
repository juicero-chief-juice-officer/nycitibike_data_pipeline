# from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks  import task_input_hash
from random import randint
from datetime import timedelta, datetime

"""
Simple flow to get taxi and livery cab (aka for-hire vehicles, fhv) trip data into cloud storage. 
"""

print('abc123')
@task
def write_gcs(df_in: pd.DataFrame, gcs_path, gcs_block) -> None:
    """Upload dataframe to GCS as parquet"""
    gcs_block.upload_from_dataframe(
            df=df_in
        ,   to_path=gcs_path
        ,   serialization_format = 'parquet_gzip'
        )

@flow()
def el_web_to_gcs_trips(year:int, month:int, color:str, gcs_block) -> None:
    """Main ETL function"""
    dataset_file = f"{color}_tripdata_{year}-{month:02}.parquet"
    dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset_file}"

    gcs_path = f"aux_data/for_hire_vehicle_trips/{color}/{year}/{month:02}/{dataset_file}"
    
    #download to df
    print(f'read from {dataset_url}')
    df = pd.read_parquet(dataset_url)
    
    #write df directly to gcs
    write_gcs(df,gcs_path,gcs_block)

    #delete from memory
    del df

@flow()
def el_parent_flow_trips(      
                    # years: list[int] #= [datetime.now().year]
                    # , months: list[int] #= [datetime.now().month-1]
                    # , colors: list[str] #= ['yellow','green']
                    years = list(range(2013,2024)),
                    months = list(range(1,13)),
                    colors = ['yellow','green','fhv']                    
                    ):

    gcs_block = GcsBucket.load("sbh-nycitibike-pipeline-p-pfct--blk-gcs-dlb")
    for mo in months:
        for yr in years:
            for clr in colors:
                try:
                    el_web_to_gcs_trips(yr,mo,clr,gcs_block)
                except Exception as e:
                    print(e)

# is_runtype_retro = True

# if is_runtype_retro:
    # years = list(range(2013,2024))
    # months = list(range(1,13))
    # colors = ['yellow','green','fhv']

# else:
#     years = [datetime.now().year]
#     months = [datetime.now().month-1]
#     colors = ['yellow','green','fhv']
# print(years)
# print(months)
# print(colors)

if __name__ == '__main__':
    el_parent_flow_trips()
    # years = list(range(2013,2024))
    # months = list(range(1,13))
    # colors = ['yellow','green','fhv']
    # print(years)
    # print(months)
    # print(colors)
    # el_parent_flow_trips(years, months, colors)