"""
This script interacts with the Azure Document Intelligence API to perform OCR on documents.

It provides functions to:
- Generate a unique document ID based on the file's content.
- Analyze a document using a specified model and extract its content.
- Extract the text content from each page of the analyzed document.
"""
# import libraries
import hashlib

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature
from azure.core.credentials import AzureKeyCredential

from app.config import DevelopmentConfig as config


def generate_document_id(file_path):
    """
    Generates a unique document ID by creating an MD5 hash of the file's content.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The MD5 hash of the file.
    """
    # Read file in binary mode and calculate MD5 hash
    with open(file_path, 'rb') as file:
        binary_data = file.read()
        md5_hash = hashlib.md5(binary_data).hexdigest()
    return md5_hash


def get_azure_document_ai_object(pdf_path):
    """
    Analyzes a PDF document using Azure Document Intelligence and returns the result.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        dict: A dictionary containing the analysis result from Azure Document Intelligence,
              with an added 'document_id' field.
    """
    # set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
    endpoint = config.DOCUMENT_INTELLIGENCE_ENDPOINT
    key = config.DOCUMENT_INTELLIGENCE_KEY
    model = config.DOCUMENT_INTELLIGENCE_MODEL

    analysis_features = ["ocrHighResolution", "keyValuePairs", "barcodes", "formulas", "languages"]
    analysis_features = [DocumentAnalysisFeature(feature) for feature in analysis_features]
    
    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
        headers={"x-ms-useragent": "langchain-parser/1.0.0"},
        features=analysis_features,
        api_version="2024-11-30"
    )
    document_ai_object = {}
    with open(pdf_path, "rb") as file_obj:
        poller = client.begin_analyze_document(
            model,
            file_obj,
            content_type="application/octet-stream",
            output_content_format="text",
        )
        result = poller.result()
        document_ai_object = result.as_dict()

    document_id = generate_document_id(pdf_path)
    document_ai_object["document_id"] = document_id
    return document_ai_object


def get_azure_page_content(document_ai_object):
    """
    Extracts the text content from each page of an analyzed document.

    Args:
        document_ai_object (dict): The analysis result from Azure Document Intelligence.

    Returns:
        dict: A dictionary where keys are page numbers and values are the text content of each page.
    """
    pages = document_ai_object.get("pages")
    page_content = {}
    for page in pages:
        page_number = page.get('pageNumber')
        lines = page.get('lines')
        lines_content = []
        for line in lines:
            content = line.get('content')
            if content:
                lines_content.append(content)
        content = '\n'.join(lines_content)
        page_content[page_number] = content
    return page_content
        
    
if __name__ == "__main__":
    pdf_path = 'C:/Users/Dell/Documents/3PL/sample_documents/3835-22 MULTILINK CO+INV+PL+BL.pdf'
    document_ai_object = get_azure_document_ai_object(pdf_path)
    page_content = get_azure_page_content(document_ai_object)
    print(page_content)