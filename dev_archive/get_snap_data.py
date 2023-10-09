import pandas as pd
from pyodide.http import open_url

base_url = "http://development.earthmaps.io/"


def url_contents_to_df(url, header_rows):
    url_contents = open_url(url)
    df = pd.read_csv(url_contents, header=header_rows)
    return df


def get_freezing_index(lat, lon):
    fi_url = f"{base_url}degree_days/freezing_index/{lat}/{lon}?format=csv"
    fi_df = url_contents_to_df(fi_url, 2)
    return fi_df


def get_thawing_index(lat, lon):
    ti_url = f"{base_url}degree_days/thawing_index/{lat}/{lon}?format=csv"
    ti_df = url_contents_to_df(ti_url, 2)
    return ti_df


def get_precip_frequency(lat, lon):
    pf_url = f"{base_url}precipitation/frequency/point/{lat}/{lon}?format=csv"
    pf_df = url_contents_to_df(pf_url, 9)
    return pf_df


def get_mean_annual_temp(lat, lon):
    mat_url = f"{base_url}temperature/{lat}/{lon}?format=csv"
    mat_df = url_contents_to_df(mat_url, 3)
    return mat_df
