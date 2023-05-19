FROM prefecthq/prefect:2.7.7-python3.9

COPY docker-requirements.txt .
COPY prefect/el_from_citibike_to_gcs.py prefect/el_from_citibike_to_gcs.py

RUN pip install -r docker-requirements.txt --trusted-host pypi.python.org