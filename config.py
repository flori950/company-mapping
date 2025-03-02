import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

from logger import (
    Logger as logger
)

class Config:
    """
    Holds all Config variables and set them by environment variables or arguments
    """
    DEV_MODE = False
    STAGE = "unknown"
    CLIENT = None
    PROJECT_ID = None
    DATASET_ID = None
    ENGINE = None
    CRUNCHBASE_BASE_API = None
    CRUNCHBASE_BASE_URL = None
    CRUNCHBASE_API_KEY = None
    OPENAI_API_KEY = None

    # for future implementations
    LINKEDIN_ACCOUNT = None
    LINKEDIN_PWD = None

    # task config
    DO_UPLOAD = False
    DO_LINKEDIN = False
    DO_OPENAI = False
    DO_DOWNLOAD = False
    DO_ANALYSIS = False
    DO_MAPPING = False

    # client config
    LINKEDIN_NEEDED = False
    CRUNBASE_NEEDED = False
    OPENAI_NEEDED = False
    BIGQUERY_NEEDED = False

    def __init__(self):
        """ Init Config """
        ARGS = self.parse_arguments()
        self.load_environment()
        try:
            self.set_general_settings(ARGS)
            if Config.DEV_MODE:
                # set debug settings
                self.set_development_settings()
            else:
                # set production settings
                self.set_production_settings(ARGS)
            # set preprocessing settings
            self.set_preprocessing_settings()
            logger.success("Config set")
        except Exception as e:
            logger.error(f"Config creation error: {e}")
            exit(1)

    def parse_arguments(self):
        """ Parse arguments """
        parser = argparse.ArgumentParser(description='Program for downloading data from Crunchbase.')
        parser.add_argument('--download_flag', action='store_true', help='Flag to enable crunchbase data processing.')
        parser.add_argument('--analysis_flag', action='store_true', help='Flag to enable analysis from csv')
        parser.add_argument('--mapping_flag', action='store_true', help='Flag to enable map analyzed companies from csv')
        parser.add_argument('--upload_flag', action='store_true', help='Flag to enable upload data to bigquery processing.')
        parser.add_argument('--linkedin_flag', action='store_true', help='Flag to enable linkedin data processing.')
        parser.add_argument('--validation_flag', action='store_true', help='Flag to enable validation of categorisation with AI.')
        parser.add_argument('--project_id', help='BigQuery project ID to ignore the environment variable')
        parser.add_argument('--dataset_id', help='BigQuery dataset ID to ignore the environment variable')
        parser.add_argument('--linkedin_account', help='Linkedin account for accessing the API')
        parser.add_argument('--linkedin_pwd', help='Linkedin account password for accessing the API')
        parser.add_argument('--crunchbase_api_key', help='If it should be started via cronejob the Crunchbase API could be added here')
        parser.add_argument('--openai_api_key', help='If it should be started via cronejob the OpenAI API could be added here')
        return parser.parse_args()

    def load_environment(self):
        """
        Load environment variables from .env file
        """
        # check if local env_base exists
        DOTENV_PATH = Path("env_base.env")
        # load it
        if DOTENV_PATH.exists():
            load_dotenv(dotenv_path=DOTENV_PATH)
            logger.info("Environment loaded from env_base.env")
            # debug mode could only set on local machine
            Config.DEV_MODE = os.getenv("MODE") == "DEV"
        else:
            load_dotenv()
            logger.info("Environment loaded from container")

    def set_general_settings(self, args):
        """
        Set general settings

        Args:
            args (dict): Arguments
        """
        if args.analysis_flag:
            Config.DO_ANALYSIS = args.analysis_flag
                
        if args.mapping_flag:
            Config.DO_MAPPING = args.mapping_flag

        if args.download_flag:
            Config.DO_DOWNLOAD = args.download_flag

        if args.linkedin_flag:
            Config.DO_LINKEDIN = args.linkedin_flag
        
        if args.validation_flag:
            Config.DO_OPENAI = args.validation_flag

        if args.project_id:
            Config.PROJECT_ID = args.project_id
        else:
            Config.PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
        if args.dataset_id:
            Config.DATASET_ID = args.dataset_id
        else:
            Config.DATASET_ID = os.getenv("GOOGLE_DATASET_ID")
        if args.linkedin_account:
            Config.LINKEDIN_ACCOUNT = args.linkedin_account
        else:
            Config.LINKEDIN_ACCOUNT = os.getenv("LINKEDIN_ACCOUNT")
        if args.linkedin_pwd:
            Config.LINKEDIN_PWD = args.linkedin_pwd
        else:
            Config.LINKEDIN_PWD = os.getenv("LINKEDIN_PWD")
        if args.crunchbase_api_key:
            Config.CRUNCHBASE_API_KEY = args.crunchbase_api_key
        else:
            Config.CRUNCHBASE_API_KEY = os.getenv("CRUNCHBASE_API_KEY")
        if args.openai_api_key:
            Config.OPENAI_API_KEY = args.openai_api_key
        else:
            Config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        # insert openai credentials

        Config.STAGE = os.getenv("STAGE")

        # set Crunchbase Config
        Config.CRUNCHBASE_BASE_API = os.getenv("CRUNCHBASE_BASE_API")
        Config.CRUNCHBASE_BASE_URL = os.getenv("CRUNCHBASE_BASE_URL") 

    def set_development_settings(self):
        """
        Set development settings
        Theese settings are only for development to prevent
        upload to BigQuery 
        """
        logger.verbose = True
        logger.debug("Development Mode is enabled")
        # changes for development mode
        Config.DO_UPLOAD = False
        

    def set_production_settings(self, args):
        """
        Set production settings
        Theese settings are only for production
        and never runs in development mode

        Args:
            args (dict): Arguments
        """
        Config.DO_UPLOAD = args.upload_flag
        Config.DO_DOWNLOAD = args.download_flag
        Config.DO_LINKEDIN = args.linkedin_flag
        Config.DO_ANALYSIS = args.analysis_flag
        Config.DO_MAPPING = args.mapping_flag
        Config.DO_OPENAI = args.validation_flag

    def set_preprocessing_settings(self):
        """
        Set preprocessing settings
        Theese settings are set after all other settings
        """

        # Crunchbase is needed if this tasks are enabled
        Config.CRUNBASE_NEEDED = any([
            Config.DO_DOWNLOAD
        ])
        # Download from Crunchbase is needed if Linkedin processing tasks are enabled
        Config.LINKEDIN_NEEDED = any([
            Config.DO_LINKEDIN
        ])
        # Crunchbase is needed if Open AI processing tasks are enabled
        Config.OPENAI_NEEDED = any([
            Config.DO_OPENAI
        ])
        # BigQuery is needed if this tasks are enabled
        Config.BIGQUERY_NEEDED = any([
            Config.DO_UPLOAD
        ])
