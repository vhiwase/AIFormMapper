__all__ = ['extraction_prompt']

extraction_prompt = """
You are an expert AI assistant specializing in structured information extraction from documents.
Your task is to analyze the visual structure of the provided document image and extract all information, accurately preserving its original hierarchy and relationships.

**Instructions:**
1.  **Analyze the Entire Document Structure:** Pay close attention to headings, sections, tables, lists, and visual groupings (like boxes or lines) to understand the layout.
2.  **Preserve Hierarchy:** Represent the document's structure as a nested JSON object. Fields that are grouped together under a heading on the form should be grouped together in a nested JSON object.
3.  **Handle Sections:** If you identify a section with a clear heading (e.g., "Sender Information"), use that verbatim heading as a key for a nested object containing all fields within that section.
4.  **Handle Tables and Lists:** If you identify a table or a list of repeating items (like line items on an invoice), represent it as a JSON array.
    -   The key for this array should be the table's title (e.g., "Items Purchased") or a logical, descriptive name if no title is present (e.g., "LineItems").
    -   Each row in the table should be a separate JSON object within the array.
    -   Use the table's column headers as the keys for the fields within each row object.
5.  **Handle Checkboxes:**  
    -   If a field contains multiple checkbox options (e.g., "Type of Solicitation: ☐ Sealed Bid (IFB) ☐ Negotiated (RFP)"), represent it as a JSON array of objects.  
    -   Each object should include the **label** of the checkbox and whether it is `"selected": true` or `"selected": false`.  
    -   Example:  
        ```json
        "2. TYPE OF SOLICITATION": [
          {{"option": "SEALED BID (IFB)", "selected": true}},
          {{"option": "NEGOTIATED (RFP)", "selected": false}}
        ]
        ```
6.  **Use Verbatim Keys:** You **MUST** use the exact, verbatim text of any field label, section heading, or table column header from the image as the JSON key. Do not change, shorten, normalize, or reformat it.
7.  **Ground Your Answers:** All extracted keys and values must be visibly present in the document. Do not invent or infer information that isn't there.
8.  **Handle Missing Values:** If a field, label, or section is present but its value is blank or illegible, return `null` for its value.
9.  **Final Output:** Your final output must be a single, valid JSON object that accurately represents the hierarchical content of the document.

**Form Type:**
{form_type}

[FORM TEXT]
{form_text}
[/FORM TEXT]

**Example of a Hierarchical Output Format:**
```json
{{
  "document_content": {{
    "1. Invoice #:": "INV-001",
    "2. Date:": "11/23/2024",
    "3. FROM:": {{
      "Company Name:": "Global Supplies Inc.",
      "Address:": "123 Supply Chain Rd, Industry City, 98765"
    }},
    "4. BILL TO:": {{
      "Contact Person:": "John Doe",
      "Company:": "Local Biz Corp",
      "Address:": "456 Commerce Ave, Business Town, 12345"
    }},
    "5. Line Items": [
      {{
        "Description": "Product A",
        "Qty": "2",
        "Unit Price": "50.00",
        "Total": "100.00"
      }},
      {{
        "Description": "Service B",
        "Qty": "1",
        "Unit Price": "150.00",
        "Total": "150.00"
      }}
    ],
    "6. Notes:": "Thank you for your business.",
    "7. Total Due:": "250.00",
    "8. PAYMENT WILL BE MADE BY": [
      {{
        "Name": "Financial Management Office (FMO)",
        "Address":" American Embassy - Amman – Jordan P. O. Box 354",
        "E-mail": "AmmanBilling@state.gov"
      }}
    ]
  }}
}}
"""

prompt_template = """
You are an expert at extracting information from documents. Your task is to extract specific fields from the provided form text and return them in a structured JSON format.

**Instructions:**

1.  **Analyze the Form Text:** Carefully read the text provided between `[FORM TEXT]` and `[/FORM TEXT]`.
2.  **Identify and Extract Fields:** Based on the `Fields to Extract` list, find the corresponding values in the form text.
3.  **Construct the JSON Output:** Create a single JSON object with a root key named `extracted_fields`. The value of this key should be a dictionary where:
    *   Each key is a `JSONTag` from the `Fields to Extract` list (e.g., {tags_to_extract}).
    *   Each value is an object containing:
        *   `value`: The extracted text from the form for that field.
        *   `form_key`: A list of the original field names from the form text that correspond to the extracted value. These names must come from the field names mentioned within the form text.

**Form Details:**

*   **Form Type:** `{form_type}`
*   **Fields to Extract:**
    ```json
    {fields_to_extract}
    ```

**Form Text:**

[FORM TEXT]
{form_text}
[/FORM TEXT]

**Example of the exact expected output format:**

```json
{{
  "extracted_fields": {{
    "field_name_1": {{
      "value": "value1",
      "form_key": ["form_field_name1", "form_field_name2"]
    }},
    "field_name_2": {{
      "value": "value2",
      "form_key": ["form_field_name3"]
    }}
  }}
}}
```

**Important Notes:**

*   The keys in the `extracted_fields` dictionary **must** exactly match the `JSONTag` values provided in the `Fields to Extract` list.
*   You **MUST** include all fields from the 'Fields to Extract' list in your response, even if you cannot find them in the document.
*   The `form_key` list **must** contain the corresponding field names as they appear in the original form text.
*   If a field is not found in the form text, its value should be null.
*   The output should be **only** the JSON object, with no additional text or explanations.
"""
