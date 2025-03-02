from linkedin_api import Linkedin
from logger import Logger as logger
from helpers.decorators import retry

class AccessError(Exception):
    pass

class LinkedinClient():
    """Linkedin client."""
    max_retries = 5
    retry_delay = 10

    def __init__(self, account, password):
        """
        Initialize access to LinkedIn.
        
        Parameters:
            account (str): LinkedIn account username.
            password (str): LinkedIn account password.
        """
        logger.info("LinkedIn Login will be initialized...")
        self.ACCOUNT = account
        self.PWD = password
        try:
            self.driver = Linkedin(self.ACCOUNT, self.PWD)
        except Exception as e:
            logger.error(f"Error testing Linkedin API connectivity: {e}")
            return False
        
    @retry(max_retries, retry_delay)
    def get_company_info(self, company_name):
        """
        Get information about a company on LinkedIn.
        
        Parameters:
            company_name (str): Name of the company.
        
        Returns:
            dict: Information about the company.
        """
        try:
            logger.info(f"Fetching information for company: {company_name}")
            company_info = self.driver.get_company(company_name)
            if company_info:
                logger.info(f"Received information for company: {company_name}")
                # Log detailed company information
                for key, value in company_info.items():
                    logger.debug(f"{key}: {value}")
            else:
                logger.warning(f"No information found for company: {company_name}")
            return company_info
        except Exception as e:
            logger.error(f"Error fetching company information: {e}")
            return None
