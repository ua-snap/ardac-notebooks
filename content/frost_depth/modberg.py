"""
A module to compute Modified Berggren Frost Depth. This module uses Imperial units throughout to align with American engineering conventions.
"""
import numpy as np
import requests
import warnings
warnings.filterwarnings("ignore")

import micropip
micropip.install("pyodide-http")
import pyodide_http
pyodide_http.patch_all()
import pandas as pd

base_url = "http://127.0.0.1:5000/"


def compute_volumetric_latent_heat_of_fusion(dry_ro, wc_pct):
    """Compute amount of heat required to melt all ice or freeze pore water in a unit volume of soil.

    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: water content (percent)
    Returns:
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    """
    # latent heat of fusion for ice is 144 BTU/lb
    # 144 BTU are absorbed for each pound of ice that is melted to water.
    L = 144 * dry_ro * (wc_pct / 100)
    return round(L, 2)


def compute_frozen_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change temperature of a frozen unit volume of soil by 1°F. Specific heat of soil solids is 0.17 (BTU/lb • °F) for most soils.

    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: water content (percent)
    Returns:
        c: volumetric specific heat ((BTUs per cubic foot) • °F)
    """
    c = dry_ro * (0.17 + (0.5 * (wc_pct / 100)))
    return round(c, 2)


def compute_unfrozen_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change the temperature of an unfrozen unit volume of soil by 1°F. The specific heat of soil solids is 0.17 BTU/lb • °F for most soils.

    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        c: volumetric specific heat (BTUs per cubic foot) • °F
    """
    c = dry_ro * (0.17 + (1.0 * (wc_pct / 100)))
    return round(c, 2)


def compute_avg_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change the temperature of an average unit volume of soil by 1°F. The specific heat of soil solids is 0.17 BTU/lb • °F for most soils.

    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        c: volumetric specific heat (BTUs per cubic foot) • °F
    """
    c = dry_ro * (0.17 + (0.75 * (wc_pct / 100)))
    return round(c, 2)


def compute_seasonal_v_s(nFI, d):
    """Compute the v_s parameter. v_s has two possible meanings depending on the problem being studied. In this case, v_s is used for computing a seasonal depth of freeze.

    Args:
        nFI: surface freezing index (°F • days)
        d: length of freezing duration (days)
    Returns:
        v_s: parameter describing intensity of freezing season
    """
    v_s = nFI / d
    return v_s


def get_projected_mat_from_api(lat, lon, model, scenario, year_start, year_end):
    """Query the SNAP Data API for mean annual temperature (2km).

    Args:
        lat: valid SNAP Data API point request latitude
        lon: valid SNAP Data API point request longitude
        model (str): one of [GFDL-CM3, NCAR-CCSM4, MRI-CGCM3, GISS-E2-R, IPSL-CM5A-LR]
        scenario (str): one of [rcp45, rcp60, rcp85]
        year_start (int): start year for summary period, 2007 through 2100
        year_end (int): end year for summary period, 2007 through 2100
    Returns:
        mat_deg_F: mean annual temperature for the given model and scenario, averaged over the summary period
    """
    # make the request
    api_url = f"http://127.0.0.1:5000/temperature/{lat}/{lon}/{year_start}/{year_end}?format=csv"
    df = pd.read_csv(api_url, header=3)
    
    # get the mean of the mean annual temperature values for all years in the time span, for the specific climate future
    mat_deg_C = df.groupby(['model', 'scenario'])['tas'].mean().loc[model][scenario]
    
    # convert from C to F and from array to float
    mat_deg_F = (mat_deg_C * 1.8) + 32
    return float(round(mat_deg_F, 1))


def get_projected_freezing_index_from_api(lat, lon, model, year_start, year_end):
    """Query the SNAP Data API for freezing index.

    Args:
        lat: valid SNAP Data API point request latitude
        lon: valid SNAP Data API point request longitude
        model (str): one of [GFDL-CM3, NCAR-CCSM4]
        year_start (int): start year for summary period, 2007 through 2099
        year_end (int): end year for summary period, 2007 through 2100
    Returns:
        freezing_index_degFdays: annual freezing index for the given RCP 8.5 model, averaged over the year range
    """
    api_url = f"{base_url}degree_days/freezing_index/{lat}/{lon}/{year_start}/{year_end}?format=csv"
    df = pd.read_csv(api_url, header=3)

    # get the mean for the climate future
    freezing_index_degFdays = df.groupby(["model"])["dd"].mean().loc[model]
    return int(round(freezing_index_degFdays))



def compute_multiyear_v_s(mat):
    """Compute the v_s parameter.

    v_s has one of two possible meanings depending on the problem being studied. In this case, v_s is useful in computing multiyear freeze depths that may develop as a long-term change in the heat balance at the ground surface.

    Args:
        mat: mean annual temperature (°F)
    Returns:
         v_s
    """
    v_s = abs(mat - 32)
    return v_s


def compute_v_o(magt):
    """Compute the v_o parameter.

    v_o is the absolute value of the difference between the mean annual temperature BELOW THE GROUND SURFACE and 32 °F.

    Args:
        magt: mean annual temperature below the ground surface (°F)
    Returns:
         v_o
    """
    v_o = abs(magt - 32)
    return v_o


def compute_thermal_ratio(v_o, v_s):
    """Compute the the thermal ratio.

    The thermal ratio is the ratio of two deltas: ground temperature - freezing and surface temperature - freezing.

    Args:
        v_o
        v_s
    Returns:
        thermal_ratio: dimensionless
    """
    thermal_ratio = v_o / v_s
    return round(thermal_ratio, 3)


def compute_fusion_parameter(v_s, c, L):
    """Compute the fusion parameter.

    Args:
        v_s: v_s parameter
        c: volumetric specific heat ((BTUs per cubic foot) • °F)
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    Returns:
        mu: (dimensionless)
    """
    mu = v_s * (c / L)
    return round(mu, 3)


def compute_lambda_coeff(mu, thermal_ratio):
    """Compute the lambda coefficient `lc` (dimensionless).

    Reference: H. P. Aldrich and H. M. Paynter, “Analytical Studies of Freezing and Thawing of Soils,” Arctic Construction and Frost Effects Laboratory, Corps of Engineers, U.S. Army, Boston, MA, First Interim Technical Report 42, Jun. 1953.

    Other implementations:
    `lc2 = 0.707 / (np.sqrt(1 + (mu * (thermal_ratio + 0.5))))`
    `lc_mean = np.mean([lc, lc2])`

    lc (used here) may overestimate frost depth, but is suited to high latitudes
    lc2 may underestimate frost depth, but is suited to lower latitudes
    lc_mean is a middle ground

    Args:
        mu: the fusion parameter (dimensionless)
        thermal_ratio: thermal ratio (dimensionless)
    Returns
        lc: the lambda coefficient value (dimensionless)
    """
    lc = 1.0 / (np.sqrt(1 + (mu * (thermal_ratio + 0.5))))
    return round(lc, 2)


def compute_depth_of_freezing(coeff, k_avg, nFI, L):
    """Compute the depth to which 32 °F temperatures will penetrate into the soil mass.

    Args:
        coeff: the lambda coefficient (dimensionless)
        k_avg: thermal conductivity of soil, average of frozen and unfrozen (BTU/hr • ft • °F)
        nFI: surface freezing index (°F • days)
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    Returns:
        x: frost depth (feet)
    """
    x = coeff * np.sqrt((48 * k_avg * nFI) / L)
    return round(x, 1)


def compute_modified_berggren(
    dry_ro,
    wc_pct,
    d,
    n,
    k_avg,
    lat,
    lon,
    model,
    fi_model,
    scenario,
    year_start,
    year_end,
):
    """
    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: water content (percent)
        d: length of freezing duration (days)
        n: factor to convert air to surface freezing index
        k_avg: thermal conductivity of soil, avg of frozen and unfrozen (BTU/hr • ft • °F)
        lat: valid latitude for SNAP Data API
        lon: valid longitude for SNAP Data API
        model: climate model for mean annual temperature
        fi_model: climate model for freezing index
        scenario: emissions scenario for mean annual temperature
        year_start: start year for average summary of temperature and freezing index
        year_end: end year for average summary of temperature and freezing index
    Returns:
        frost_depth: Modified Bergrenn frost depth (feet)
    """
    mat = get_projected_mat_from_api(lat, lon, model, scenario, year_start, year_end)
    magt = mat  # see assumptions documented in README
    FI = get_projected_freezing_index_from_api(lat, lon, fi_model, year_start, year_end)
    nFI = n * FI

    L = compute_volumetric_latent_heat_of_fusion(dry_ro, wc_pct)
    c = compute_avg_volumetric_specific_heat(dry_ro, wc_pct)
    v_s = compute_seasonal_v_s(nFI, d)
    v_o = compute_v_o(magt)
    thermal_ratio = compute_thermal_ratio(v_o, v_s)
    mu = compute_fusion_parameter(v_s, c, L)
    lambda_coeff = compute_lambda_coeff(mu, thermal_ratio)

    frost_depth = compute_depth_of_freezing(lambda_coeff, k_avg, nFI, L)
    return frost_depth
