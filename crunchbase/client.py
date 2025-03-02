import requests

from helpers.decorators import retry
from logger import Logger as logger


# create own AccessError
class AccessError(Exception):
    pass


class CrunchbaseClient():
    """ Crunchbase Client """
    max_retries = 5
    retry_delay = 10

    def __init__(self, api_key, base_url):
        """
        Initializes the Crunchbase Client

        Args:
            api_key (str): The API key for crunchbase.
            base_url (str): The Crunchbase base url.
        """
        try:
            self.API_KEY = api_key
            self.QUERY_URL = base_url + "/searches/organizations"
       # Test API connectivity during initialization
            if not self.test_api_connectivity():
                raise ConnectionError("Crunchbase API is not reachable")
        except Exception as e:
            logger.error(f"Problem with Crunchbase credentials: {e}")

    def test_api_connectivity(self):
        """
        Test API connectivity by making a test request to the Crunchbase API.
        """
        try:
            headers = {
                "accept": "application/json",
                "X-cb-user-key": self.API_KEY,
                "Content-Type": "application/json"
            }

            # Define payload for the test request
            payload = {
                "field_ids": [
                    "name" # just a test with company names
                ],
                "limit": 1  # Limit for the test request
            }

            # Make a test request to the API with the payload
            response = requests.post(self.QUERY_URL, json=payload, headers=headers)
            # Check if the response is successful
            if response.status_code == 200:
                logger.success("Crunchbase API is reachable")
                return True
            else:
                logger.error("Crunchbase API is not reachable")
                return False
        except Exception as e:
            logger.error(f"Error testing API connectivity: {e}")
            return False

    @retry(max_retries, retry_delay)
    def company_count(self, query: dict) -> int:
        """
        Get the total count of companies matching the given query.

        Args:
            query (dict): The query to be used for counting companies.

        Returns:
            int: The total count of companies matching the query.
        """
        try:
            headers = {
                "accept": "application/json",
                "X-cb-user-key": self.API_KEY,
                "Content-Type": "application/json"
            }

            # Send a POST request to get the count of companies
            response = requests.post(self.QUERY_URL, params={"user_key": self.API_KEY}, json=query, headers=headers)
            # Check if the response is successful
            if response.status_code == 200:
                result = response.json()
                total_companies = result["count"]
                return total_companies
            else:
                logger.error("Error in getting company count: Unexpected status code")
                return 0
        except Exception as e:
            logger.error(f"Error in getting company count: {e}")
            return 0  # Return 0 in case of any error

    @retry(max_retries, retry_delay)
    def get_data(self, query: dict, after_id: str = None, limit: int = 1000):
        """
        Get data from Crunchbase

        Args:
            query (dict): The query (only columns, order_by and filters)
            after_id (str, optional): The UUID to start fetching data after. Defaults to None.
            limit (int, optional): The limit. Defaults to 1000.

        Returns:
            dict: The response.
        """
        try:
            headers = {
                "accept": "application/json",
                "X-cb-user-key": self.API_KEY,
                "Content-Type": "application/json"
            }

            dynamic_data = {
                "limit": limit,
            }

            # add query and after_id to data
            data = {**query, **dynamic_data}
            if after_id:
                data["after_id"] = after_id

            response = requests.post(
                self.QUERY_URL, json=data, headers=headers)
            # Handle specific error codes
            if response.status_code == 401:
                logger.error("Invalid Crunchbase credentials")
                raise AccessError("Invalid credentials")
            elif response.status_code == 400:
                error_message = response.json().get("error", {}).get("message")
                error_code = response.json().get("error", {}).get("code")
                if error_code == "MD103":
                    logger.error("Multiple pagination parameters specified")
                elif error_code == "MD403":
                    logger.error("Request is asking for more than 1000 results")
                elif error_code == "CS102":
                    logger.error("Invalid entity collection id specified")
                elif error_code == "CS103":
                    logger.error("Invalid JSON body or search request")
                elif error_code == "CS105":
                    logger.error("Invalid URI")
                elif error_code == "CS106":
                    logger.error("Query timeout exceeded")
                elif error_code == "CS109":
                    logger.error("Unknown or invalid operator ID")
                elif error_code == "CS111":
                    logger.error("Invalid specified values or format")
                elif error_code == "CS112":
                    logger.error("Field ID does not exist")
                elif error_code.startswith("CS15"):
                    logger.error("Too many concurrent requests")
                elif error_code == "CS404":
                    logger.error("Requested resource not found")
            elif response.status_code == 404:
                error_code = response.json().get("error", {}).get("code")
                if error_code == "CS102":
                    logger.error("Invalid entity collection id specified")
                elif error_code == "CS112":
                    logger.error("Field ID does not exist")
            elif response.status_code == 429:
                logger.error("Too many concurrent requests")
            elif response.status_code == 502:
                logger.error("Service is unavailable during an outage")
            elif response.status_code == 409:
                logger.error("Too many requests, user is rate-limited")
            elif response.status_code == 500:
                logger.error("Internal server error")

            # Raise an exception for non-successful status codes
            response.raise_for_status()

            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            raise
        except Exception as e:
            logger.error(f"Error in get data from Crunchbase: {e}")
            raise
    