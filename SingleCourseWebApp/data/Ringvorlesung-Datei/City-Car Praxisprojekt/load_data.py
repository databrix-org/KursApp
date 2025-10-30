import json
import pandas as pd
import os

def _read_from_local( table: str = None, suffix: str = "csv"):
    '''
    Read the data from local file system
    '''
    file_path = f"{table}.{suffix}"
    return file_path

def read_table(table=None):
    '''
    Read a table from a given database from local file system
    '''
    if not table:
        raise ValueError(f"{table} is not a valid table ") 
    print(f"loading: {table} ")
    file_path = _read_from_local( table=table)
    return pd.read_csv(file_path)

def read_citycar_data():
    '''
    Read all tables from the City_Car_Praxis-Projekt database from local file system
    '''
    database = "City_Car_Praxis-Projekt"
    df_app_downloads = read_table(table="app_downloads")
    df_signups = read_table(table="signups")
    df_ride_requests = read_table(table="ride_requests")
    df_ride_requests["pickup_ts"] = pd.to_datetime(df_ride_requests["pickup_ts"])
    df_ride_requests["dropoff_ts"] = pd.to_datetime(df_ride_requests["dropoff_ts"])
    df_transactions = read_table(table="transactions")
    df_reviews = read_table(table="reviews")
    return df_app_downloads, df_signups, df_ride_requests, df_transactions, df_reviews

def read_sales_code_data():
    '''
    Read all tables from the Sales_Code_Praxis-Projekt database from local file system
    '''
    database = "Sales_Code_Praxis-Projekt"
    h_vehicle = read_table(table="h_vehicle")
    h_sales_code = read_table(table="h_sales_code")
    l_vehicle_sales_code = read_table(table="l_vehicle_sales_code")
    s_vehicle_axle_details = read_table(table="s_vehicle_axle_details")
    vedoc_asa = read_table(table="vedoc_asa")
    return h_vehicle, h_sales_code, l_vehicle_sales_code, s_vehicle_axle_details, vedoc_asa




    