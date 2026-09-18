"""
generate_data.py
-----------------
Creates the three CSV datasets used by the dashboard:

  data/districts.csv       -> one row per district (lat/lon + latest snapshot)
  data/daily_trends.csv    -> island-wide daily new/cumulative cases
  data/vaccination.csv     -> island-wide daily vaccination % coverage

NOTE FOR THE STUDENT:
This is SYNTHETIC data generated with a fixed random seed so the dashboard
has something realistic to render out-of-the-box. For your actual
submission you should replace this with a real published dataset, e.g.:
  - Sri Lanka Ministry of Health COVID-19 situation reports
  - HDX (Humanitarian Data Exchange) Sri Lanka COVID-19 dataset
  - Our World in Data (owid) COVID-19 dataset, filtered to Sri Lanka
Keep this script (or document the swap) in your report's
"Data source & preprocessing" section.
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# ---------------------------------------------------------------
# 1. District reference table (25 districts of Sri Lanka)
# ---------------------------------------------------------------
districts = [
    # name, lat, lon, population (thousands), province
    ("Colombo",        6.9271, 79.8612, 2324, "Western"),
    ("Gampaha",        7.0917, 79.9995, 2348, "Western"),
    ("Kalutara",       6.5854, 79.9607, 1221, "Western"),
    ("Kandy",          7.2906, 80.6337, 1418, "Central"),
    ("Matale",         7.4675, 80.6234,  484, "Central"),
    ("Nuwara Eliya",   6.9497, 80.7891,  711, "Central"),
    ("Galle",          6.0535, 80.2210, 1063, "Southern"),
    ("Matara",         5.9549, 80.5550,  814, "Southern"),
    ("Hambantota",     6.1241, 81.1185,  599, "Southern"),
    ("Jaffna",         9.6615, 80.0255,  583, "Northern"),
    ("Kilinochchi",    9.3803, 80.3770,  113, "Northern"),
    ("Mannar",         8.9810, 79.9044,   99, "Northern"),
    ("Vavuniya",       8.7514, 80.4971,  172, "Northern"),
    ("Mullaitivu",     9.2670, 80.8142,   92, "Northern"),
    ("Batticaloa",     7.7170, 81.7000,  526, "Eastern"),
    ("Ampara",         7.2975, 81.6747,  649, "Eastern"),
    ("Trincomalee",    8.5711, 81.2335,  379, "Eastern"),
    ("Kurunegala",     7.4863, 80.3623, 1618, "North Western"),
    ("Puttalam",       8.0362, 79.8283,  762, "North Western"),
    ("Anuradhapura",   8.3114, 80.4037,  860, "North Central"),
    ("Polonnaruwa",    7.9403, 81.0188,  406, "North Central"),
    ("Badulla",        6.9934, 81.0550,  815, "Uva"),
    ("Monaragala",     6.8714, 81.3507,  451, "Uva"),
    ("Ratnapura",      6.6828, 80.3992, 1088, "Sabaragamuwa"),
    ("Kegalle",        7.2513, 80.3464,  814, "Sabaragamuwa"),
]

df_d = pd.DataFrame(districts, columns=["district", "lat", "lon", "population_k", "province"])

# synthetic case load roughly scaled to population + noise, with a few
# "hot" districts (Colombo/Gampaha/Kandy area) to match the reference image
base_rate = rng.uniform(4, 14, size=len(df_d))  # cases per 1000 population
hot = df_d["district"].isin(["Colombo", "Gampaha", "Kalutara", "Kandy", "Kurunegala"])
base_rate = np.where(hot, base_rate * 2.6, base_rate)

raw_confirmed = df_d["population_k"].values * base_rate
# scale so the island-wide total lands close to a realistic mid-pandemic
# snapshot (~17,500 confirmed), matching the scale of the reference dashboard
TARGET_TOTAL = 17530
raw_confirmed = raw_confirmed * (TARGET_TOTAL / raw_confirmed.sum())
confirmed = np.round(raw_confirmed).astype(int)
deaths = np.round(confirmed * rng.uniform(0.004, 0.01, size=len(df_d))).astype(int)
recovered = np.round(confirmed * rng.uniform(0.80, 0.93, size=len(df_d))).astype(int)
active = np.maximum(confirmed - recovered - deaths, 0)

df_d["confirmed"] = confirmed
df_d["active"] = active
df_d["recovered"] = recovered
df_d["deaths"] = deaths
df_d["case_rate_per_1000"] = (df_d["confirmed"] / df_d["population_k"]).round(2)

q_low, q_high = df_d["case_rate_per_1000"].quantile([0.4, 0.75])

def risk_band(rate):
    if rate >= q_high:
        return "High"
    elif rate >= q_low:
        return "Medium"
    return "Low"

df_d["risk_level"] = df_d["case_rate_per_1000"].apply(risk_band)

df_d.to_csv("data/districts.csv", index=False)

# ---------------------------------------------------------------
# 2. Island-wide daily trend (cumulative + new cases) over ~150 days
# ---------------------------------------------------------------
n_days = 150
dates = pd.date_range("2021-03-01", periods=n_days, freq="D")

# logistic-ish growth with daily noise, tapering near the end
t = np.arange(n_days)
growth = TARGET_TOTAL / (1 + np.exp(-0.06 * (t - 95)))    # S-curve to match ~17,530 total
noise = rng.normal(0, 60, size=n_days).cumsum() * 0.15
cumulative = np.clip(growth + noise, 0, None)
cumulative = np.maximum.accumulate(np.round(cumulative)).astype(int)
new_cases = np.diff(cumulative, prepend=0)
new_cases = np.clip(new_cases, 0, None)

df_t = pd.DataFrame({
    "date": dates,
    "new_cases": new_cases,
    "cumulative_cases": cumulative,
})
df_t.to_csv("data/daily_trends.csv", index=False)

# ---------------------------------------------------------------
# 3. Island-wide vaccination progress over the same period
# ---------------------------------------------------------------
first_dose = 100 / (1 + np.exp(-0.05 * (t - 70)))
second_dose = 90 / (1 + np.exp(-0.045 * (t - 95)))
booster = 70 / (1 + np.exp(-0.05 * (t - 125)))

df_v = pd.DataFrame({
    "date": dates,
    "first_dose_pct": np.round(np.clip(first_dose, 0, 100), 1),
    "second_dose_pct": np.round(np.clip(second_dose, 0, 100), 1),
    "booster_pct": np.round(np.clip(booster, 0, 100), 1),
})
df_v.to_csv("data/vaccination.csv", index=False)

print("Generated:")
print(" data/districts.csv     ", df_d.shape)
print(" data/daily_trends.csv  ", df_t.shape)
print(" data/vaccination.csv   ", df_v.shape)
print()
print("Latest totals -> confirmed: {}, active: {}, recovered: {}, deaths: {}".format(
    df_d["confirmed"].sum(), df_d["active"].sum(), df_d["recovered"].sum(), df_d["deaths"].sum()
))
