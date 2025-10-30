import json
import pandas as pd
import os
from pathlib import Path

def _read_from_local(table: str = None, suffix: str = "csv", base_path: str = "."):
    '''
    Read the data from local file system with proper path handling
    '''
    if not table:
        raise ValueError("Table name cannot be None or empty")
    
    file_path = Path(base_path) / f"{table}.{suffix}"
    return str(file_path)

def read_table(table=None, base_path: str = "."):
    '''
    Read a table from local file system with improved error handling
    '''
    if not table:
        raise ValueError(f"'{table}' is not a valid table name") 
    
    file_path = _read_from_local(table=table, base_path=base_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        print(f"Loading: {table} from {file_path}")
        return pd.read_csv(file_path)
    except Exception as e:
        raise Exception(f"Error reading {file_path}: {str(e)}")

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




    