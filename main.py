"""
main.py
-------
Sri Lanka COVID-19 Interactive Geo Dashboard
Coursework 1 (Individual) - HNDDSFT-M0104 Data Visualization
Pool 2: Geospatial Visualization with Bokeh

Run with:
    bokeh serve --show covid_dashboard

Folder layout expected:
    covid_dashboard/
        main.py                 <- this file
        data/districts.csv
        data/daily_trends.csv
        data/vaccination.csv
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, HoverTool, Div, Select, Slider, CheckboxButtonGroup,
    LinearColorMapper, ColorBar, NumeralTickFormatter, DatetimeTickFormatter,
    Range1d, Wedge, Legend, LegendItem, TapTool, CustomJS, LinearAxis
)
from bokeh.plotting import figure
from bokeh.palettes import Turbo256
from bokeh.transform import cumsum

# ------------------------------------------------------------------
# THEME (matches the reference dark dashboard: navy background,
# red / orange / green / dark stat cards, neon accent lines)
# ------------------------------------------------------------------
BG          = "#0b1330"
PANEL_BG    = "#111a3d"
GRID_COLOR  = "#22305f"
TEXT_COLOR  = "#e6ebff"
MUTED_TEXT  = "#9aa4c7"
RED         = "#e5384d"
ORANGE      = "#f5a623"
GREEN       = "#28c76f"
BLACK_CARD  = "#05070f"
GOLD        = "#f0b90b"
TEAL        = "#3ddc97"
BLUE        = "#4da3ff"

RISK_COLORS = {"Low": GREEN, "Medium": ORANGE, "High": RED}

DATA_DIR = Path(__file__).parent / "data"

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
districts_df = pd.read_csv(DATA_DIR / "districts.csv")
trends_df = pd.read_csv(DATA_DIR / "daily_trends.csv", parse_dates=["date"])
vacc_df = pd.read_csv(DATA_DIR / "vaccination.csv", parse_dates=["date"])


def lonlat_to_webmercator(lon, lat):
    """Project plain lon/lat degrees to Web Mercator (EPSG:3857) so the
    points line up with Bokeh/CARTO tile providers."""
    k = 6378137.0
    x = lon * (k * math.pi / 180.0)
    y = np.log(np.tan((90 + lat) * math.pi / 360.0)) * k
    return x, y


mx, my = lonlat_to_webmercator(districts_df["lon"].values, districts_df["lat"].values)
districts_df["x"] = mx
districts_df["y"] = my

# marker radius scaled by confirmed cases (sqrt scale keeps small
# districts visible while big ones don't swamp the map, same idea as
# the bubble sizing in the reference dashboard)
size_min, size_max = 12, 42
c = districts_df["confirmed"].values
districts_df["marker_size"] = size_min + (np.sqrt(c) / np.sqrt(c.max())) * (size_max - size_min)
districts_df["color"] = districts_df["risk_level"].map(RISK_COLORS)

full_source = ColumnDataSource(districts_df)
map_source = ColumnDataSource(districts_df)  # filtered copy driven by controls

# ------------------------------------------------------------------
# TOP STAT CARDS  (Total confirmed / active / recovered / deaths)
# ------------------------------------------------------------------
def stat_card(label, value, color, text_color="#ffffff"):
    return Div(
        text=f"""
        <div style="background:{color}22;border:2px solid {color};border-radius:14px;
                    padding:14px 10px;text-align:center;height:92px;
                    display:flex;flex-direction:column;justify-content:center;">
            <div style="color:{MUTED_TEXT};font-size:13px;letter-spacing:1px;
                        font-family:Arial, sans-serif;">{label}</div>
            <div style="color:{text_color};font-size:30px;font-weight:800;
                        font-family:Arial, sans-serif;margin-top:4px;">{value:,}</div>
        </div>
        """,
        sizing_mode="stretch_width",
    )


total_confirmed = int(districts_df["confirmed"].sum())
total_active = int(districts_df["active"].sum())
total_recovered = int(districts_df["recovered"].sum())
total_deaths = int(districts_df["deaths"].sum())

card_confirmed = stat_card("TOTAL CONFIRMED CASES", total_confirmed, RED)
card_active = stat_card("ACTIVE CASES", total_active, ORANGE)
card_recovered = stat_card("TOTAL RECOVERED", total_recovered, GREEN)
card_deaths = stat_card("TOTAL DEATHS", total_deaths, "#666666", text_color="#ffffff")

header = Div(text=f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:6px 4px 14px 4px;">
  <div style="color:{TEXT_COLOR};font-family:Arial, sans-serif;font-size:26px;font-weight:800;
              letter-spacing:1px;">
    🇱🇰 SRI LANKA COVID-19 STATUS
  </div>
  <div style="color:{MUTED_TEXT};font-family:Arial, sans-serif;font-size:13px;text-align:right;">
    MINISTRY OF HEALTH<br/><span style="font-size:11px;">(synthetic demo data)</span>
  </div>
</div>
""", sizing_mode="stretch_width")

# ------------------------------------------------------------------
# GEO MAP  (bubble / "choropleth-style" markers over a dark basemap)
# ------------------------------------------------------------------
map_fig = figure(
    title="DISTRICT CASE MAP",
    x_axis_type="mercator", y_axis_type="mercator",
    tools="pan,wheel_zoom,reset,tap,save",
    active_scroll="wheel_zoom",
    background_fill_color=PANEL_BG,
    border_fill_color=PANEL_BG,
    height=430, sizing_mode="stretch_width",
)
map_fig.title.text_color = TEXT_COLOR
map_fig.title.text_font_size = "13pt"
map_fig.grid.grid_line_color = None
map_fig.axis.visible = False
map_fig.outline_line_color = GRID_COLOR

try:
    from bokeh.models import WMTSTileSource
    dark_tiles = WMTSTileSource(
        url="https://a.basemaps.cartocdn.com/dark_all/{Z}/{X}/{Y}.png",
        attribution=(
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
            'contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        ),
    )
    map_fig.add_tile(dark_tiles)
except Exception:
    pass  # if tiles can't be fetched (offline), the bubbles still render fine

bubbles = map_fig.circle(
    x="x", y="y", size="marker_size", source=map_source,
    fill_color="color", fill_alpha=0.55, line_color="color", line_width=2,
)

map_hover = HoverTool(
    renderers=[bubbles],
    tooltips="""
    <div style="font-family:Arial, sans-serif;font-size:12px;">
        <div style="font-weight:bold;font-size:13px;color:#222;">@district</div>
        <div>Confirmed: <b>@confirmed{0,0}</b></div>
        <div>Active: <b>@active{0,0}</b></div>
        <div>Recovered: <b>@recovered{0,0}</b></div>
        <div>Deaths: <b>@deaths{0,0}</b></div>
        <div>Rate / 1,000 pop: <b>@case_rate_per_1000</b></div>
        <div>Risk level: <b>@risk_level</b></div>
    </div>
    """,
)
map_fig.add_tools(map_hover)

# legend for risk colors (manual, since fill color is a data column)
legend_html = " &nbsp; ".join(
    f'<span style="color:{col};font-weight:bold;">&#9679;</span> '
    f'<span style="color:{TEXT_COLOR};font-size:12px;">{lvl}</span>'
    for lvl, col in RISK_COLORS.items()
)
map_legend_div = Div(text=f'<div style="text-align:right;">{legend_html}</div>',
                      sizing_mode="stretch_width")

# ------------------------------------------------------------------
# CONTROLS: search / filter by district & risk level
# ------------------------------------------------------------------
district_options = ["All Districts"] + sorted(districts_df["district"].tolist())
district_select = Select(title="Search district", value="All Districts",
                          options=district_options, width=200)

risk_group = CheckboxButtonGroup(
    labels=["Low", "Medium", "High"], active=[0, 1, 2], width=260
)
risk_group_title = Div(text=f'<div style="color:{MUTED_TEXT};font-size:12px;'
                             f'font-family:Arial, sans-serif;margin-bottom:2px;">'
                             f'Filter by risk level</div>')


def update_map(attr, old, new):
    df = districts_df.copy()

    active_idx = risk_group.active
    allowed_risk = [risk_group.labels[i] for i in active_idx]
    df = df[df["risk_level"].isin(allowed_risk)]

    if district_select.value != "All Districts":
        df = df[df["district"] == district_select.value]

    map_source.data = ColumnDataSource.from_df(df)

    if len(df) == 1:
        map_fig.x_range = Range1d(df["x"].iloc[0] - 60000, df["x"].iloc[0] + 60000)
        map_fig.y_range = Range1d(df["y"].iloc[0] - 60000, df["y"].iloc[0] + 60000)
    else:
        map_fig.x_range = Range1d(mx.min() - 40000, mx.max() + 40000)
        map_fig.y_range = Range1d(my.min() - 40000, my.max() + 40000)


district_select.on_change("value", update_map)
risk_group.on_change("active", update_map)
update_map(None, None, None)  # set initial view

# ------------------------------------------------------------------
# DAILY CASE TRENDS  (line chart + time slider, like the reference)
# ------------------------------------------------------------------
trends_df["zero"] = 0
trends_source = ColumnDataSource(trends_df)
window_source = ColumnDataSource(trends_df)  # sliced by the slider

trend_fig = figure(
    title="DAILY CASE TRENDS", x_axis_type="datetime",
    height=260, sizing_mode="stretch_width",
    background_fill_color=PANEL_BG, border_fill_color=PANEL_BG,
    tools="pan,wheel_zoom,reset,save", toolbar_location="above",
)
trend_fig.title.text_color = TEXT_COLOR
trend_fig.title.text_font_size = "13pt"
trend_fig.grid.grid_line_color = GRID_COLOR
trend_fig.grid.grid_line_alpha = 0.3
trend_fig.xaxis.major_label_text_color = MUTED_TEXT
trend_fig.yaxis.major_label_text_color = MUTED_TEXT
trend_fig.outline_line_color = GRID_COLOR
trend_fig.xaxis.formatter = DatetimeTickFormatter(days="%d %b", months="%b %Y")

trend_fig.varea(x="date", y1="zero", y2="new_cases", source=window_source,
                 fill_color=RED, fill_alpha=0.18)
new_line = trend_fig.line(x="date", y="new_cases", source=window_source,
                           line_color=RED, line_width=2, legend_label="New cases / day")

# cumulative cases live on their own scale (thousands vs. hundreds/day),
# so give them a secondary y-axis on the right rather than squashing
# the daily-new-cases line flat
trend_fig.extra_y_ranges = {
    "cum": Range1d(start=0, end=trends_df["cumulative_cases"].max() * 1.1)
}
trend_fig.add_layout(
    LinearAxis(y_range_name="cum", axis_label="Cumulative",
               major_label_text_color=MUTED_TEXT),
    "right",
)
cum_line = trend_fig.line(x="date", y="cumulative_cases", source=window_source,
                           line_color=ORANGE, line_width=2, legend_label="Cumulative cases",
                           y_range_name="cum")
trend_fig.legend.location = "top_left"
trend_fig.legend.background_fill_color = PANEL_BG
trend_fig.legend.label_text_color = TEXT_COLOR
trend_fig.legend.border_line_color = None
trend_fig.legend.click_policy = "hide"

trend_fig.add_tools(HoverTool(
    renderers=[new_line],
    tooltips=[("Date", "@date{%F}"), ("New cases", "@new_cases{0,0}"),
              ("Cumulative", "@cumulative_cases{0,0}")],
    formatters={"@date": "datetime"},
    mode="vline",
))

date_min, date_max = trends_df["date"].min(), trends_df["date"].max()
range_slider_start = trends_df["date"].min()

time_slider = Slider(
    start=0, end=len(trends_df) - 1, value=len(trends_df) - 1, step=1,
    title="Show data up to day #", width=400,
)


def update_trend_window(attr, old, new):
    day_idx = time_slider.value
    sliced = trends_df.iloc[: day_idx + 1]
    window_source.data = ColumnDataSource.from_df(sliced)

    vsliced = vacc_df.iloc[: day_idx + 1]
    vacc_window_source.data = ColumnDataSource.from_df(vsliced)

    # update the coverage donuts to reflect the selected day
    latest = vacc_df.iloc[day_idx]
    update_donuts(latest["first_dose_pct"], latest["second_dose_pct"], latest["booster_pct"])


time_slider.on_change("value", update_trend_window)

slider_label = Div(text=f'<div style="color:{MUTED_TEXT};font-size:12px;'
                         f'font-family:Arial, sans-serif;">Drag to replay the outbreak day-by-day '
                         f'(also updates vaccination charts below)</div>')

# ------------------------------------------------------------------
# VACCINATION PROGRESS  (line chart)
# ------------------------------------------------------------------
vacc_window_source = ColumnDataSource(vacc_df)

vacc_fig = figure(
    title="VACCINATION PROGRESS", x_axis_type="datetime",
    height=260, sizing_mode="stretch_width",
    background_fill_color=PANEL_BG, border_fill_color=PANEL_BG,
    tools="pan,wheel_zoom,reset,save", toolbar_location="above",
)
vacc_fig.title.text_color = TEXT_COLOR
vacc_fig.title.text_font_size = "13pt"
vacc_fig.grid.grid_line_color = GRID_COLOR
vacc_fig.grid.grid_line_alpha = 0.3
vacc_fig.xaxis.major_label_text_color = MUTED_TEXT
vacc_fig.yaxis.major_label_text_color = MUTED_TEXT
vacc_fig.outline_line_color = GRID_COLOR
vacc_fig.xaxis.formatter = DatetimeTickFormatter(days="%d %b", months="%b %Y")
vacc_fig.y_range = Range1d(0, 105)
vacc_fig.yaxis.formatter = NumeralTickFormatter(format="0'%'")

l1 = vacc_fig.line(x="date", y="first_dose_pct", source=vacc_window_source,
                    line_color=GOLD, line_width=2, legend_label="1st dose")
l2 = vacc_fig.line(x="date", y="second_dose_pct", source=vacc_window_source,
                    line_color=TEAL, line_width=2, legend_label="2nd dose")
l3 = vacc_fig.line(x="date", y="booster_pct", source=vacc_window_source,
                    line_color=BLUE, line_width=2, legend_label="Booster")
vacc_fig.legend.location = "top_left"
vacc_fig.legend.background_fill_color = PANEL_BG
vacc_fig.legend.label_text_color = TEXT_COLOR
vacc_fig.legend.border_line_color = None
vacc_fig.legend.click_policy = "hide"

vacc_fig.add_tools(HoverTool(
    renderers=[l1],
    tooltips=[("Date", "@date{%F}"), ("1st dose", "@first_dose_pct{0.0}%"),
              ("2nd dose", "@second_dose_pct{0.0}%"), ("Booster", "@booster_pct{0.0}%")],
    formatters={"@date": "datetime"},
    mode="vline",
))

# ------------------------------------------------------------------
# VACCINATION COVERAGE  (two donut / wedge charts, like the reference)
# ------------------------------------------------------------------
def make_donut_source(pct, color):
    pct = float(pct)
    data = pd.DataFrame({
        "value": [pct, 100 - pct],
        "color": [color, "#28304f"],
        "label": ["Completed", "Remaining"],
    })
    data["angle"] = data["value"] / data["value"].sum() * 2 * math.pi
    return ColumnDataSource(data)


def donut_figure(title):
    fig = figure(
        title=title, height=210, width=210, toolbar_location=None,
        background_fill_color=PANEL_BG, border_fill_color=PANEL_BG,
        x_range=Range1d(-1.3, 1.3), y_range=Range1d(-1.3, 1.3),
        tools="",
    )
    fig.title.text_color = TEXT_COLOR
    fig.title.text_font_size = "11pt"
    fig.title.align = "center"
    fig.axis.visible = False
    fig.grid.grid_line_color = None
    fig.outline_line_color = None
    return fig


first_dose_final = vacc_df["first_dose_pct"].iloc[-1]
second_dose_final = vacc_df["second_dose_pct"].iloc[-1]

donut1_source = make_donut_source(first_dose_final, GOLD)
donut2_source = make_donut_source(second_dose_final, TEAL)

donut1_fig = donut_figure("1st DOSE COVERAGE")
donut2_fig = donut_figure("2nd DOSE COVERAGE")

donut1_wedge = donut1_fig.annular_wedge(
    x=0, y=0, inner_radius=0.55, outer_radius=0.9,
    start_angle=cumsum("angle", include_zero=True), end_angle=cumsum("angle"),
    fill_color="color", line_color=PANEL_BG, source=donut1_source,
)
donut2_wedge = donut2_fig.annular_wedge(
    x=0, y=0, inner_radius=0.55, outer_radius=0.9,
    start_angle=cumsum("angle", include_zero=True), end_angle=cumsum("angle"),
    fill_color="color", line_color=PANEL_BG, source=donut2_source,
)

donut1_label = Div(text=f'<div style="text-align:center;color:{GOLD};font-size:22px;'
                         f'font-weight:800;font-family:Arial, sans-serif;margin-top:-140px;">'
                         f'{first_dose_final:.0f}%</div>', width=210)
donut2_label = Div(text=f'<div style="text-align:center;color:{TEAL};font-size:22px;'
                         f'font-weight:800;font-family:Arial, sans-serif;margin-top:-140px;">'
                         f'{second_dose_final:.0f}%</div>', width=210)


def update_donuts(pct1, pct2, pct3):
    d1 = make_donut_source(pct1, GOLD).data
    d2 = make_donut_source(pct2, TEAL).data
    donut1_source.data = d1
    donut2_source.data = d2
    donut1_label.text = (f'<div style="text-align:center;color:{GOLD};font-size:22px;'
                          f'font-weight:800;font-family:Arial, sans-serif;margin-top:-140px;">'
                          f'{pct1:.0f}%</div>')
    donut2_label.text = (f'<div style="text-align:center;color:{TEAL};font-size:22px;'
                          f'font-weight:800;font-family:Arial, sans-serif;margin-top:-140px;">'
                          f'{pct2:.0f}%</div>')


# ------------------------------------------------------------------
# LAYOUT
# ------------------------------------------------------------------
stat_row = row(card_confirmed, card_active, card_recovered, card_deaths,
                sizing_mode="stretch_width", spacing=14)

controls_row = row(district_select, column(risk_group_title, risk_group),
                    sizing_mode="fixed", spacing=24)

map_panel = column(
    row(controls_row, map_legend_div, sizing_mode="stretch_width"),
    map_fig,
    sizing_mode="stretch_width",
)

trend_panel = column(
    trend_fig, row(time_slider, slider_label, sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

donut_panel = column(
    Div(text=f'<div style="color:{TEXT_COLOR};font-family:Arial, sans-serif;'
             f'font-size:13pt;font-weight:700;margin-bottom:4px;">VACCINATION COVERAGE</div>'),
    row(column(donut1_fig, donut1_label), column(donut2_fig, donut2_label),
        sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

bottom_row = row(
    column(vacc_fig, sizing_mode="stretch_width"),
    column(donut_panel, sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

dashboard = column(
    header,
    stat_row,
    map_panel,
    trend_panel,
    bottom_row,
    sizing_mode="stretch_width",
)

curdoc().add_root(dashboard)
curdoc().title = "Sri Lanka COVID-19 Dashboard"
