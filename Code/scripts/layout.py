from dash import html, dcc

def get_layout(
    indicator_options,
    database_options,
    norm_map_labels,
    first_year,
    last_year,
    year_options,
    scale_options,
    color_range_options,
    type_options
):
    return html.Div([
        # --- Sidebar ---
        html.Div([
            html.Label("Indicator"),
            dcc.Dropdown(
                id="indicator",
                options=[{"label": i, "value": i} for i in indicator_options],
                value=indicator_options[0],
                placeholder="Indicator",
                style={'marginBottom': '20px'}
            ),

            html.Label("Database"),
            dcc.Dropdown(
                id="database",
                options=[{"label": i, "value": i} for i in database_options],
                value=database_options[0],
                placeholder="Database",
                style={'marginBottom': '20px'}
            ),

            html.Label("Normalization"),
            dcc.Dropdown(
                id="normalization",
                options=[{"label": name, "value": name} for name in norm_map_labels],
                value=norm_map_labels[0],
                placeholder="Normalization",
                style={'marginBottom': '20px'}
            ),

            html.Label("Type"),
            dcc.Dropdown(
                id="type",
                options=type_options,
                value="Annual",
                placeholder="Type",
                style={'marginBottom': '20px'}
            ),

            html.Label("Scale"),
            dcc.Dropdown(
                id="scale",
                options=[{"label": i, "value": i} for i in scale_options],
                value='relative',
                placeholder="Scale",
                style={'marginBottom': '20px'}
            ),

            html.Label("Color Range"),
            dcc.Dropdown(
                id="color_range",
                options=[{"label": i, "value": i} for i in color_range_options],
                value='raw',
                placeholder="Color Range",
                style={'marginBottom': '20px'}
            ),
        ], style={
            'flex': '0 0 250px',
            'padding': '15px',
            'backgroundColor': '#f8f9fa',
            'boxShadow': '2px 0px 5px rgba(0,0,0,0.1)',
            'height': '100vh',
            'overflowY': 'auto'
        }),

        # --- Main content (map + slider) ---
        html.Div([
            html.Div([
                dcc.Graph(
                    id="world_map",
                    style={'height': '85vh', 'width': '80vw', 'margin': '0 auto'}
                )
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'height': '85vh'}),

            html.Div([
                html.Label("Year", style={'fontWeight': 'bold', 'textAlign': 'center', 'display': 'block', 'fontSize':'20px'}),
                dcc.Slider(
                    id='year',
                    min=first_year,
                    max=last_year,
                    step=1,
                    marks={
                        int(year_options[0]): str(first_year),
                        int(year_options[-1]): str(last_year),
                        **{int(y): str(int(y)) for y in year_options if int(y) % 5 == 0 and y >= first_year}
                    },
                    value=last_year,
                    tooltip={"placement": "bottom", "always_visible": False},
                )
            ], style={'width': '60%', 'margin': '10px auto 0 auto', 'padding': '0'})
        ], style={'flex': '1', 'padding': '0px'}),
    ], style={'display': 'flex', 'flexDirection': 'row', 'height': '100vh'})
