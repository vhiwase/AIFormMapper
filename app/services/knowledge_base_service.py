import base64
import io
from openai import AzureOpenAI
from app.config import DevelopmentConfig as config
from app.utils.logger import log as _log
import functools
from app.prompt import extraction_prompt

log = functools.partial(_log, silence=False)

class KnowledgeBaseService:
    def __init__(self, pil_image, ocr_text, previous_page_summary=None):
        self._initialize_config()
        self.pil_image = pil_image
        self.ocr_text = ocr_text
        self.previous_page_summary = previous_page_summary

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
    def _encode_image(self):
        if self.pil_image is None:
            raise ValueError("No image provided to encode")
        try:
            img = self.pil_image.convert('RGB')
        except Exception:
            img = self.pil_image

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

    @log()
    def initial_extraction(self, form_type: str) -> tuple[str, str]:
        base64_encoded_image = self._encode_image()

        def build_messages(system_prompt, prompt):
            return [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded_image}"}}
                    ]
                }
            ]
        
        safe_system_prompt = (
            f"You are an assistant that processes OCR’d shipping documents, such as '{form_type}'. "
            "Extract key-value pairs of all relevant information and output valid JSON. "
            "Ignore OCR noise and typos."
        )
        
        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        
        prompt = extraction_prompt.format(form_type=form_type, form_text=self.ocr_text)
        if self.previous_page_summary:
            prompt = f"{prompt}\n\nPrevious Page Summary:\n{self.previous_page_summary}"
            
        response = client.chat.completions.create(
            model=self.deployment,
            messages=build_messages(safe_system_prompt, prompt),
            max_tokens=4000
        )
        
        extraction_content = response.choices[0].message.content
        return extraction_content, base64_encoded_image
