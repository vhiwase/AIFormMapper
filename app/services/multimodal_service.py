import functools
import base64
import io

from app.mapping import mapping

from app.services.form_type_service import FormTypeService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.mapping_service import MappingService

from app.utils.logger import log as _log
from app.utils.algorithms import get_string_similarity


log = functools.partial(_log, silence=False)

def _find_all_matching_indices(line_dataframe, form_key, threshold=0):
    """
    Finds all indices in a dataframe that match a given form key.

    This function searches for matches in a few steps:
    1.  Exact match on a single line.
    2.  Exact match on combined adjacent lines.
    3.  Fuzzy string matching for close matches.

    Args:
        line_dataframe (pd.DataFrame): Dataframe containing OCR line data,
            including a 'text' column.
        form_key (str): The string key to search for. Can contain newlines.
        threshold (int): Dissimilarity score threshold for fuzzy matching.

    Returns:
        list[int]: A sorted list of unique line indices that match the form key.
    """
    value_top_indices = set()
    search_lines = [s.strip().lower() for s in form_key.split('\n') if s.strip()]
    
    if not search_lines:
        return []

    texts = {index: str(text).strip().lower() for index, text in line_dataframe.text.items()}
    sorted_indices = sorted(texts.keys())

    for search_line in search_lines:
        if not search_line:
            continue
        
        # 1. Exact match on single line
        match_found = False
        for index in sorted_indices:
            if search_line in texts.get(index, ""):
                value_top_indices.add(index)
                match_found = True
                break
        if match_found:
            continue

        # 2. Exact match on combined adjacent lines
        for i in range(len(sorted_indices) - 1):
            idx1 = sorted_indices[i]
            idx2 = sorted_indices[i+1]
            if idx2 != idx1 + 1:
                continue
            combined_text = texts.get(idx1, "") + ' ' + texts.get(idx2, "")
            if search_line in combined_text:
                value_top_indices.add(idx1)
                value_top_indices.add(idx2)
                match_found = True
                break
        if match_found:
            continue

        # 3. Fallback to fuzzy matching
        for index in sorted_indices:
            target_lower = texts.get(index, "")
            dissimilarity_score = get_string_similarity(search_line, target_lower).get("dissimilarity_score")
            text_length = get_string_similarity(search_line, target_lower).get("text_length")
            subtext_length = get_string_similarity(search_line, target_lower).get("subtext_length")
            if text_length > subtext_length and subtext_length==1:
                continue
            if abs(text_length - subtext_length) < 2 and dissimilarity_score <= threshold:
                value_top_indices.add(index)
                break # Found a fuzzy match, move to next search_line
    
    return sorted(list(value_top_indices))


class MultiModal:
    """
    A class to process documents using a multi-modal approach, combining
    image and text data for information extraction and mapping.

    This class orchestrates a pipeline of pre-processing, inference, and
    post-processing steps to extract structured data from document images.

    Attributes:
        pil_images (list): A list of PIL Image objects.
        ocr_texts (list): A list of OCR-extracted texts for each image.
        mapping_key_name (str): The key name for the specific mapping to be used.
        document_ai_object: An object containing detailed document analysis results,
            including a line dataframe with coordinates.
        mapping (dict): The data mapping configuration.
        form_type_service (FormTypeService): A service for identifying form types.
    """
    def __init__(self, pil_images: list, ocr_texts: list, mapping_key_name: str, document_ai_object=None):
        """
        Initializes the MultiModal class with document data.

        Args:
            pil_images (list): A list of PIL Image objects for each page.
            ocr_texts (list): A list of strings, where each string is the
                OCR text of a corresponding page.
            mapping_key_name (str): The key for the mapping configuration to use.
            document_ai_object: An optional object containing pre-computed
                document analysis data, like line dataframes.
        """
        self.pil_images = pil_images
        self.ocr_texts = ocr_texts
        self.mapping_key_name = mapping_key_name
        self.document_ai_object = document_ai_object
        self.mapping = mapping[mapping_key_name]
        
        self.form_type_service = FormTypeService()

    @log()
    def pre_process(self) -> dict:
        """
        Performs pre-processing steps on the input document.

        This involves identifying the form type from the first page's OCR text
        and encoding all document images into base64 strings.

        Returns:
            dict: A dictionary containing the identified 'form_type' and a list
                of 'base64_images'.
        """
        form_type = "Unknown"
        if self.ocr_texts:
            form_type = self.form_type_service.identify_form_type(self.ocr_texts[0])

        base64_images = []
        for pil_image in self.pil_images:
            try:
                img = pil_image.convert('RGB')
            except Exception:
                img = pil_image

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            base64_images.append(base64.b64encode(img_byte_arr.getvalue()).decode("utf-8"))
        
        pre_process_output = {
            "form_type": form_type,
            "base64_images": base64_images
        }
        return pre_process_output

    @log()
    def inference(self, pre_process_output: dict) -> dict:
        """
        Performs the main inference step to extract information.

        This method builds a knowledge base from the content of all pages and
        then uses a mapping service to extract the final, structured output.

        Args:
            pre_process_output (dict): The output from the pre_process method,
                containing 'form_type' and 'base64_images'.

        Returns:
            dict: The final extracted and mapped data from the document.
        """
        form_type = pre_process_output.get("form_type")
        base64_images = pre_process_output.get("base64_images")
        
        # Part 1: Knowledge Base Creation
        knowledge_base_content = ""
        previous_page_summary = None
        for i, pil_image in enumerate(self.pil_images):
            ocr_text = self.ocr_texts[i] if i < len(self.ocr_texts) else ""
            kb_service = KnowledgeBaseService(pil_image, ocr_text, previous_page_summary)
            extraction_content, _ = kb_service.initial_extraction(form_type)
            knowledge_base_content += extraction_content + "\n\n"
            previous_page_summary = extraction_content

        # Part 2: Final Mapping
        mapping_service = MappingService(self.mapping_key_name)
        final_output = mapping_service.final_mapping(knowledge_base_content, form_type, base64_images)

        return final_output

    @staticmethod
    def _find_best_matched_indices(form_keys, value_for_search, line_dataframe, template_field):
        """
        Finds the best matching indices for a field, prioritizing value locations
        that appear on the same page as a corresponding form key.

        Args:
            form_keys (list[str]): A list of possible form keys for the field.
            value_for_search (str): The value string to search for.
            line_dataframe (pd.DataFrame): Dataframe with line-level OCR data.
            template_field (str): The name of the template field.

        Returns:
            tuple[list[int], str]: A tuple containing the list of best matched
            indices and the associated field name for the region.
        """
        matched_indices = []
        field_name_for_region = None

        if form_keys and value_for_search:
            key_indices_by_page = {}
            all_key_indices = []
            for fk in form_keys:
                indices = _find_all_matching_indices(line_dataframe, fk, threshold=0)
                all_key_indices.extend(indices)
                for idx in indices:
                    page = line_dataframe.loc[idx, 'page']
                    if page not in key_indices_by_page:
                        key_indices_by_page[page] = {'indices': [], 'fks': set()}
                    key_indices_by_page[page]['indices'].append(idx)
                    key_indices_by_page[page]['fks'].add(fk)

            value_indices_by_page = {}
            value_indices = _find_all_matching_indices(line_dataframe, value_for_search, threshold=0)
            for idx in value_indices:
                page = line_dataframe.loc[idx, 'page']
                if page not in value_indices_by_page:
                    value_indices_by_page[page] = []
                value_indices_by_page[page].append(idx)
            
            common_pages = set(key_indices_by_page.keys()) & set(value_indices_by_page.keys())

            if common_pages:
                for page in sorted(list(common_pages)):
                    matched_indices.extend(value_indices_by_page[page])
                    field_name_for_region = list(key_indices_by_page[page]['fks'])[0]
            else:
                if value_indices:
                    matched_indices = value_indices
                    if form_keys:
                        field_name_for_region = form_keys[0]
                elif all_key_indices:
                    matched_indices = all_key_indices
                    if form_keys:
                        field_name_for_region = form_keys[0]

        elif form_keys:
            for fk in form_keys:
                matched_indices.extend(_find_all_matching_indices(line_dataframe, fk, threshold=0))
            if form_keys:
                field_name_for_region = form_keys[0]

        elif value_for_search:
            matched_indices = _find_all_matching_indices(line_dataframe, value_for_search, threshold=0)
            field_name_for_region = template_field
        
        return matched_indices, field_name_for_region

    @staticmethod
    def _create_field_regions(indices, field_name, value, template_field, document_id, line_dataframe):
        """
        Creates a list of region dictionaries from a list of matched indices.

        Args:
            indices (list[int]): The list of line indices for the field.
            field_name (str): The name of the field.
            value (str): The predicted value of the field.
            template_field (str): The name of the template field.
            document_id (str): The ID of the document.
            line_dataframe (pd.DataFrame): Dataframe with line-level OCR data.

        Returns:
            list[dict]: A list of dictionaries, each representing a matched region
            with its coordinates and other metadata.
        """
        regions = []
        if not indices:
            return regions

        unique_indices = sorted(list(set(indices)))
        
        matched_regions_data = line_dataframe.loc[unique_indices,['text', 'top_left_x', 'top_left_y', 'bottom_right_x', 'bottom_right_y', 'height', 'width', 'unit', 'page', 'line_numbers']].to_dict(orient='records')
        
        for matched_region in matched_regions_data:
            region = {
                'text': matched_region['text'],
                'top_left_x': matched_region['top_left_x'],
                'top_left_y': matched_region['top_left_y'],
                'bottom_right_x': matched_region['bottom_right_x'],
                'bottom_right_y': matched_region['bottom_right_y'],
                'height': matched_region['height'], 
                'width': matched_region['width'],
                'unit': matched_region['unit'], 
                'page': matched_region['page'],
                'line_numbers': matched_region['line_numbers'],
                'predicted_value': value, 
                'field_name': field_name,
                'document_id': document_id,
                'template_field': template_field
            }
            regions.append(region)
        return regions

    @log()
    def post_process(self, inference_output: dict) -> dict:
        """
        Performs post-processing to add bounding box information to extracted fields.

        This method takes the output from the inference step and uses the
        document analysis object to find the coordinates of the extracted values.

        Args:
            inference_output (dict): The output from the inference method.

        Returns:
            dict: A dictionary of extracted fields, where each field includes
            its value, bounding box coordinates, and other metadata.
        """

        if not self.document_ai_object:
            return inference_output

        try:
            content_data = inference_output.get('chunk', {})
            llm_extracted_fields = content_data.get('extracted_fields', {})
        except (AttributeError):
            llm_extracted_fields = {}

        line_dataframe = self.document_ai_object.line_dataframe
        document_id = self.document_ai_object.document_id
        template_fields = {item['JSONTag'] for item in self.mapping}
        
        extracted_fields = []

        for template_field in template_fields:
            value_info = llm_extracted_fields.get(template_field)
            value = value_info.get('value') if value_info else None
            form_keys = value_info.get('form_key', []) if value_info else []
            value_for_search = str(value).strip() if value is not None and not isinstance(value, dict) else None
            
            matched_indices, field_name = self._find_best_matched_indices(form_keys, value_for_search, line_dataframe, template_field)

            if matched_indices:
                regions = self._create_field_regions(matched_indices, field_name, value_for_search, template_field, document_id, line_dataframe)
                extracted_fields.extend(regions)
                
        return extracted_fields

    @log()
    def handler(self):
        """
        Orchestrates the full document processing pipeline.

        This method runs the pre-processing, inference, and post-processing
        steps in sequence to perform the end-to-end document extraction task.

        Returns:
            dict: The final post-processed output containing extracted fields
            with their bounding box information.
        """
        pre_process_output = self.pre_process()
        inference_output = self.inference(pre_process_output)
        post_process_output = self.post_process(inference_output)
        return post_process_output
