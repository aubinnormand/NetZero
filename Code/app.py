from pathlib import Path
import sys
import dash
from dash import dcc, html

# Root of project (NetZero)
base_path = Path(__file__).parent.parent  # <-- parent of Code/
code_path = Path(__file__).parent         # Code/
scripts_path = Path(__file__).parent / "scripts"
sys.path.append(str(scripts_path.resolve()))

# Ajouter le dossier Code au path
sys.path.append(str(code_path.resolve()))


from scripts.data_utils import import_csv_data, import_data_sig
from scripts.map_utils import simplify_geom
from scripts.layout import get_layout
from scripts.callbacks import register_callbacks
from scripts.config import norm_map, scale_options, color_range_options, type_options, first_year, geom_simplify_tol, last_year


# --- Load data ---
filename = "data_final_all_norm.csv"
df_data = import_csv_data(base_path,filename)
gdf_world = import_data_sig(base_path,'world.geojson', )

# --- Simplify geometry ---
gdf_world = gdf_world[gdf_world['Country_code'].notna()].copy()
gdf_world['geometry'] = gdf_world['geometry'].apply(lambda g: simplify_geom(g, tol=geom_simplify_tol))

# --- Options ---
indicator_options = df_data['Indicator'].unique()
database_options = df_data['Source'].unique()
year_options = sorted(df_data['Year'].unique())

norm_map_labels = list(norm_map.keys())

# --- Dash app ---
app = dash.Dash(__name__)
server = app.server  # <-- Must be global, visible par Gunicorn

app.title = "NetZeroVisu"
app.layout = get_layout(indicator_options, database_options, norm_map_labels, first_year, last_year, year_options, scale_options, color_range_options, type_options)
register_callbacks(app, df_data, gdf_world, norm_map)

if __name__ == "__main__":
    app.run(debug=False)

