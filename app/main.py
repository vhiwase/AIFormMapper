import os
import shutil
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.services.multimodal_service import MultiModal
from app.utils.azure_read_api import get_azure_document_ai_object, get_azure_page_content
from app.utils.pdf_converter import pdf_page_images_generator
from app.utils.azure_document_ai import parse_document_ai_object

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Your application is up!"}


@app.post("/extract/")
async def extract_information(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        os.makedirs("/app/temp_data", exist_ok=True)
        temp_file_path = f"/app/temp_data/temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file
        azure_document_ai_object = get_azure_document_ai_object(temp_file_path)
        document_ai_object = parse_document_ai_object(azure_document_ai_object)
        page_content = get_azure_page_content(azure_document_ai_object)

        images = []
        ocr_texts = []
        for page_num, image in pdf_page_images_generator(temp_file_path, dpi=300):
            images.append(image)
            ocr_texts.append(page_content.get(page_num, ""))

        multimodel = MultiModal(images, ocr_texts=ocr_texts, mapping_key_name='dock_management', document_ai_object=document_ai_object)
        output = multimodel.handler()

        # Clean up the temporary file
        os.remove(temp_file_path)

        # Format the response to match expected structure
        formatted_response = {
            "formatted_response": {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(output) if output else "{}"
                        }
                    }
                ]
            }
        }
        return formatted_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))