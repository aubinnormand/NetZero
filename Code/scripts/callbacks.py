from dash import Input, Output
import plotly.graph_objects as go
import json
import numpy as np
from map_utils import symlog

def register_callbacks(app, df_data, gdf_world, norm_map):
    
    # --- Mapping ---
    category_to_indicator = (
        df_data.groupby("Category")["Indicator"]
        .unique()
        .apply(list)
        .to_dict()
    )
    indicator_to_db = (
        df_data.groupby("Indicator")["Source"]
        .unique()
        .apply(list)
        .to_dict()
    )

    # --- Dynamic Indicator dropdown ---
    @app.callback(
        Output("indicator", "options"),
        Output("indicator", "value"),
        Input("category", "value")
    )
    def update_indicator_dropdown(selected_category):
        valid_inds = category_to_indicator.get(selected_category, [])
        options = [{"label": ind, "value": ind} for ind in valid_inds]
        default_value = valid_inds[0] if valid_inds else None
        return options, default_value

    # --- Dynamic Database dropdown ---
    @app.callback(
        Output("database", "options"),
        Output("database", "value"),
        Input("indicator", "value")
    )
    def update_database_dropdown(selected_indicator):
        valid_dbs = indicator_to_db.get(selected_indicator, [])
        options = [{"label": db, "value": db} for db in valid_dbs]
        default_value = valid_dbs[0] if valid_dbs else None
        return options, default_value

    # --- Map update callback ---
    @app.callback(
        Output("world_map", "figure"),
        Input("category", "value"),
        Input("indicator", "value"),
        Input("database", "value"),
        Input("type", "value"),
        Input("year", "value"),
        Input("scale", "value"),
        Input("color_range", "value"),
        Input("normalization", "value")
    )
    def update_map(category, indicator, database, type_value, year, scale, color_range, normalization):
        # --- Filter data ---
        df_filtered = df_data[
            (df_data['Category'] == category) &
            (df_data['Indicator'] == indicator) &
            (df_data['Source'] == database) &
            (df_data['Type'] == type_value) &
            (df_data['Year'] == year)
        ].copy()

        # --- Merge with geometry ---
        gdf_merged = gdf_world.merge(df_filtered, on='Country_code', how='left')
        geojson_data = json.loads(gdf_merged.to_json())

        # --- Columns for values and units ---
        col_value, col_unit = norm_map[normalization]
        if col_value not in gdf_merged.columns:
            gdf_merged[col_value] = np.nan
        if col_unit not in gdf_merged.columns:
            gdf_merged[col_unit] = ""

        z_values = gdf_merged[col_value]
        no_data_at_all = z_values.dropna().empty

        if no_data_at_all:
            unit_prefix = ""
            z_plot_scaled = np.zeros(len(gdf_merged))
            colorscale_to_use = [[0, 'lightgray'], [1, 'lightgray']]
            zmin, zmax = 0, 1
            colorbar_ticks = dict(ticks="", tickvals=[], ticktext=[])
            hovertemplate = f"<b>%{{text}}</b><br>{indicator} ({normalization}) = No data<extra></extra>"
        else:
            # --- Determine color range ---
            if color_range == 'raw':
                zmin_raw, zmax_raw = z_values.min(), z_values.max()
            elif color_range.startswith("q"):
                q_low = float(color_range[1:])
                q_high = 1 - q_low
                zmin_raw, zmax_raw = z_values.quantile(q_low), z_values.quantile(q_high)
            elif color_range.startswith("*"):
                factor = float(color_range[1:])
                zmin_raw, zmax_raw = factor * z_values.min(), factor * z_values.max()
            else:
                raise ValueError("color_range must be 'raw', 'q0.xx', or '*0.xx'")

            # --- Determine z_plot_scaled and zmin/zmax depending on scale ---
            unit_prefix = gdf_merged[col_unit].iloc[0] if col_unit in gdf_merged.columns else ""
            unit_multiplier = 1

            if scale == 'absolute':
                z_plot = z_values.copy()
                zborne = max(abs(zmin_raw), abs(zmax_raw))
                if zborne >= 1e9:
                    unit_multiplier = 1e9
                    unit_prefix = f"G{unit_prefix}"
                elif zborne >= 1e6:
                    unit_multiplier = 1e6
                    unit_prefix = f"M{unit_prefix}"
                elif zborne >= 1e3:
                    unit_multiplier = 1e3
                    unit_prefix = f"k{unit_prefix}"
                z_plot_scaled = z_plot / unit_multiplier
                zmin, zmax = -zborne / unit_multiplier, zborne / unit_multiplier
                colorscale_to_use = 'RdYlGn_r'

            elif scale == 'relative':
                z_plot = z_values.copy()
                zborne = max(abs(zmin_raw), abs(zmax_raw))
                if zborne >= 1e9:
                    unit_multiplier = 1e9
                    unit_prefix = f"G{unit_prefix}"
                elif zborne >= 1e6:
                    unit_multiplier = 1e6
                    unit_prefix = f"M{unit_prefix}"
                elif zborne >= 1e3:
                    unit_multiplier = 1e3
                    unit_prefix = f"k{unit_prefix}"
                z_plot_scaled = z_plot / unit_multiplier
                zmin = zmin_raw / unit_multiplier
                zmax = zmax_raw / unit_multiplier
                colorscale_to_use = 'RdYlGn_r'

            elif scale == 'rank':
                z_plot = z_values.rank(ascending=True)
                z_plot_scaled = z_plot
                zmin, zmax = z_plot.min(), z_plot.max()
                colorscale_to_use = 'YlOrBr'

            elif scale == 'log':
                z_plot = z_values.apply(symlog)
                z_plot_scaled = z_plot
                zmin, zmax = z_plot.min(), z_plot.max()
                colorscale_to_use = 'RdYlGn_r'

            else:
                raise ValueError("scale must be 'absolute', 'relative', 'rank', or 'log'")

            if type_value == "Annual":
                unit_prefix = f"{unit_prefix}/year"

            # --- Colorbar ticks ---
            tickvals, ticktext = [], []
            if scale == 'absolute':
                pos_ticks = np.linspace(0, zmax, 5)[1:]
                neg_ticks = np.linspace(zmin, 0, 5)[:-1]
                tickvals = np.concatenate([neg_ticks, [0], pos_ticks])
            else:
                tickvals = np.linspace(zmin, zmax, 9)
            for v in tickvals:
                abs_v = abs(v)
                if abs_v > 100:
                    ticktext.append(f"{int(round(v))}")
                elif abs_v > 10:
                    ticktext.append(f"{round(v,1)}")
                else:
                    ticktext.append(f"{round(v,2)}")
            colorbar_ticks = dict(tickvals=tickvals, ticktext=ticktext)
            hovertemplate = f"<b>%{{text}}</b><br>{indicator} ({normalization}) = %{{customdata[0]:.2f}} {unit_prefix}<extra></extra>"

        # --- Build figure ---
        fig = go.Figure(go.Choropleth(
            geojson=json.loads(gdf_merged.to_json()),
            locations=gdf_merged.index,
            z=z_plot_scaled,
            text=gdf_merged['name'],
            colorscale=colorscale_to_use,
            zmin=zmin,
            zmax=zmax,
            zmid=0 if scale=='absolute' else None,
            customdata=np.stack([z_plot_scaled], axis=-1),
            hovertemplate=hovertemplate,
            colorbar=dict(
                title=dict(text=f"<b>{unit_prefix}</b>", side="top", font=dict(size=14,color="black",family="Arial")),
                x=0.0, xanchor='left', len=0.8, thickness=30,
                tickvals=colorbar_ticks.get('tickvals', None),
                ticktext=colorbar_ticks.get('ticktext', None)
            )
        ))

        fig.update_layout(
            geo=dict(
                scope="world", projection_type="natural earth",
                showcountries=True, showcoastlines=True, showland=True, showocean=True,
                landcolor="lightgray", oceancolor="lightblue", lakecolor="lightblue",
                domain=dict(x=[0.07, 1], y=[0, 1])
            ),
            margin=dict(l=0,r=0,t=0,b=0)
        )

        # No data patch
        fig.add_shape(type="rect", xref="paper", yref="paper", x0=0.0, y0=0.93, x1=0.03, y1=0.96,
                      fillcolor="lightgray", line=dict(color="black", width=1))
        fig.add_annotation(xref="paper", yref="paper", x=0.035, y=0.96, text="No data",
                           showarrow=False, font=dict(size=12, color="black"), align="left")

        return fig
