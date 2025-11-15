def extraction_prompt(markdown_preview):

    return f"""You are a financial data extraction expert. Analyze the balance sheets and suggest common metrics that can be consistently extracted from each balance sheet.

    Here is the markdown content of the balance sheet:
    {markdown_preview}

    Suggest relevant metrics that can be extracted from this balance sheet. 
    For each metric, provide:
    1. The metric name (in snake_case for Python)
    2. The data type (str, int, float, bool)
    3. A clear description

    Focus on:
    - Key financial figures (amounts, balances, totals)
    - Identifiers (account numbers, names, dates)
    - Counts (number of transactions, deposits, etc.)

    Return ONLY valid JSON format (no markdown, no explanations):
    {{
    "suggested_metrics": [
        {{
        "name": "account_holder_name",
        "type": "str",
        "description": "The name of the account holder"
        }},
        {{
        "name": "total_assets",
        "type": "float",
        "description": "Total assets amount"
        }},
        {{
        "name": "number_deposits",
        "type": "int",
        "description": "The number of deposits"
        }}
    ],
    "reasoning": "Brief explanation of why these metrics are relevant"
    }}"""

def extraction_prompt_with_user_input(user_prompt, markdown_preview):

    return f"""You are a financial data extraction expert. A user wants to extract specific metrics from balance sheets.

    User's requirements: {user_prompt}

    Here is the markdown content of the balance sheets:
    {markdown_preview}

    Based on the user's requirements and the balance sheets content, suggest common metrics that can be consistently extracted from each balance sheet. 
    For each metric, provide:
    1. The metric name (in snake_case for Python)
    2. The data type (str, int, float, bool)
    3. A clear description

    Return ONLY valid JSON format (no markdown, no explanations):
    {{
    "suggested_metrics": [
        {{
        "name": "account_holder_name",
        "type": "str",
        "description": "The name of the account holder"
        }},
        {{
        "name": "total_assets",
        "type": "float",
        "description": "Total assets amount"
        }}
    ],
    "reasoning": "Brief explanation of why these metrics are relevant"
    }}"""