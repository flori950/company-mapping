from company_keywords.keywords import Keywords

def construct_prompt(company_name, city, country, strategy_code, short_description):
    """
    Constructs the OpenAI prompt based on the company name, city, country, RE strategy, and company description.

    Args:
        company_name (str): The name of the company.
        city (str): The city of the company.
        country (str): The country of the company.
        strategy_code (str): The RE strategy code (R0, R1, etc.).
        short_description (str): The short description of the company.

    Returns:
        list: A list of messages with system and user roles for OpenAI API.
    """
    strategy = Keywords.re_strategies.get(strategy_code)
    if not strategy:
        raise ValueError(f"Strategy code {strategy_code} not found in Keywords")

    # Return messages for the chat-based OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that provides structured answers for validation."
        },
        {
            "role": "user",
            "content": (
                f"Analyze if the company '{company_name}' located in {city}, {country}, "
                f"with the description '{short_description}', can apply the circular economy strategy "
                f"'{strategy['name']}' defined as '{strategy['definition']}'. "
                f"Please answer in the following structured format:\n\n"
                f"1. Agreement: [Agree/Disagree]\n"
                f"2. Strategy: [{strategy_code}: {strategy['name']} or None if not applicable]\n"
                f"3. Explanation (only if disagreeing): [Brief explanation within 20 words]\n\n"
                f"Note: Provide 'None' for the strategy if you disagree and cannot find a suitable strategy."
            )
        }
    ]
    
    return messages
