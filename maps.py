# zsdkap_dtypes = {
#     'Warenempfänger': 'string',
#     'Materialnummer': 'string',
#     'Artikeltext': 'string',
#     'Auftrag': 'string',
#     'Positionsnummer': 'string',
#     'Kontroler MRP': 'string',
#     'Menge': 'string',
#     'WA-Datum': 'datetime64[ns]',
#     'Erfassungsdatum': 'datetime64[ns]',
# }
#
# zsdkap_new_columns_names = {
#     'Warenempfänger': 'receiver',
#     'Materialnummer': 'mat_number',
#     'Artikeltext': 'mat_description',
#     'Auftrag': 'customer_order_number',
#     'Positionsnummer': 'customer_order_position',
#     'Kontroler MRP': 'mrp_controller',
#     'Menge': 'orders_quantity',
#     'WA-Datum': 'dispatch_date',
#     'Erfassungsdatum': 'creation_date'
# }

zsdkap_dtypes = {
    'Odbiorca materia≈Ç√≥w': 'string',
    'Materia≈Ç': 'string',
    'Nazwa': 'string',
    'Dokument sprzeda≈ºy': 'string',
    'Pozycja': 'string',
    'Kontroler MRP': 'string',
    'Ilo≈õƒá zlecenia': 'string',
    # 'WADAT': 'datetime64[ns]',
    # 'Data utworzenia': 'datetime64[ns]',
}

zsdkap_new_columns_names = {
    'Odbiorca materia≈Ç√≥w': 'receiver',
    'Materia≈Ç': 'mat_number',
    'Nazwa': 'mat_description',
    'Dokument sprzeda≈ºy': 'customer_order_number',
    'Pozycja': 'customer_order_position',
    'Kontroler MRP': 'mrp_controller',
    'Ilo≈õƒá zlecenia': 'orders_quantity',
    'WADAT': 'dispatch_date',
    'Data utworzenia': 'creation_date',
}

vbap_new_columns_names = {
    'VBELN': 'customer_order_number',
    'POSNR': 'customer_order_position',
    'WERKS': 'delivery_plant',
    'SOBKZ': 'special_stock_indicator'
}

mb5td_dtypes = {
    'Materiał': 'string',
    'Zakład': 'string',
    'Zakład dostarczający': 'string',
    'Ilość': 'float',
    'Dok.zaopatrz.': 'string',
    'Pozycja': 'string',
}

mb5td_new_columns_names = {
    'Materiał': 'mat_number',
    'Zakład': 'plant',
    'Zakład dostarczający': 'supplying_plant',
    'Ilość': 'transit_quantity',
    'Zapas specjalny': 'special_stock_indicator',
    'Dok.zaopatrz.': 'purchase_order_number',
    'Pozycja': 'purchase_order_position'
}

zek103_dtypes = {
    "Mat": "string",
    "Best-Nr": "string",
    "Pos": "string",
    "Zakł": "string",
    "KdAuf": "string",
    "Poz.": "string",
}

zek103_new_columns_names = {
    "Mat": "mat_number",
    "Best-Nr": "purchase_order_number",
    "Pos": "purchase_order_position",
    "Term. dost.": "po_delivery_date",
    "Zakł": "plant",
    "Off. Mg": "po_quantity", # purchase order quantity
    "KdAuf": "customer_order_number",
    "Poz.": "customer_order_position",
    "Wyd. mat.": "po_dispatch_date", # purchase order dispatch date
    "Benennung": "mat_description_zek103"
}

mb52_dtypes = {
    "Materiał": "string",
    "Skład": "string",
    "Zakład": "string",
    "Dokument SD": "string",
    "Pozycja (SD)": "string",
}

mb52_new_columns_names = {
    "Materiał": "mat_number",
    "Skład": "storage_location",
    "Zakład": "plant",
    "Dokument SD": "customer_order_number",
    "Pozycja (SD)": "customer_order_position",
    "Nieogranicz.wykorz.": "stock_quantity",
}

cohv_dtypes = {
    "Nr materiału": "string",
    "Zlecenie": "string",
    "Zakład": "string",
}

cohv_new_columns_names = {
    "Nr materiału": "mat_number",
    "Krótki tekst materiału": "mat_description",
    "Zlecenie": "production_order_number",
    "Godz. rozp. wg harm.": "production_date",
    "Zakład": "production_plant",
    "Ilość zlecenia (GMEIN)": "production_quantity"
}