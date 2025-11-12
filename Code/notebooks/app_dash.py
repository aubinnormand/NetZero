# app_dash.py
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import geopandas as gpd
import json
import numpy as np
import sys
from pathlib import Path
import importlib
import ipynbname 
from datetime import datetime

base_path = Path("C:/Users/Aubin/Documents/NetZero")
code_path = base_path/"Code"
# Ajouter le dossier scripts au path
scripts_path = code_path  / "scripts"
sys.path.append(str(scripts_path.resolve()))

import data_utils  # importe le module une première fois

# Après avoir modifié data_utils.py
importlib.reload(data_utils)

# Maintenant tu peux accéder aux fonctions mises à jour
from data_utils import import_data_raw, import_data_sig, melt_long_format, clean_year_column, save_long_dataframe, concat_intermediate_files



# --- Fonction symlog ---
def symlog(x):
    """Logarithme symétrique : log10(|x|+1) * signe(x)"""
    if pd.isna(x):
        return None
    return np.sign(x) * np.log10(abs(x) + 1)

# --- Normalisations ---
norm_map = {
    'No norm': ('Value', 'Unit'),
    'Area': ('Value_norm_area', 'Unit_norm_area'),
    'Population': ('Value_norm_population', 'Unit_norm_population'),
    'Hab/km2': ('Value_norm_densite', 'Unit_norm_densite'),
    'PPP': ('Value_norm_ppp', 'Unit_norm_ppp'),
    'GDP': ('Value_norm_gdp', 'Unit_norm_gdp'),
    'PPP/hab': ('Value_norm_ppp_hab', 'Unit_norm_ppp_hab'),
    'GDP/hab': ('Value_norm_gdp_hab', 'Unit_norm_gdp_hab')
}

# --- Chargement des données ---

filename="data_final_all_norm.csv"
filepath= base_path/ "Data" / 'data_final' / filename
df_data = pd.read_csv(filepath)

gdf_world=import_data_sig('world.geojson',base_path)
def simplify_geom(geom, tol=0.1):
    if geom is None:
        return None
    if geom.geom_type == 'Polygon':
        return geom.simplify(tol, preserve_topology=True)
    elif geom.geom_type == 'MultiPolygon':
        return type(geom)([poly.simplify(tol, preserve_topology=True) for poly in geom.geoms])
    return geom
    
gdf_world = gdf_world[gdf_world['Country_code'].notna()].copy()
gdf_world['geometry'] = gdf_world['geometry'].apply(lambda g: simplify_geom(g, tol=0.1))
gdf_world.head(10)


df_data['Year'] = df_data['Year'].astype(int)

# --- Initialiser Dash ---
app = dash.Dash(__name__)
app.title = "Carte interactive mondiale"

# --- Layout ---
app.layout = html.Div([
    html.Div([
        html.H1("Carte mondiale interactive", style={'marginBottom': '10px'}),

        html.Div([
            html.Label("Choisir l'indicateur :"),
            dcc.Dropdown(
                id='dropdown-indicator',
                options=[{'label': ind, 'value': ind} for ind in sorted(df_data['Indicator'].unique())],
                value=df_data['Indicator'].unique()[0]
            )
        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%'}),

        html.Div([
            html.Label("Choisir normalisation :"),
            dcc.Dropdown(
                id='dropdown-norm',
                options=[{'label': n, 'value': n} for n in norm_map.keys()],
                value='No norm'
            )
        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%'}),

        html.Div([
            html.Label("Choisir échelle :"),
            dcc.Dropdown(
                id='dropdown-scale',
                options=[{'label': s, 'value': s} for s in ['absolute', 'relative', 'rank', 'log']],
                value='relative'
            )
        ], style={'width': '32%', 'display': 'inline-block'}),
    ], style={'padding': '10px', 'backgroundColor': '#f5f5f5'}),

    html.Div([
        html.Label("Année :", style={'fontWeight': 'bold', 'marginTop': '10px'}),
        dcc.Slider(
            id='slider-year',
            min=df_data['Year'].min(),
            max=df_data['Year'].max(),
            step=1,
            value=df_data['Year'].min(),
            marks={int(y): str(y) for y in sorted(df_data['Year'].unique())},
            tooltip={"placement": "bottom", "always_visible": False}
        )
    ], style={'padding': '15px 30px 0px 30px'}),

    dcc.Graph(
        id='world-map',
        style={'width': '100%', 'height': 'calc(100vh - 230px)', 'marginBottom': '10px'}
    )
])

# --- Callback ---
@app.callback(
    Output('world-map', 'figure'),
    Input('dropdown-indicator', 'value'),
    Input('slider-year', 'value'),
    Input('dropdown-norm', 'value'),
    Input('dropdown-scale', 'value')
)
def update_map(indicator, year, norm_name, scale):
    year = int(year)
    df_filtered = df_data[(df_data['Indicator'] == indicator) & (df_data['Year'] == year)].copy()

    if df_filtered.empty:
        return go.Figure().update_layout(
            title=f"Aucune donnée pour {indicator} en {year}",
            paper_bgcolor='white'
        )

    gdf_merged = gdf_world.merge(df_filtered, on='Country_code', how='left')
    geojson_data = json.loads(gdf_merged.to_json())

    col_value, col_unit = norm_map[norm_name]
    z_plot = gdf_merged[col_value]
    unit_val = gdf_merged[col_unit].iloc[0] if col_unit in gdf_merged.columns else ""

    if scale == 'relative':
        fig = go.Figure(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index,
            z=z_plot,
            text=gdf_merged['name'],
            colorscale=color_map,
            zmin=zmin,
            zmax=zmax,
            customdata=gdf_merged[col_value],
            colorbar_title=colorbar_title,
            hovertemplate = (f"<b>%{{text}}</b><br>{indicator} ({norm_name}) = %{{customdata:.2f}} {unit_val}<extra></extra>"),

        ))

    elif scale == 'rank':
        z_plot = z_plot.rank(ascending=True)
        fig = go.Figure(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index,
            z=z_plot,
            text=gdf_merged['name'],
            colorscale='RdYlGn_r',
            colorbar_title=f"{indicator} ({unit_val})",
            hovertemplate=f"<b>%{{text}}</b><br>{indicator} ({norm_name}) = %{{z:.2f}} {unit_val}<extra></extra>"
        ))
    elif scale == 'log':
        z_plot = z_plot.apply(symlog)
        fig = go.Figure(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index,
            z=z_plot,
            text=gdf_merged['name'],
            colorscale='RdYlGn_r',
            colorbar_title=f"{indicator} ({unit_val})",
            hovertemplate=f"<b>%{{text}}</b><br>{indicator} ({norm_name}) = %{{z:.2f}} {unit_val}<extra></extra>"
        ))
    elif scale == 'absolute':
        # Create colorbar
        colorbar_dict = dict(
            title=f"{indicator} ({unit_val})",
            tickvals=tickvals,
            ticktext=ticktext)
        zborne=max(abs(zmin),abs(zmax))
        zmid = 0
        fig = go.Figure(go.Choropleth(
            geojson=geojson_data,
            locations=gdf_merged.index,
            z=z_plot,
            text=gdf_merged['name'],
            colorscale=color_map,
            zmin=--100,
            zmax=zborne,
            zmid=0,
            customdata=gdf_merged[col_value],
            colorbar_title=colorbar_title,
            colorbar=colorbar_dict,
            hovertemplate = (f"<b>%{{text}}</b><br>{indicator} ({norm_name}) = %{{customdata:.2f}} {unit_val}<extra></extra>"),
            visible=(norm_name == "No norm"),
            name=norm_name
        ))

    fig.update_layout(
        geo=dict(
            showcountries=True,
            showcoastlines=True,
            showland=True,
            landcolor="lightgray",
            oceancolor="lightblue",
            projection_type="natural earth",
            fitbounds="locations"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )

    return fig

# --- Lancer ---
if __name__ == "__main__":
    import webbrowser
    url = "http://127.0.0.1:8050/"
    webbrowser.open_new_tab(url)
    app.run(debug=True, port=8050, threaded=True)
