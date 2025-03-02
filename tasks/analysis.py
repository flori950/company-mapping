import os
import pandas as pd
from company_keywords.keywords import Keywords
from logger import Logger as logger
from tasks.mapping import generate_germany_map

def categorize_company(row):
    description = row['Short_Description'].lower()
    matched_codes = []
    matched_names = []

    # Check for all matching RE strategies (both code and name)
    for key, strategy in Keywords.re_strategies.items():
        # Check if the strategy name exists in the company description
        if strategy['name'].lower() in description:
            matched_codes.append(key)  # Append the strategy code like 'R0', 'R1'
            matched_names.append(strategy['name'])  # Append the strategy name like 'Refuse', 'Rethink'

    # If one or more matches are found, return them
    if matched_codes and matched_names:
        return pd.Series([row['Name'], row['Short_Description'], ', '.join(matched_codes), ', '.join(matched_names), len(matched_codes)])
    else:
        # Return 'Uncategorized' if no matches are found
        return pd.Series([row['Name'], row['Short_Description'], 'Uncategorized', 'Uncategorized', 0])

def run_job():
    # Define the path to crunchbase.csv relative to the current script location
    csv_path = os.path.join(os.path.dirname(__file__), "../reporting/crunchbase.csv")

    # Fetch data from Crunchbase
    logger.log("Fetching data from reporting")
    df = pd.read_csv(csv_path)

    # Apply categorization and capture number of categories
    logger.log("Categorizing companies based on their short descriptions")
    df[['Company_Name', 'Short_Description', 'RE_Strategy_Codes', 'RE_Strategy_Names', 'Category_Count']] = df.apply(categorize_company, axis=1)

    # Count how many entries have more than 1 RE strategy
    multiple_re_count = df[df['Category_Count'] > 1].shape[0]
    logger.log(f"Number of entries with more than one RE strategy: {multiple_re_count}")

    # Filter out rows where categories are 'Uncategorized'
    df_filtered = df[df['RE_Strategy_Codes'] != 'Uncategorized']

    # Select the necessary columns including address (City, Region, Country)
    df_filtered = df_filtered[['Company_Name', 'Short_Description', 'RE_Strategy_Codes', 'RE_Strategy_Names', 'City', 'Region', 'Country']]

    # Save categorized data as CSV
    logger.log("Saving categorized data as csv with address details")
    output_csv = "reporting/categorized_crunchbase_with_address.csv"
    df_filtered.to_csv(output_csv, index=False)

    # Clean up memory
    del df
    del df_filtered

    # Log that the job is complete
    logger.log("Analysis job complete.")
