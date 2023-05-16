FROM prefecthq/prefect:2.7.7-python3.9

copy docker-requirements.txt .

RUN pip install -r docker-requirements.txt --trusted-host pypi.python.org