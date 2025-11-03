from openai import AzureOpenAI
from app.config import DevelopmentConfig as config
from app.utils.logger import log as _log, logger
import functools

log = functools.partial(_log, silence=False)

class FormTypeService:
    def __init__(self):
        self._initialize_config()

    def _initialize_config(self):
        self.api_key = config.GPT_4_1_API_KEY
        self.api_version = config.GPT_4_1_API_VERSION
        if not config.GPT_4_1_DEPLOYMENT_NAME:
            raise ValueError("Deployment name must be configured")
        self.deployment = config.GPT_4_1_DEPLOYMENT_NAME
        self.endpoint = config.GPT_4_1_AZURE_ENDPOINT
        if not self.endpoint:
            raise ValueError("Azure endpoint must be configured")

    @log()
    def identify_form_type(self, ocr_text: str) -> str:
        if not ocr_text:
            return "Unknown"

        prompt = f"""
        Based on the following OCR text from a document, please identify the type of the document.
        Examples of document types include: "Invoice", "Bill of Lading", "Packing List", "Dock Receipt", "Purchase Order", etc.
        Please provide only the document type as a short, descriptive name.

        OCR Text:
        ---
        {ocr_text[:2000]}
        ---

        Document Type:
        """

        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

        response = client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an expert in document analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        
        form_type = "Unknown"
        try:
            content = response.choices[0].message.content
            if content:
                form_type = content.strip()
        except Exception:
            logger.error("Unexpected response structure when identifying form type")
        logger.info(f"Identified form type: {form_type}")
        return form_type
