import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
from load_data import read_table

def daily_rides():
    df_ride_requests = read_table("ride_requests")
    df_ride_requests["request_ts"] = pd.to_datetime(df_ride_requests["request_ts"])
    daily_counts = df_ride_requests.groupby(df_ride_requests["request_ts"].dt.date).count()
    daily_counts.rename(
        columns={"request_ts": "rides requested", "cancel_ts": "rides canceled", "dropoff_ts": "rides completed"},
        inplace=True)
    return daily_counts[["rides requested", "rides canceled", "rides completed"]]


def hourly_rides():
    df_ride_requests = read_table("ride_requests")
    df_ride_requests["request_ts"] = pd.to_datetime(df_ride_requests["request_ts"])
    hourly_counts = df_ride_requests.groupby(df_ride_requests["request_ts"].dt.hour).count()
    hourly_counts.rename(
        columns={"request_ts": "rides requested", "cancel_ts": "rides canceled", "dropoff_ts": "rides completed"},
        inplace=True)
    return hourly_counts
