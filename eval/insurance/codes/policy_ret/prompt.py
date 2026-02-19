def policy_retrieval_prompt_baseline(provider_name):
    """
    Retrieves all official links to genetic testing coverage policies for a provider without keyword filtering.
    Returns strictly formatted JSON with 'pdf_links' and 'webpage_links'.
    """
    return (
        f"Find all official policy documents about genetic testing coverage for '{provider_name}'."
        f"Include every relevant policy, even if there are multiple documents."
        "Determine whether each link is a PDF or an HTML webpage based on its format or extension."
        "Group them accordingly in the response.\n\n"

        "Only include links from official sources such as the insurance company's website or regulatory bodies. "
        "Exclude links from news articles, blog posts, or discussion forums. "

        "If the policy is available as a PDF, return the direct PDF link under the key \"pdf_links\". "
        "If the policy is available only as an HTML webpage, return the webpage URL under the key \"webpage_links\". "
        "The response must be strictly in JSON format with two single keys: "
        "\"pdf_links\", containing an array of valid PDF URLs, and "
        "\"webpage_links\", containing an array of valid webpage URLs. "
        "Do not include any additional text or explanations—only the JSON object."
    )

def policy_retrieval_prompt_keyword_checked_document(provider_name):
    """
    Retrieves links only if the documents contain specific genetic-related keywords and excludes irrelevant content.
    """
    return (
        f"Find and list all official links to policy documents that describe genetic testing coverage for the insurance provider '{provider_name}'. "
        "Only include documents if they contain at least one of the following key terms: "
        "'coverage policy', 'medical policy', 'clinical policy', 'WES', 'WGS', 'BRCA', 'Duchenne muscular dystrophy', "
        "'hereditary cancer', 'genetic testing', 'lynch syndrome', or 'pharmacogenetic'. "
        "Include every relevant policy, even if there are multiple documents."
        "Exclude any documents that contain the phrase 'providal guideline', or that are press releases, claim forms, newsletters, blog posts, or provider manuals."
        "Only include links from official sources such as the insurance company’s website or regulatory bodies. "

        "Determine whether each link is a PDF or an HTML webpage based on its format or extension."
        "Group them accordingly in the response.\n\n"
        "If a document is available as a downloadable PDF, return the full direct PDF link under the key 'pdf_links'. "
        "If the document is only available as a webpage, return the full URL under the key 'webpage_links'. "
        "The JSON response must follow this exact format: "
        "{\"pdf_links\": [list of direct PDF links], \"webpage_links\": [list of webpage URLs]}. "
        "If no qualifying documents are found, return empty lists. "
        "Do not include any explanation, markdown, natural language, or formatting — only return the raw JSON object."
    )

def policy_retrieval_prompt_keyword_verified_links(provider_name):
    """
    Added stricter requirements for URL validity and official policy page confirmation.
    """
    return (
        f"Find and list all official links to policy documents that describe genetic testing coverage for the insurance provider '{provider_name}'. "
        "Only include documents if they contain at least one of the following key terms: "
        "'coverage policy', 'medical policy', 'clinical policy', 'WES', 'WGS', 'BRCA', 'Duchenne muscular dystrophy', "
        "'hereditary cancer', 'genetic testing', 'lynch syndrome', or 'pharmacogenetic'. "
        "Include every relevant policy, even if there are multiple documents."
        "Exclude any documents that contain the phrase 'providal guideline', or that are press releases, claim forms, newsletters, blog posts, or provider manuals."
        "Only include links from official sources such as the insurance company’s website or regulatory bodies, with official PDF links or official HTML policy pages."
        "Determine whether each link is a PDF or an HTML webpage based on its format or extension."
        "Group them accordingly in the response.\n\n"
        "If a document is available as a downloadable PDF, return the full direct PDF link under the key 'pdf_links'. "
        "If the document is only available as a webpage, return the full URL under the key 'webpage_links'. "
        "The JSON response must follow this exact format: "
        "{\"pdf_links\": [list of direct PDF links], \"webpage_links\": [list of webpage URLs]}. "
        "Make sure the lists contain only valid, existing URLs. If no documents are found, return empty lists. "
        "Do not include any explanation, markdown, natural language, or formatting — only return the raw JSON object."
    )

prompt_functions = {
    "baseline": policy_retrieval_prompt_baseline,
    "keyword": policy_retrieval_prompt_keyword_checked_document,
    "verified": policy_retrieval_prompt_keyword_verified_links
}
