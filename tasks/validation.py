import os
import json
import pandas as pd
from bigquery.client import BigQueryClient
from logger import Logger as logger
from company_keywords.keywords import Keywords
from openai_request.client import OpenAIClient
from openai_request.openai_requests_prompt import construct_prompt
from tasks.mapping import generate_germany_map

def run_job(client: OpenAIClient, bqclient: BigQueryClient, upload=False):

    #TODO bigquery upload
    # Process the CSV and add the OpenAI responses
    input_csv = 'reporting/categorized_crunchbase_with_address.csv'
    output_csv = 'reporting/categorized_crunchbase_with_openai_responses.csv'
    re_strategies = Keywords.re_strategies

    process_csv_and_save(input_csv, output_csv, re_strategies, client)

def validate_columns(df, required_columns):
    """
    Validate if the required columns exist in the DataFrame.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    return True

def validate_strategy_code(strategy_code, strategy_dict):
    """
    Validate if the strategy code exists in the given strategy dictionary.
    """
    if strategy_code not in strategy_dict:
        logger.error(f"Strategy code {strategy_code} is not valid.")
        return False
    return True

def handle_row_error(row, error_message):
    """
    Logs an error when there is an issue with processing a row.
    """
    logger.error(f"Error processing row: {row}. Error: {error_message}")
    return "Error in OpenAI response"

# Function to load or create cache in the 'reporting' folder
def load_cache(cache_file):
    cache_folder = os.path.join(os.getcwd(), 'cache')
    cache_file_path = os.path.join(cache_folder, cache_file)

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    if os.path.exists(cache_file_path):
        logger.info(f"Loading cache from {cache_file_path}")
        with open(cache_file_path, 'r') as f:
            return json.load(f)
    logger.info(f"No cache found. Starting fresh.")
    return {}

# Function to save cache to a file in the 'reporting' folder
def save_cache(cache, cache_file):
    cache_folder = os.path.join(os.getcwd(), 'cache')
    cache_file_path = os.path.join(cache_folder, cache_file)

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    logger.info(f"Saving cache to {cache_file_path}")
    with open(cache_file_path, 'w') as f:
        json.dump(cache, f)

def get_cache_key(company_name, city, country, strategy_code):
    """
    Generate a unique cache key based on company name, city, country, and strategy code.
    """
    return f"{company_name}_{city}_{country}_{strategy_code}"

def process_csv_and_save(input_csv, output_csv, strategy_dict, openai_client, cache_file='openai_cache.json'):
    """
    Reads the categorized Crunchbase CSV, sends each entry to OpenAI, and adds the strategy code and term or a disagreement message
    as new columns 'openai_agreement', 'openai_strategy', and 'openai_explanation'. Saves the new DataFrame to a CSV, using caching.
    """
    logger.info(f"Loading data from {input_csv}")
    
    # Load the cache
    cache = load_cache(cache_file)
    
    # Read the input CSV
    df = pd.read_csv(input_csv)

    # Validate if required columns exist
    required_columns = ['Company_Name', 'City', 'Country', 'RE_Strategy_Codes', 'RE_Strategy_Names', 'Short_Description']
    if not validate_columns(df, required_columns):
        return
    
    # Initialize lists for new columns
    openai_agreements = []
    openai_strategies = []
    openai_explanations = []

    # Loop through each row and generate OpenAI responses
    for _, row in df.iterrows():
        try:
            company_name = row['Company_Name']
            city = row['City']
            country = row['Country']
            strategy_codes = row['RE_Strategy_Codes'].split(", ")
            short_description = row['Short_Description']

            # Initialize lists to store responses for this row
            row_agreements = []
            row_strategies = []
            row_explanations = []

            # Iterate over each strategy code
            for strategy_code in strategy_codes:
                # Validate strategy code
                if not validate_strategy_code(strategy_code, strategy_dict):
                    row_agreements.append("Invalid")
                    row_strategies.append(f"Invalid strategy code: {strategy_code}")
                    row_explanations.append("")
                    continue

                # Generate a unique cache key based on company and strategy
                cache_key = get_cache_key(company_name, city, country, strategy_code)
                
                # Check if the result is already cached
                if cache_key in cache:
                    logger.info(f"Using cached response for {company_name} ({strategy_code})")
                    response = cache[cache_key]
                else:
                    # Construct the OpenAI prompt for each strategy
                    messages = construct_prompt(company_name, city, country, strategy_code, short_description)

                    # Get OpenAI response
                    logger.info(f"Sending request to OpenAI for {company_name} ({strategy_code})")
                    response = openai_client.get_openai_response(messages)

                    # Cache the response
                    cache[cache_key] = response
                    save_cache(cache, cache_file)

                # Parse the response into its structured format
                agreement, strategy, explanation = parse_openai_response(response)

                # Append the parsed values to the row-specific lists
                row_agreements.append(agreement)
                row_strategies.append(strategy)
                row_explanations.append(explanation)

            # Combine responses for this row into a single string
            openai_agreements.append(", ".join(row_agreements))
            openai_strategies.append(", ".join(row_strategies))
            openai_explanations.append(", ".join(row_explanations))

        except Exception as e:
            openai_agreements.append("Error")
            openai_strategies.append("Error")
            openai_explanations.append(handle_row_error(row, str(e)))

    # Validate that the number of responses matches the number of rows
    if len(openai_agreements) != len(df):
        raise ValueError("Length of OpenAI responses does not match the number of rows in the DataFrame.")

    # Add the responses as new columns
    df['openai_agreement'] = openai_agreements
    df['openai_strategy'] = openai_strategies
    df['openai_explanation'] = openai_explanations

    # Save the updated DataFrame to the output CSV
    logger.info(f"Saving new CSV with OpenAI responses to {output_csv}")
    df.to_csv(output_csv, index=False)

    # Explicitly delete the DataFrame and clear memory
    del df
    logger.log("Validation job complete.")

def parse_openai_response(response):
    """
    Parse the structured response from OpenAI and return the agreement, strategy, and explanation.

    Args:
        response (str): The structured response from OpenAI.

    Returns:
        tuple: A tuple containing agreement (str), strategy (str), and explanation (str).
    """
    try:
        # Split the response into lines
        lines = response.split("\n")

        # Extract the agreement (Assume format: "Agreement: Agree" or "Agreement: Disagree")
        agreement = lines[0].split(": ")[1].strip()

        # Extract the strategy (Assume format: "Strategy: R#: StrategyName")
        strategy = lines[1].split(": ")[1].strip()

        # Extract the explanation, if present (only if disagreement exists)
        if agreement == "Disagree" and len(lines) > 2:
            explanation = lines[2].split(": ")[1].strip()
        else:
            explanation = ""

        return agreement, strategy, explanation

    except Exception as e:
        logger.error(f"Error parsing OpenAI response: {response}. Error: {str(e)}")
        return "Error", "Error", "Error"


