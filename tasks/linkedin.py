import time
import random
import pandas as pd

from linkedin_request.client import LinkedinClient
from logger import Logger as logger

# TODO: Upload to Bigquery

def run_job(linkedinclient: LinkedinClient):
    
    logger.log("Loading data from CSV")
    df = pd.read_csv("reporting/crunchbase.csv")
 
    # Scrape LinkedIn company data for each company name in the DataFrame
    linkedin_data = []
    for company_name in df['Name']:
        logger.log(f"Scraping LinkedIn data for company: {company_name}")
        # Make API call to LinkedIn
        company_data = LinkedinClient.get_company_info(linkedinclient, company_name)
        linkedin_data.append(company_data)
        # Wait for 10-20 seconds before making the next API call
        time.sleep(random.uniform(10, 20))

    # Add LinkedIn data to DataFrame
    df['linkedin_data'] = linkedin_data

    # save dataframe as csv if DEV_MODE is True
    # if Config.DEV_MODE:

    #it will be always saved in reportings for the linkedin search
    logger.debug("Saving data as csv")
    df.to_csv(f"reporting/linkedin.csv", index=False)

    # delete dataframes to free up memory
    del df
