def name_retrieval_prompt_baseline():
    """
    Retrieves all payer names associated with GeneDx.
    Returns strictly formatted JSON with 'Providers' and 'source_url'.
    """
    return (
        "You are a helpful assistant. Respond only in strict JSON format with no explanation or extra commentary."
        "List all the medical insurance providers that are currently in-network with GeneDx." 
        "Format your response as: {\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}." 
        "Only use information from official GeneDx or trusted affiliate websites."
    )

def name_retrieval_prompt_explicit_source():
    """
    Retrieves all payer names associated with GeneDx.
    Add the website source used for retrieval.
    Returns strictly formatted JSON with 'Providers' and 'source_url'.
    """
    return (
        "You are a helpful assistant. List all the medical insurance providers that are currently in-network with GeneDx. "
        "You may use the official GeneDx insurance network page at "
        "https://www.genedx.com/commercial-insurance-in-network-contracts/ as the primary source of information. "
        "Output the result strictly in JSON format using the following structure: {\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
        "Only include links from the official GeneDx website or affiliated trusted sources. "
        "Do not include any introduction, explanation, or extra commentary — only return the JSON object."
    )

prompt_functions = {
    "baseline": name_retrieval_prompt_baseline,
    "explicit": name_retrieval_prompt_explicit_source
}
