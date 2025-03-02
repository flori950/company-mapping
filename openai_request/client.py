import requests
import openai
from helpers.decorators import retry
from logger import Logger as logger

class AccessError(Exception):
    pass

class OpenAIClient():
    """ Open AI Client """
    max_retries = 5
    retry_delay = 10

    def __init__(self, api_key):
        """
        Initializes the OpenAI Client.

        Args:
            OPENAI_API_KEY (str): The API key for OpenAI.
        """
        try:
            self.OPENAI_API_KEY = api_key
            openai.api_key = self.OPENAI_API_KEY

            # Test API connectivity during initialization
            if not self.test_api_connectivity():
                raise ConnectionError("OpenAI API is not reachable")
        except Exception as e:
            logger.error(f"Problem with OpenAI credentials: {e}")
            raise e
        
    @retry(max_retries, retry_delay)
    def test_api_connectivity(self):
        """
        Test API connectivity by making a test request to the OpenAI API.
        """
        try:
            response = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {self.OPENAI_API_KEY}"})
            if response.status_code == 200:
                logger.success("OpenAI API is reachable")
                return True
            else:
                logger.error(f"OpenAI API is not reachable. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error testing API connectivity: {e}")
            return False

    def get_openai_response(self, messages, model="gpt-3.5-turbo", max_tokens=100, temperature=0.7):
        """
        Sends a chat request to the OpenAI API using the GPT-3.5 Turbo model via `requests.post()`.

        Args:
            messages (list): A list of dictionaries containing the role and content of the messages.
            model (str): The model to use for the request (default is GPT-3.5 Turbo).
            max_tokens (int): Maximum number of tokens in the response.
            temperature (float): Sampling temperature to control creativity.

        Returns:
            str: The content of the response from OpenAI.
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_API_KEY}"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                logger.success("Successfully received a response from OpenAI")
                
                # Extract the content from the first choice in the response
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Error: {response.status_code} - {response.text}")
                raise AccessError(f"Failed to retrieve data from OpenAI API: {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to OpenAI failed: {e}")
            raise AccessError("Failed to retrieve data from OpenAI API") from e
