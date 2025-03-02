import time

from bigquery.client import BigQueryClient
from crunchbase.client import CrunchbaseClient
from linkedin_request.client import LinkedinClient
from openai_request.client import OpenAIClient
from tasks import (
    analysis,
    crunchbase,
    linkedin,
    validation,
    mapping
)

from config import Config

from logger import Logger as logger


if __name__ == "__main__":

    _s_time = time.time()
    # Step 1: Get Arguments and Environment Variables to set Config

    CONFIG = Config()
    # Step 2: Create Clients depending on Config

    logger.info("Create Clients")
    # create Bigquery Client if needed
    if CONFIG.BIGQUERY_NEEDED:
        logger.log("Creating BigQuery Client")
        BQClient = BigQueryClient(
            project_id=CONFIG.PROJECT_ID,
            dataset_name=CONFIG.DATASET_ID
        )
    else:
        logger.log("BigQuery is not needed")
        BQClient = None

    # create Crunchbase Client if needed
    if CONFIG.CRUNBASE_NEEDED:
        logger.log("Creating Crunchbase Client")
        CRUNCHBASE = CrunchbaseClient(
            CONFIG.CRUNCHBASE_API_KEY,
            CONFIG.CRUNCHBASE_BASE_URL
            # CONFIG.CRUNCHBASE_BASE_API
        )
    else:
        logger.log("Crunchbase is not needed")
        CRUNCHBASE = None
    
    # create Linkedin Client if needed
    if CONFIG.LINKEDIN_NEEDED:
        logger.log("Creating Linkedin Client")
        LINKEDIN = LinkedinClient(
            CONFIG.LINKEDIN_ACCOUNT,
            CONFIG.LINKEDIN_PWD
        )
    else:
        logger.log("Linkedin is not needed")
        LINKEDIN = None

    # create Open AI Client if needed
    if CONFIG.OPENAI_NEEDED:
        logger.log("Creating Open AI Client")
        OPENAI = OpenAIClient(
            CONFIG.OPENAI_API_KEY
        )
    else:
        logger.log("Open AI is not needed")
        OPENAI = None
    # Step 3: BigQuery check Dataset (if not exists, create it)

    if CONFIG.BIGQUERY_NEEDED and not BQClient.dataset_exists():
        logger.warning("Dataset does not exist. Creating it now...")
        BQClient.create_dataset()

    # Step 4: do the single jobs to get data and upload

    if CONFIG.DO_DOWNLOAD:
        logger.info("Start Download Job")
        # run job
        crunchbase.run_job(CRUNCHBASE, BQClient, CONFIG.DO_UPLOAD)
        logger.success("Finished Download Job")

    # without upload to BQ
    if CONFIG.DO_LINKEDIN:
        logger.info("start linkedin job")
        # run job
        linkedin.run_job(LINKEDIN)
        logger.success("finished linkedin Job")
    
    # without upload to BQ
    if CONFIG.DO_ANALYSIS:
        logger.info("Start analysis Job")
        analysis.run_job()
        logger.info("Finished analysis Job")

    # without upload to BQ
    if CONFIG.DO_MAPPING:
        logger.info("Start mapping Job")
        logger.log("Generating map based on categorized data")
        output_csv = "reporting/categorized_crunchbase_with_address.csv"
        mapping.generate_germany_map(output_csv, "img/unvalidated/germany_re_strategy_map.png")
        logger.log("Done with unvalidated data mapping")
        logger.log("Generating map based on validated categorized data")
        categorized_csv = 'reporting/categorized_crunchbase_with_openai_responses.csv'
        # Call the function to generate maps for the validation results
        mapping.generate_germany_map_with_validation_disagree(categorized_csv, "img/validated/disagree/germany_re_strategy_map_validated_disagree.png")
        mapping.generate_germany_map_with_validation_agree(categorized_csv, "img/validated/agree/germany_re_strategy_map_validated_agree.png")
        logger.info("Finished mapping Job")

    # without upload to BQ
    if CONFIG.DO_OPENAI:
        logger.info("Start validation job")
        # run job
        validation.run_job(OPENAI, CONFIG.DO_OPENAI)
        logger.success("Finished validation job")
    # Programm finished

    _e_time = time.time()
    logger.log(f"Programm finished in {_e_time - _s_time} seconds")
