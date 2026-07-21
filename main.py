from pathlib import Path

import pandas as pd

from maps import (zsdkap_new_columns_names, zsdkap_dtypes, vbap_new_columns_names, mb5td_new_columns_names, mb5td_dtypes,
                  zek103_new_columns_names, zek103_dtypes, mb52_dtypes, mb52_new_columns_names, cohv_dtypes,
                  cohv_new_columns_names)
from py_rfc_methods import get_delivery_plants_and_special_stock_indicators_df
from helper_functions import clean_number


SAP_SYSTEM = "P11_SSO"
STORAGE_LOCATIONS = ['0004', '0005']
SUPPLYING_PLANT = '2101'

DATES_RANGE_FILTER = {
    '2101': '2026-07-21', #
    '0301': '2026-07-23', #
    '1201': '2026-07-28', # śr --> wt ; pt --> śr
    '3701': '2026-07-23', # wt --> czw , pt --> śr
}


source_files_dir = Path(r"P:\Technisch\PLANY PRODUKCJI\PLANIŚCI\PP_TOOLS_TEMP_FILES\18_MISSING_STOCK_ORDERS_IDENTIFIER")
output_files_dir = Path(r"P:\Technisch\PLANY PRODUKCJI\PLANIŚCI\PP_TOOLS_TEMP_FILES\18_MISSING_STOCK_ORDERS_IDENTIFIER\output")

# 1. Define filenames in ONE place using a dictionary
source_file_names = {
    "zsdkap": "ZSDKAP.csv",
    "mb5td": "MB5TD.XLSX",
    "zek103": "ZEK103.XLSX",
    "mb52": "MB52.XLSX",
    "cohv": "COHV.XLSX"
}

output_file_names = {
    "df_zar": "df_ZAR.xlsx",
    "df_zri": "df_ZRI.xlsx",
    "df_zrv": "df_ZRV.xlsx",
    "df": "df.xlsx",
}

source_files = {key: source_files_dir / name for key, name in source_file_names.items()}
output_files = {key: output_files_dir / name for key, name in output_file_names.items()}

def determine_shortages(source_files_dict: dict, mrp_controllers_tuple: tuple, product_names_tuple: tuple,
                        output_files_dict: dict, assembly_line: str):

    zsdkap = pd.read_csv(source_files_dict["zsdkap"], dtype=zsdkap_dtypes, sep=';', encoding='MacRoman')

    # Preparing ZSDKAP data
    df = zsdkap.copy()
    df = df.rename(columns=zsdkap_new_columns_names)
    df = df[(df['mrp_controller'].isin(mrp_controllers_tuple)) & (
        df['mat_description'].str.startswith(product_names_tuple))].reset_index(drop=True)

    df['orders_quantity'] = df['orders_quantity'].apply(clean_number)
    df['orders_quantity'] = df['orders_quantity'].astype(int)
    df['customer_order_position'] = df['customer_order_position'].str.zfill(6)
    df['dispatch_date'] = pd.to_datetime(df['dispatch_date'], dayfirst=True, errors='coerce')
    df['creation_date'] = pd.to_datetime(df['creation_date'], dayfirst=True, errors='coerce')

    columns_to_drop = ['Land', 'Postleitzahl', 'Ort', 'Strasse', 'Name', 'UPS', 'Materialgruppe',
                       'Materialgruppenbezeichnung', 'Bestellnummer', 'Versandbedingung', 'Uhrzeiten', 'Kopfnotiz 3',
                       'Kopfnotiz 4', 'Gewicht', 'Volumen', 'Lieferpriorität', 'Route', 'Transportzone WE',
                       'Wskaźnik przetw. specj.', 'ID kontenera', 'Spedition']
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Including delivery plants with PyRFC
    delivery_plants = get_delivery_plants_and_special_stock_indicators_df(SAP_SYSTEM,
                                                                          df['customer_order_number'].tolist(), 1000,
                                                                          100)
    delivery_plants = delivery_plants.rename(columns=vbap_new_columns_names)
    df = pd.merge(df, delivery_plants, how='left', on=['customer_order_number', 'customer_order_position'])
    df.dropna(subset=['delivery_plant'], inplace=True)
    df = df[df['special_stock_indicator'] != 'E']

    zsdkap_customer_orders = df.copy()  # Keep copy for later operations

    df_grouped = df.groupby(['delivery_plant', 'mat_number', 'dispatch_date'], as_index=False).agg({
        'orders_quantity': 'sum',
        'mat_description': 'first',
    })

    sap_list = df['mat_number'].tolist()  # Save list with items for which we have any customer orders - only these
    # items will be the subjects of analysis

    # Get purchase orders data
    zek103_df = pd.read_excel(source_files['zek103'], dtype=zek103_dtypes)
    zek103_df.rename(columns=zek103_new_columns_names, inplace=True)
    zek103_df['po_delivery_date'] = pd.to_datetime(zek103_df['po_delivery_date'], dayfirst=True, errors='coerce')
    zek103_df['po_dispatch_date'] = pd.to_datetime(zek103_df['po_dispatch_date'], dayfirst=True, errors='coerce')
    zek103_df = zek103_df[zek103_df['mat_number'].isin(sap_list)]
    cols_to_drop = ['Szuk. ciąg', 'LFT', 'Best-Mg', 'Bestät. Menge', 'ME', 'Best. Liefdat.']
    zek103_df = zek103_df.drop(columns=[col for col in cols_to_drop if col in zek103_df.columns])

    # Drop purchase orders linked to special customer requirements - as we focus only on stock orders
    zek103_df = zek103_df[zek103_df['customer_order_number'].isna()]

    zek103_2_df = zek103_df.copy()  # I copy ZEK103 df to get quantities which will be dispatched from production plant

    zek103_df = zek103_df.groupby(['po_delivery_date', 'plant', 'mat_number'], as_index=False).agg({
        'po_quantity': 'sum',
        'po_dispatch_date': 'first',
        'mat_description_zek103': 'first',

    })

    # Merge zsdkap with zek103 (purchase orders)
    zsdkap_zek103_merged_df = pd.merge(df_grouped, zek103_df, how='outer',
                                       left_on=['delivery_plant', 'mat_number', 'dispatch_date'],
                                       right_on=['plant', 'mat_number', 'po_delivery_date'])

    zsdkap_zek103_merged_df['delivery_plant'] = zsdkap_zek103_merged_df['delivery_plant'].combine_first(
        zsdkap_zek103_merged_df['plant'])
    zsdkap_zek103_merged_df['dispatch_date'] = zsdkap_zek103_merged_df['dispatch_date'].combine_first(
        zsdkap_zek103_merged_df['po_delivery_date'])
    zsdkap_zek103_merged_df['mat_description'] = zsdkap_zek103_merged_df['mat_description'].combine_first(
        zsdkap_zek103_merged_df['mat_description_zek103'])

    zsdkap_zek103_merged_df['orders_quantity'] = zsdkap_zek103_merged_df['orders_quantity'].fillna(0)
    zsdkap_zek103_merged_df['po_quantity'] = zsdkap_zek103_merged_df['po_quantity'].fillna(0)

    zsdkap_zek103_merged_df = zsdkap_zek103_merged_df.drop(
        columns=['plant', 'po_delivery_date', 'mat_description_zek103'])

    # Get MB52 data (stocks levels)
    mb52_df = pd.read_excel(source_files['mb52'], dtype=mb52_dtypes)
    mb52_df.rename(columns=mb52_new_columns_names, inplace=True)
    mb52_df = mb52_df[(mb52_df['mat_number'].isin(sap_list)) & (mb52_df['customer_order_number'].isna()) & (
        mb52_df['storage_location'].isin(STORAGE_LOCATIONS))]

    mb52_df = mb52_df.groupby(['plant', 'mat_number'], as_index=False).agg({
        'stock_quantity': 'sum',
    })

    # Merge MB52 with zsdkap and zek103
    zsdkap_zek103_mb52_merged_df = pd.merge(zsdkap_zek103_merged_df, mb52_df, left_on=['delivery_plant', 'mat_number'],
                                            right_on=['plant', 'mat_number']).drop(columns=['plant'])

    # Get COHV data (production orders for next days)
    cohv_df = pd.read_excel(source_files['cohv'], dtype=cohv_dtypes)
    cohv_df = cohv_df.rename(columns=cohv_new_columns_names)
    cohv_df['production_date'] = pd.to_datetime(cohv_df['production_date'], dayfirst=True, errors='coerce')
    cohv_df = cohv_df[cohv_df['mat_number'].isin(sap_list)]
    cohv_df = cohv_df.groupby(['production_plant', 'mat_number', 'production_date'], as_index=False).agg({
        'production_quantity': 'sum',
    })

    # Merge COHV data with zsdkap, zek103 and mb52
    zsdkap_zek103_mb52_cohv_merged_df = (
        pd.merge(zsdkap_zek103_mb52_merged_df, cohv_df, left_on=['delivery_plant', 'mat_number', 'dispatch_date'],
                 right_on=['production_plant', 'mat_number', 'production_date'], how='outer'))
    zsdkap_zek103_mb52_cohv_merged_df['dispatch_date'] = zsdkap_zek103_mb52_cohv_merged_df[
        'dispatch_date'].combine_first(zsdkap_zek103_mb52_cohv_merged_df['production_date'])
    zsdkap_zek103_mb52_cohv_merged_df = zsdkap_zek103_mb52_cohv_merged_df.drop(
        columns=['production_date', 'production_plant'])

    zsdkap_zek103_mb52_cohv_merged_df['production_quantity'] = zsdkap_zek103_mb52_cohv_merged_df[
        'production_quantity'].fillna(0)
    zsdkap_zek103_mb52_cohv_merged_df['delivery_plant'] = zsdkap_zek103_mb52_cohv_merged_df['delivery_plant'].fillna(
        SUPPLYING_PLANT)

    # Get mb5td data (goods in transport)
    mb5td_df = pd.read_excel(source_files["mb5td"], dtype=mb5td_dtypes)
    mb5td_df.rename(columns=mb5td_new_columns_names, inplace=True)
    mb5td_df = mb5td_df[mb5td_df['mat_number'].isin(sap_list)]
    mb5td_df = mb5td_df[mb5td_df['special_stock_indicator'].isna()]
    mb5td_df = mb5td_df[['mat_number', 'supplying_plant', 'purchase_order_number', 'purchase_order_position', 'transit_quantity']]

    # Handle purchase orders and transportation quantities issue (goods in transport are not visible as outcome)
    zek103_2_mb5td_merged_df = pd.merge(zek103_2_df, mb5td_df,
                                        on=['mat_number', 'purchase_order_number', 'purchase_order_position'],
                                        how='left')
    zek103_2_mb5td_merged_df['transit_quantity'] = zek103_2_mb5td_merged_df['transit_quantity'].fillna(0)
    zek103_2_mb5td_merged_df['supplying_plant'] = zek103_2_mb5td_merged_df['supplying_plant'].fillna(SUPPLYING_PLANT)
    zek103_2_mb5td_merged_df['dispatched_quantity'] = zek103_2_mb5td_merged_df['po_quantity'] - \
                                                      zek103_2_mb5td_merged_df['transit_quantity']

    dispatches_df = zek103_2_mb5td_merged_df.groupby(['mat_number', 'supplying_plant', 'po_dispatch_date'],
                                                     as_index=False).agg({
        'dispatched_quantity': 'sum',
    })
    dispatches_df = dispatches_df[dispatches_df['dispatched_quantity'] > 0]

    # Create final_df
    final_df = zsdkap_zek103_mb52_cohv_merged_df.copy()

    final_df = (pd.merge(final_df, dispatches_df, left_on=['delivery_plant', 'mat_number', 'dispatch_date'],
                         right_on=['supplying_plant', 'mat_number', 'po_dispatch_date'], suffixes=('', '_disp'),
                         how='outer'))
    final_df['dispatch_date'] = final_df['dispatch_date'].combine_first(final_df['po_dispatch_date_disp'])
    final_df['delivery_plant'] = final_df['delivery_plant'].combine_first(final_df['supplying_plant'])
    final_df = final_df.drop(columns=['po_dispatch_date_disp', 'supplying_plant'])

    final_df['orders_quantity'] = final_df['orders_quantity'].fillna(0)
    final_df['production_quantity'] = final_df['production_quantity'].fillna(0)
    final_df['dispatched_quantity'] = final_df['dispatched_quantity'].fillna(0)
    final_df['po_quantity'] = final_df['po_quantity'].fillna(0)

    # For material description
    final_df['mat_description'] = (
        final_df.groupby(['mat_number', 'delivery_plant'])['mat_description']
        .transform(lambda x: x.ffill().bfill())
    ).infer_objects(copy=False)

    # For stock quantity
    final_df['stock_quantity'] = (
        final_df.groupby(['mat_number', 'delivery_plant'])['stock_quantity']
        .transform(lambda x: x.ffill().bfill())
    ).infer_objects(copy=False)

    # Sort the rows by plant, material number, and date
    final_df = final_df.sort_values(by=['delivery_plant', 'mat_number', 'dispatch_date']).reset_index(drop=True)
    # Calculate the running totals (cumulative sums) for orders and POs within each group
    final_df['cum_orders'] = final_df.groupby(['delivery_plant', 'mat_number'])['orders_quantity'].cumsum()
    final_df['cum_po'] = final_df.groupby(['delivery_plant', 'mat_number'])['po_quantity'].cumsum()
    final_df['cum_prod'] = final_df.groupby(['delivery_plant', 'mat_number'])['production_quantity'].cumsum()
    final_df['cum_dispatches'] = final_df.groupby(['delivery_plant', 'mat_number'])['dispatched_quantity'].cumsum()

    # Compute the final stock left column
    final_df['stock_left'] = final_df['stock_quantity'] + final_df['cum_po'] - final_df['cum_orders'] + final_df['cum_prod'] - final_df['cum_dispatches']

    # Drop the temporary cumulative columns
    final_df = final_df.drop(columns=['cum_orders', 'cum_po', 'cum_prod', 'cum_dispatches'])

    # Map the dictionary to create a temporary "boundary date" series for each row
    # We also convert the dictionary values to datetime on the fly
    boundary_dates = final_df['delivery_plant'].map(DATES_RANGE_FILTER)
    boundary_dates = pd.to_datetime(boundary_dates)

    # Keep rows where dispatch_date is less than or equal to the boundary date.
    # (If a plant isn't in your dictionary, we keep it by using .isna())
    filtered_final_df = final_df[
        (final_df['dispatch_date'] <= boundary_dates) | (boundary_dates.isna())
        ]

    filtered_final_df.to_excel(output_files_dict[f'df_{assembly_line}'], index=False)

    # Get shortages df
    shortages_df = filtered_final_df[filtered_final_df['stock_left'] < 0][
        ['delivery_plant', 'mat_number', 'mat_description', 'dispatch_date', 'stock_left']]

    # Get customer orders numbers from zsdkap
    zsdkap_customer_orders = zsdkap_customer_orders[
        ['delivery_plant', 'mat_number', 'mat_description', 'orders_quantity', 'creation_date', 'dispatch_date',
         'customer_order_number', 'customer_order_position']]

    # Filter the df
    zsdkap_customer_orders = zsdkap_customer_orders.sort_values(
        by=['delivery_plant', 'mat_number', 'creation_date', 'dispatch_date'],
        ascending=[True, True, False, True]).reset_index(drop=True)

    # calculate cumsums within the groups
    zsdkap_customer_orders['cum_orders'] = \
    zsdkap_customer_orders.groupby(['delivery_plant', 'mat_number', 'dispatch_date'])['orders_quantity'].cumsum()

    # Create df with delayed orders
    shortages_temp = shortages_df[['delivery_plant', 'mat_number', 'dispatch_date', 'stock_left']].copy()
    shortages_temp['shortage'] = shortages_temp['stock_left'] * -1
    shortages_temp = shortages_temp.drop(columns=['stock_left'])

    # Keep only rows with shortages
    delayed_orders = pd.merge(
        zsdkap_customer_orders,
        shortages_temp,
        on=['delivery_plant', 'mat_number', 'dispatch_date'],
        how='inner'
    )

    # Mark orders which should be delayed
    delayed_orders['to_be_delayed'] = (
            (delayed_orders['cum_orders'] - delayed_orders['orders_quantity']) < delayed_orders['shortage']
    )

    return shortages_df, delayed_orders


if __name__ == "__main__":
    lines = ["zar", "zrv", "zri"]

    product_names = [
        ('ZAR',),
        ('ZRE_M', 'ZRE M', 'ZRV_M', 'ZRV M'),
        ('ZRI',)
    ]

    mrp_controllers = [
        ('L2B', 'L2R', 'LI2', 'LI4', 'LI7'),
        ('L2E', 'L2V', 'LI1', 'LI3'),
        ('L2I',)
    ]

    for line, names, controllers in zip(lines, product_names, mrp_controllers):
        df1, df2 = determine_shortages(source_files, controllers, names, output_files, line,)
