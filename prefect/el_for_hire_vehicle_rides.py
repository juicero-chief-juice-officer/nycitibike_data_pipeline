from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from random import randint
from prefect.tasks  import task_input_hash
from datetime import timedelta, datetime

"""
Simple flow to get taxi and livery cab (aka for-hire vehicles, fhv) trip data into cloud storage. 
"""

print('a')
@task
def write_gcs(df_in: pd.DataFrame, gcs_path: Path) -> None:
    """Upload dataframe to GCS as parquet"""
    gcs_block = GcsBucket.load("sbh-nycitibike-pipeline-p-pfct--blk-gcs-dlb")
    gcs_block.upload_from_dataframe(
            df=df
        ,   to_path=gcs_path
        ,   serialization_format = 'parquet_gzip'
        )

@flow()
def el_web_to_gcs_trips(year:int, month:int, color:str) -> None:
    """Main ETL function"""
    dataset_file = f"{color}_tripdata_{year}-{month:02}.parquet"
    dataset_url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{dataset_file}"
    
    gcs_path = f"aux_data/for_hire_vehicle_trips/{color}/{year}/{month:02}/{dataset_file}"
    
    #download to df
    print(f'read from {dataset_url}')
    df = pd.read_parquet(dataset_url)
    print(df.columns)
    
    #write df directly to gcs
    write_gcs(df,gcs_path)
    del df

@flow()
def el_parent_flow_trips(      
                    years: list[int] = [datetime.now().year]
                    , months: list[int] = [datetime.now().month-1]
                    , colors: list[str] = ['yellow','green']
                    ):
    try:
        for mo in months:
            for yr in years:
                for clr in colors:
                    el_web_to_gcs_trips(yr,mo,clr)
    except Exception as e:
        print(e)
if __name__ == '__main__':
    print('asdljkhfalksdhflaksjd')
    years = list(range(2013,2024))
    months = list(range(1,13))
    colors = ['yellow','green']
    el_parent_flow_trips(years, months, colors)

