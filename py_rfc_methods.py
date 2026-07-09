import pandas as pd
from sap_conn import get_conn
from sap_rtab import rfc_read_table

import time


def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


def get_delivery_plants_and_special_stock_indicators_df(sap_system, orders_list, chunk_size=1000, printing_frequency=2):
    vbeln_chunks = list(chunks(orders_list, chunk_size))
    vbap = []

    with get_conn(sap_system) as conn:

        for chunk_num, vbeln_chunk in enumerate(vbeln_chunks, start=1):
            is_printing = chunk_num % printing_frequency == 0
            chunk_start = time.perf_counter()

            vbeln_filter = " OR ".join(
                [f"VBELN = '{m}'" for m in vbeln_chunk]
            )

            vbap_chunk_data = rfc_read_table(
                conn=conn,
                table="VBAP",
                fields=[
                    "VBELN",  # zlecenie klienta
                    "POSNR",  # pozycja
                    "WERKS",  # zakład dostarczający
                    "SOBKZ",  # special stock indicator - "E" for special customer requirements
                ],
                where=f"""
                    {vbeln_filter}
                """,
                # rowcount=1500
            )

            vbap.extend(vbap_chunk_data)

            if is_printing:
                print(
                    f"\nVBELN chunk {chunk_num}/{len(vbeln_chunks)} "
                    f"| docs={len(vbeln_chunk)}"
                    f"\n Chunk time: {time.perf_counter() - chunk_start:.2f} s"
                )

        vbap_df = pd.DataFrame(
            vbap,
            columns=["VBELN", "POSNR", "WERKS", "SOBKZ"]
    )

    vbap_df.drop_duplicates(subset=["VBELN", "POSNR"], keep="first", inplace=True)

    return vbap_df