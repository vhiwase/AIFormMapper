mapping = {
    "dock_management": [
        {
            "FormField": "Origin - Company Name",
            "JSONTag": "OriginCompany",
            "DataType": "Text",
            "Notes": "Extract only the company name (e.g., 'Tesla Inc'). Avoid merging with address.",
            "SourcePage": 1
        },
        {
            "FormField": "Origin - Address",
            "JSONTag": "OriginAddress",
            "DataType": "Text",
            "Notes": "Full street, city, state, ZIP, and country in one string (e.g., '6563 Headquarters Dr, Plano, TX 75024, USA').",
            "SourcePage": 1
        },
        {
            "FormField": "Origin - Phone",
            "JSONTag": "OriginPhone",
            "DataType": "Text",
            "Notes": "Format like '+1 (555) 123-4567'. Ignore any phone icons.",
            "SourcePage": 1
        },
        {
            "FormField": "Origin - Email",
            "JSONTag": "OriginEmail",
            "DataType": "Text",
            "Notes": "Extract the plain email address without icons (e.g., 'support@example.com').",
            "SourcePage": 1
        },
        {
            "FormField": "Destination - Company Name",
            "JSONTag": "DestinationCompany",
            "DataType": "Text",
            "Notes": "Only the company name (e.g., 'EAGLE Manufacturer ltd').",
            "SourcePage": 1
        },
        {
            "FormField": "Destination - Address",
            "JSONTag": "DestinationAddress",
            "DataType": "Text",
            "Notes": "Full street, city, state, ZIP, and country in one string.",
            "SourcePage": 1
        },
        {
            "FormField": "Destination - Phone",
            "JSONTag": "DestinationPhone",
            "DataType": "Text",
            "Notes": "Same formatting as OriginPhone (e.g., '+1 (555) 123-4567').",
            "SourcePage": 1
        },
        {
            "FormField": "Destination - Email",
            "JSONTag": "DestinationEmail",
            "DataType": "Text",
            "Notes": "Plain email value only (e.g., 'support@example.com').",
            "SourcePage": 1
        },
        {
            "FormField": "Handling Unit Type",
            "JSONTag": "HandlingUnitType",
            "DataType": "Text",
            "Notes": "Dropdown value like 'Pallet', 'Crate', etc.",
            "SourcePage": 1
        },
        {
            "FormField": "Quantity",
            "JSONTag": "Quantity",
            "DataType": "Number",
            "Notes": "Numeric only (e.g., 3). No units or symbols.",
            "SourcePage": 1
        },
        {
            "FormField": "Weight Unit",
            "JSONTag": "WeightUnit",
            "DataType": "Text",
            "Notes": "Dropdown text value (e.g., 'Lbs').",
            "SourcePage": 1
        },
        {
            "FormField": "Weight Value",
            "JSONTag": "Weight",
            "DataType": "Number",
            "Notes": "Numeric only (e.g., 3200). No commas or unit suffix.",
            "SourcePage": 1
        },
        {
            "FormField": "BOL No",
            "JSONTag": "BOLNumber",
            "DataType": "Text",
            "Notes": "Capture as-is (e.g., '123456588'). Can be numeric or alphanumeric.",
            "SourcePage": 1
        },
        {
            "FormField": "Carrier Pro No",
            "JSONTag": "CarrierProNumber",
            "DataType": "Text",
            "Notes": "Capture raw text (e.g., '123345854').",
            "SourcePage": 1
        },
        {
            "FormField": "Customer Ref. ID",
            "JSONTag": "CustomerReferenceID",
            "DataType": "Text",
            "Notes": "Capture as-is (e.g., '5754122254').",
            "SourcePage": 1
        },
        {
            "FormField": "NMFC",
            "JSONTag": "NMFC",
            "DataType": "Text",
            "Notes": "Typically numeric or short text code (e.g., '150'). Treat as text.",
            "SourcePage": 1
        },
        {
            "FormField": "No NMFC Class on BOL",
            "JSONTag": "NoNMFCClassOnBOL",
            "DataType": "Checkbox",
            "Notes": "Return {'selected': True} if checked, {'selected': False} if unchecked.",
            "SourcePage": 1
        },
        {
            "FormField": "In Bond",
            "JSONTag": "InBond",
            "DataType": "Checkbox",
            "Notes": "Return {'selected': True} if checked, {'selected': False} if unchecked.",
            "SourcePage": 1
        },
        {
            "FormField": "Hazmat",
            "JSONTag": "Hazmat",
            "DataType": "Checkbox",
            "Notes": "Return {'selected': True} if checked, {'selected': False} if unchecked.",
            "SourcePage": 1
        },
        {
            "FormField": "Order ID",
            "JSONTag": "OrderID",
            "DataType": "Text",
            "Notes": "E.g., 1539964. Numeric text—no prefix.",
            "SourcePage": 1
        },
        {
            "FormField": "Shipment ID",
            "JSONTag": "ShipmentID",
            "DataType": "Text",
            "Notes": "Starts with 'S' consistently (e.g., 'S1539964'). Always capture the full alphanumeric.",
            "SourcePage": 1
        },
        {
            "FormField": "Transport ID",
            "JSONTag": "TransportID",
            "DataType": "Text",
            "Notes": "Starts with 'T' (e.g., 'T1254247'). Do not strip the letter. Capture the full alphanumeric.",
            "SourcePage": 1
        }
    ]
}
