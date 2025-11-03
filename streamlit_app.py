import streamlit as st
import requests
import os
import json
import logging
import io
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config to wide mode and custom title
st.set_page_config(
    page_title="Document Information Extraction",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state if not already done
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.extracted_data = None
    st.session_state.doc_images = []
    st.session_state.current_page = 0
    st.session_state.selected_field = None
    st.session_state.highlight_all = False # New state for highlighting all fields
    st.session_state.origin_company = ""
    st.session_state.origin_address = ""
    st.session_state.origin_phone = ""
    st.session_state.origin_email = ""
    st.session_state.dest_company = ""
    st.session_state.dest_address = ""
    st.session_state.dest_phone = ""
    st.session_state.dest_email = ""
    st.session_state.handling_unit = ""
    st.session_state.quantity = 0
    st.session_state.weight = 0.0
    st.session_state.weight_unit = "Lbs"
    st.session_state.bol_no = ""
    st.session_state.carrier_pro = ""
    st.session_state.customer_ref = ""
    st.session_state.nmfc = ""
    st.session_state.no_nmfc = False
    st.session_state.in_bond = False
    st.session_state.hazmat = False
    st.session_state.order_id = ""
    st.session_state.shipment_id = ""
    st.session_state.transport_id = ""
    st.session_state.last_uploaded_file = None

# Custom CSS for better spacing and layout
st.markdown("""
    <style>
    .stForm {background-color: #f0f2f6; padding: 20px; border-radius: 10px;}
    .uploadedImage {border: 2px solid #ccc; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

st.title("Document Information Extraction")

# Create two columns
col1, col2 = st.columns([1, 1])

# --- Left Column --- #
with col1:
    st.subheader("Document Viewer")
    uploaded_file = st.file_uploader("Choose a document file", type=["pdf", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        if st.session_state.last_uploaded_file != uploaded_file:
            st.session_state.last_uploaded_file = uploaded_file
            st.session_state.doc_images = []
            st.session_state.extracted_data = None
            st.session_state.selected_field = None
            st.session_state.highlight_all = False
            st.session_state.current_page = 0

            if uploaded_file.type == "application/pdf":
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    for page in doc:
                        pix = page.get_pixmap()
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        st.session_state.doc_images.append(img)
            else:
                st.session_state.doc_images.append(Image.open(uploaded_file))

    if st.session_state.doc_images:
        st.session_state.current_page = st.number_input(
            "Page", 
            min_value=1, 
            max_value=len(st.session_state.doc_images), 
            value=st.session_state.current_page + 1, 
            step=1
        ) - 1

        img_to_display = st.session_state.doc_images[st.session_state.current_page].copy()
        draw = ImageDraw.Draw(img_to_display)

        fields_to_draw = []
        if st.session_state.get("highlight_all") and st.session_state.extracted_data:
            for key in st.session_state.extracted_data['extracted_fields']:
                fields_to_draw.extend(st.session_state.extracted_data['extracted_fields'][key])
        elif st.session_state.selected_field and st.session_state.extracted_data:
            fields_to_draw = st.session_state.extracted_data['extracted_fields'].get(st.session_state.selected_field, [])

        for field_data in fields_to_draw:
            if field_data and field_data.get('page_number') == st.session_state.current_page + 1:
                bbox = field_data.get('bounding_box')
                if bbox:
                    points = list(zip(bbox[0::2], bbox[1::2]))
                    page_info = st.session_state.extracted_data['pages'][st.session_state.current_page]
                    page_width, page_height = page_info.get('width', img_to_display.size[0]), page_info.get('height', img_to_display.size[1])
                    img_width, img_height = img_to_display.size

                    x_scale = img_width / page_width if page_width > 0 else 1
                    y_scale = img_height / page_height if page_height > 0 else 1
                    
                    scaled_points = [(p[0] * x_scale, p[1] * y_scale) for p in points]
                    draw.polygon(scaled_points, outline="red", width=3)

        st.image(img_to_display, use_column_width=True, caption=f"Page {st.session_state.current_page + 1}")

# --- Right Column --- #
with col2:
    st.subheader("Extracted Information")

    if uploaded_file is not None:
        col_extract, col_highlight = st.columns(2)
        with col_extract:
            if st.button("Extract Information"):
                with st.spinner("Extracting information..."):
                    try:
                        temp_file_path = os.path.join("/app/temp_data", uploaded_file.name)
                        os.makedirs("/app/temp_data", exist_ok=True)
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        files = {'file': (uploaded_file.name, open(temp_file_path, 'rb'), uploaded_file.type)}
                        response = requests.post("http://fastapi_app:8000/extract/", files=files)
                        os.remove(temp_file_path)

                        if response.status_code == 200:
                            data = response.json()
                            content_str = data.get('formatted_response', {}).get('choices', [{}])[0].get('message', {}).get('content', '{}')
                            
                            raw_data = json.loads(content_str)
                            extracted_fields_list = raw_data if isinstance(raw_data, list) else raw_data.get('extracted_fields', [])

                            transformed_fields = {}
                            page_info_from_fields = {}

                            for field in extracted_fields_list:
                                if 'template_field' in field:
                                    key = field['template_field']
                                    if key not in transformed_fields:
                                        transformed_fields[key] = []

                                    x1, y1, x2, y2 = field.get('top_left_x'), field.get('top_left_y'), field.get('bottom_right_x'), field.get('bottom_right_y')
                                    
                                    bbox_polygon = None
                                    if all(v is not None for v in [x1, y1, x2, y2]):
                                        bbox_polygon = [x1, y1, x2, y1, x2, y2, x1, y2]

                                    transformed_fields[key].append({
                                        'value': field.get('predicted_value') if field.get('predicted_value') is not None else field.get('text'),
                                        'bounding_box': bbox_polygon,
                                        'page_number': field.get('page')
                                    })

                                    page_num = field.get('page')
                                    if page_num and page_num not in page_info_from_fields:
                                        page_info_from_fields[page_num] = {
                                            'width': field.get('width'),
                                            'height': field.get('height'),
                                            'unit': field.get('unit')
                                        }
                            
                            num_pages = len(st.session_state.doc_images) if st.session_state.doc_images else 1
                            pages_list = []
                            for i in range(1, num_pages + 1):
                                if i in page_info_from_fields:
                                    pages_list.append(page_info_from_fields[i])
                                elif page_info_from_fields:
                                    pages_list.append(list(page_info_from_fields.values())[0])
                                else:
                                    pages_list.append({'width': 1, 'height': 1, 'unit': 'pixel'})

                            extracted_data = {
                                'extracted_fields': transformed_fields,
                                'pages': pages_list
                            }
                            
                            st.session_state.extracted_data = extracted_data
                            fields_data = extracted_data.get('extracted_fields', {})

                            def get_val(key):
                                field_list = fields_data.get(key, [])
                                if not field_list:
                                    return ''
                                return field_list[0].get('value') or ''

                            st.session_state.origin_company = get_val('OriginCompany')
                            st.session_state.origin_address = get_val('OriginAddress')
                            st.session_state.origin_phone = get_val('OriginPhone')
                            st.session_state.origin_email = get_val('OriginEmail')
                            st.session_state.dest_company = get_val('DestinationCompany')
                            st.session_state.dest_address = get_val('DestinationAddress')
                            st.session_state.dest_phone = get_val('DestinationPhone')
                            st.session_state.dest_email = get_val('DestinationEmail')
                            st.session_state.handling_unit = get_val('HandlingUnitType')
                            st.session_state.quantity = float(get_val('Quantity') or 0)
                            st.session_state.weight = float(get_val('Weight') or 0)
                            st.session_state.weight_unit = get_val('WeightUnit') or 'Lbs'
                            st.session_state.bol_no = get_val('BOLNumber')
                            st.session_state.carrier_pro = get_val('CarrierProNumber')
                            st.session_state.customer_ref = get_val('CustomerReferenceID')
                            st.session_state.nmfc = get_val('NMFC')
                            st.session_state.hazmat = bool(get_val('Hazmat'))
                            st.session_state.no_nmfc = bool(get_val('NoNMFCClassOnBOL'))
                            st.session_state.in_bond = bool(get_val('InBond'))
                            st.session_state.order_id = get_val('OrderID')
                            st.session_state.shipment_id = get_val('ShipmentID')
                            st.session_state.transport_id = get_val('TransportID')
                            
                            st.success("Information extracted successfully!")
                            st.session_state.selected_field = None
                            st.experimental_rerun()
                        else:
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
        with col_highlight:
            if st.session_state.extracted_data:
                button_text = "Clear All Highlights" if st.session_state.get("highlight_all") else "Highlight All Fields"
                if st.button(button_text):
                    st.session_state.highlight_all = not st.session_state.get("highlight_all", False)
                    st.session_state.selected_field = None
                    st.experimental_rerun()

    def create_field(label, session_key, json_tag):
        input_col, button_col = st.columns([3, 1])
        with input_col:
            st.text_input(label, value=str(st.session_state.get(session_key, '')), disabled=True, key=f"txt_{session_key}")
        with button_col:
            if st.button(f"Highlight", key=f"btn_{session_key}"):
                st.session_state.selected_field = json_tag
                st.session_state.highlight_all = False
                if st.session_state.extracted_data:
                    field_data_list = st.session_state.extracted_data['extracted_fields'].get(json_tag)
                    if field_data_list:
                        st.session_state.current_page = field_data_list[0].get('page_number', 1) - 1
                        st.experimental_rerun()

    def highlight_logic(json_tag):
        st.session_state.selected_field = json_tag
        st.session_state.highlight_all = False
        if st.session_state.extracted_data:
            field_data_list = st.session_state.extracted_data['extracted_fields'].get(json_tag)
            if field_data_list:
                st.session_state.current_page = field_data_list[0].get('page_number', 1) - 1
                st.experimental_rerun()

    st.markdown("### Origin Details")
    create_field("Company Name", "origin_company", "OriginCompany")
    create_field("Address", "origin_address", "OriginAddress")
    create_field("Phone", "origin_phone", "OriginPhone")
    create_field("Email", "origin_email", "OriginEmail")

    st.markdown("### Destination Details")
    create_field("Company Name", "dest_company", "DestinationCompany")
    create_field("Address", "dest_address", "DestinationAddress")
    create_field("Phone", "dest_phone", "DestinationPhone")
    create_field("Email", "dest_email", "DestinationEmail")

    st.markdown("### Shipment Details")
    col_ship1, col_ship2 = st.columns(2)
    with col_ship1:
        st.text_input("Handling Unit Type", value=st.session_state.get('handling_unit', ''), disabled=True)
        if st.button("Highlight", key="btn_HandlingUnitType"):
            highlight_logic("HandlingUnitType")
        st.number_input("Quantity", value=float(st.session_state.get('quantity', 0)), min_value=0.0, disabled=True)
        if st.button("Highlight", key="btn_Quantity"):
            highlight_logic("Quantity")
        st.number_input("Weight", value=float(st.session_state.get('weight', 0.0)), min_value=0.0, disabled=True)
        if st.button("Highlight", key="btn_Weight"):
            highlight_logic("Weight")
        st.text_input("Weight Unit", value=st.session_state.get('weight_unit', ''), disabled=True)
        if st.button("Highlight", key="btn_WeightUnit"):
            highlight_logic("WeightUnit")
    with col_ship2:
        st.text_input("BOL No", value=st.session_state.get('bol_no', ''), disabled=True)
        if st.button("Highlight", key="btn_BOLNumber"):
            highlight_logic("BOLNumber")
        st.text_input("Carrier Pro No", value=st.session_state.get('carrier_pro', ''), disabled=True)
        if st.button("Highlight", key="btn_CarrierProNumber"):
            highlight_logic("CarrierProNumber")
        st.text_input("Customer Ref. ID", value=st.session_state.get('customer_ref', ''), disabled=True)
        if st.button("Highlight", key="btn_CustomerReferenceID"):
            highlight_logic("CustomerReferenceID")
        st.text_input("NMFC", value=st.session_state.get('nmfc', ''), disabled=True)
        if st.button("Highlight", key="btn_NMFC"):
            highlight_logic("NMFC")

    st.markdown("### Options")
    col_check1, col_check2, col_check3 = st.columns(3)
    with col_check1:
        st.checkbox("No NMFC Class on BOL", value=st.session_state.get('no_nmfc', False), disabled=True)
    with col_check2:
        st.checkbox("In Bond", value=st.session_state.get('in_bond', False), disabled=True)
    with col_check3:
        st.checkbox("Hazmat", value=st.session_state.get('hazmat', False), disabled=True)

    st.markdown("### Reference Numbers")
    col_id1, col_id2, col_id3 = st.columns(3)
    with col_id1:
        st.text_input("Order ID", value=st.session_state.get('order_id', ''), disabled=True)
        if st.button("Highlight", key="btn_OrderID"):
            highlight_logic("OrderID")
    with col_id2:
        st.text_input("Shipment ID", value=st.session_state.get('shipment_id', ''), disabled=True)
        if st.button("Highlight", key="btn_ShipmentID"):
            highlight_logic("ShipmentID")
    with col_id3:
        st.text_input("Transport ID", value=st.session_state.get('transport_id', ''), disabled=True)
        if st.button("Highlight", key="btn_TransportID"):
            highlight_logic("TransportID")
