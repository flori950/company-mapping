from datetime import datetime
import json
import pandas as pd
from bigquery.client import BigQueryClient
from bigquery.job_config import CRUNCHBASE_CONFIG
from bigquery.schemes.crunchbase_schema import CRUNCHBASE_SCHEMA

from crunchbase.client import CrunchbaseClient
from crunchbase.crunchbase_query import CRUNCHBASE_QUERY
from logger import Logger as logger
from helpers.decorators import calc_time
from config import Config
from crunchbase.crunchbase_column_rename import COLUMN_NAME_MAPPING
from tqdm import tqdm

def run_job(client: CrunchbaseClient, bqclient: BigQueryClient, upload=False):
    
    # get data from Crunchbase
    logger.log("Fetching data from Crunchbase")
    df = get_data(client)
    logger.debug("Saving data as csv")
    df.to_csv(f"reporting/crunchbase.csv", index=False)
    
    # write data to BigQuery
    if upload:
        logger.log("Uploading data to BigQuery")
        upload_df(bqclient, df)

    # delete dataframes to free up memory
    del df

def extract_location_data(row):
    try:
        if isinstance(row, list):
            location_data = row
        else:
            location_data = json.loads(row.replace("'", "\""))
        city = next((item['value'] for item in location_data if item["location_type"] == "city"), None)
        region = next((item['value'] for item in location_data if item["location_type"] == "region"), None)
        country = next((item['value'] for item in location_data if item["location_type"] == "country"), None)
        continent = next((item['value'] for item in location_data if item["location_type"] == "continent"), None)
        return pd.Series([city, region, country, continent], index=['City', 'Region', 'Country', 'Continent'])
    except Exception as e:
        logger.error(f"Error in extracting location data: {e}")
        return pd.Series([None, None, None, None], index=['City', 'Region', 'Country', 'Continent'])


@calc_time
def get_data(client: CrunchbaseClient) -> pd.DataFrame:
    """
    Get data from CrunchbaseClient with pagination using after_id and save it to a CSV file.

    Args:
        client (CrunchbaseClient): The CrunchbaseClient object.

    Returns:
        pd.DataFrame: The extracted data as a pandas DataFrame.
    """
    raw = pd.DataFrame()
    query = CRUNCHBASE_QUERY  

    try:
        comp_count = client.company_count(query)
        logger.info(f"The number of companies found: {comp_count}")
        data_acq = 0
        with tqdm(total=comp_count) as pbar: 
            while data_acq < comp_count:
                if data_acq != 0:
                    last_uuid = raw.uuid.iloc[-1]
                    response = client.get_data(query, after_id=last_uuid)
                    normalized_raw = pd.json_normalize(response['entities'])
                    raw = pd.concat([raw, normalized_raw], ignore_index=True)
                    data_acq = len(raw.uuid)
                else:
                    response = client.get_data(query)
                    normalized_raw = pd.json_normalize(response['entities'])
                    raw = pd.concat([raw, normalized_raw], ignore_index=True)
                    data_acq = len(raw.uuid)
                pbar.update(len(normalized_raw))
        # Rename columns based on the mapping
        raw.rename(columns=COLUMN_NAME_MAPPING, inplace=True)

        # Split properties.location_identifiers into multiple columns
        raw[['City', 'Region', 'Country', 'Continent']] = raw['Location_Identifiers'].apply(extract_location_data)

        # Drop the original Location_Identifiers column
        #raw.drop(columns=['Location_Identifiers'], inplace=True)

        # Add a column for partition date
        raw['dwh_partitiondate'] = datetime.now()


        return raw
    except Exception as e:
        logger.error(f"Error in getting data from Crunchbase: {e}")

@calc_time
def upload_df(client: BigQueryClient, dataframe: pd.DataFrame):
    try:
        tablename = "Crunchbasedownload"
        table_id = client.dataset_refstring + "." + tablename
        if not client.table_exists(tablename):
            client.create_table(tablename, CRUNCHBASE_SCHEMA)
            upload_job = client.load_table_from_dataframe(dataframe, tablename, CRUNCHBASE_CONFIG)
            try:
                upload_job.result()
            except Exception as e:
                handle_upload_error(e, upload_job)
            logger.info("Upload complete")            
        else:
            if client.check_is_no_duplicate(table_id, dataframe):
                upload_job = client.load_table_from_dataframe(dataframe, tablename, CRUNCHBASE_CONFIG)
                try:
                    upload_job.result()
                except Exception as e:
                    handle_upload_error(e, upload_job)
                logger.info("Upload complete")
            else:
                logger.info("No upload necessary")
    except Exception as e:
        logger.error(f"Error: {e}")



def handle_upload_error(error, job):
    logger.error(f"Error while waiting for job result: {error}")
    job_errors = getattr(job, 'errors', None)
    
    if job_errors:
        logger.error(f"Job errors: {job_errors}")
