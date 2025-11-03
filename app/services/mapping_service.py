import json
from openai import AzureOpenAI
from app.config import DevelopmentConfig as config
from app.utils.logger import log as _log, logger
import functools
from app.mapping import mapping
from app.prompt import prompt_template

log = functools.partial(_log, silence=False)

class MappingService:
    def __init__(self, mapping_key_name):
        self._initialize_config()
        self.mapping_key_name = mapping_key_name # type: ignore

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
    def final_mapping(self, extraction_content: str, form_type: str, base64_images: list[str]) -> dict:
        key_management = mapping.get(self.mapping_key_name, {})
        fields_to_extract_str = ""
        tags_to_extract = []
        for item in key_management:
            fields_to_extract_str += f"- Form Field: '{item['FormField']}' -> JSON Tag: '{item['JSONTag']}'"
            if item.get('Notes'):
                fields_to_extract_str += f" (Notes: {item['Notes']})"
            fields_to_extract_str += "\n"
            tags_to_extract.append(item['JSONTag'])
        
        prompt = prompt_template.format(
            form_type=form_type,
            tags_to_extract=tags_to_extract,
            fields_to_extract=fields_to_extract_str,
            form_text=str(extraction_content)
        )

        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=str(self.endpoint)
        )

        safe_system_prompt = (
            f"You are an assistant that processes OCR’d shipping documents, such as '{form_type}'. "
            "Extract key-value pairs of all relevant information and output valid JSON. "
            "Ignore OCR noise and typos."
        )

        def build_messages(system_prompt, prompt):
            content = [{"type": "text", "text": prompt}]
            for b64_img in base64_images:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}})
            
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]

        response = client.chat.completions.create(
            model=self.deployment,
            messages=build_messages(safe_system_prompt, prompt),
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        return self._postprocess(content)

    def _postprocess(self, chunk: str) -> dict:
        try:
            if chunk.startswith("```json"):
                chunk = chunk[7:-4]
            
            return {"chunk": json.loads(chunk)}
        except (json.JSONDecodeError, TypeError):
            logger.error("Failed to parse JSON from model output.")
            return {"chunk": {"extracted_fields": {}}}