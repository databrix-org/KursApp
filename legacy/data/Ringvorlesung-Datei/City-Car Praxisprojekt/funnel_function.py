import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
import os

def _ride_request_details_filter(df_ride_requests: pd.DataFrame = None,
                                 df_signups_detail: pd.DataFrame = None,
                                 on_column: str = None,
                                 filter_string: str = None):
    df_ride_requests_details = pd.merge(df_ride_requests, df_signups_detail, how="left", left_on="user_id",
                                        right_on="user_id")
    df_ride_requests_details = df_ride_requests_details[df_ride_requests_details[on_column] == filter_string]
    return df_ride_requests_details


def _common_stages(funnel: dict = None, df_ride_requests_details: pd.DataFrame = None,
                   df_transactions: pd.DataFrame = None, df_reviews: pd.DataFrame = None):
    funnel["ride_request"] = df_ride_requests_details.drop_duplicates(["user_id"])["user_id"].count()

    df_accepted_rides = df_ride_requests_details[df_ride_requests_details["accept_ts"].notna()]
    funnel["ride_accepted"] = df_accepted_rides.drop_duplicates(["user_id"])["user_id"].count()

    df_ride_completed = df_ride_requests_details[df_ride_requests_details["dropoff_ts"].notna()]
    funnel["ride_completed"] = df_ride_completed.drop_duplicates(["user_id"])["user_id"].count()

    df_ride_completed_details = pd.merge(df_ride_completed, df_transactions, how="left", left_on="ride_id",
                                         right_on="ride_id")
    funnel["transactions"] = \
        df_ride_completed_details[df_ride_completed_details["charge_status"] == "Approved"].drop_duplicates(
            ["user_id"])[
            "user_id"].count()

    df_ride_completed_details = pd.merge(df_ride_completed_details, df_reviews, how="left", left_on="ride_id",
                                         right_on="ride_id")
    funnel["reviews"] = \
        df_ride_completed_details[df_ride_completed_details["review_id"].notna()].drop_duplicates(["user_id_x"])[
            "user_id_x"].count()
    return funnel


def _percentage(df_funnel: pd.DataFrame = None) -> pd.DataFrame:
    df_funnel["percentage top"] = df_funnel["values"].div(df_funnel["values"][0] / 100).astype(int).astype(str)
    df_funnel["percentage previous"] = df_funnel["values"].div(df_funnel["values"].shift() / 100).fillna(100).astype(
        int).astype(str)
    df_funnel["percentage"] = df_funnel["percentage top"].str.cat(df_funnel["percentage previous"], sep="% / ").str.cat(
        ["%"] * len(df_funnel))
    return df_funnel


def _to_dataframe(funnel: dict = None, on_column: str = None, filter_string: str = None) -> pd.DataFrame:
    funnel = {"stages": funnel.keys(), "values": funnel.values()}
    df_funnel = pd.DataFrame(data=funnel)
    if on_column and filter_string:
        df_funnel[on_column] = filter_string
    return df_funnel
