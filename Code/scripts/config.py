# --- Normalizations and units ---
norm_map = {
    'No norm': ('Value', 'Unit'),
    'Area': ('Value_norm_area', 'Unit_norm_area'),
    'Population': ('Value_norm_population', 'Unit_norm_population'),
    'GDP': ('Value_norm_gdp', 'Unit_norm_gdp'),
    'GDP(PPP)': ('Value_norm_ppp', 'Unit_norm_ppp'),
    'GDP/hab': ('Value_norm_gdp_hab', 'Unit_norm_gdp_hab'),
    'PGD(PPP)/hab': ('Value_norm_ppp_hab', 'Unit_norm_ppp_hab'),
}

# --- Geometry simplification ---
geom_simplify_tol = 0.1

# --- Dropdown options ---
scale_options = ['absolute', 'relative', 'rank', 'log']
color_range_options = ['raw', 'q0.01', 'q0.05', 'q0.1', '*0.8']
type_options = [
    {"label": "Annual", "value": "Annual"},
    {"label": "Cumulative", "value": "Cumulative"}
]

# --- Slider settings ---
first_year = 1960
last_year= 2023
year_step = 1

# --- Choropleth defaults ---
default_colorscale = 'RdYlGn_r'
no_data_color = 'lightgray'
