from dash import Dash, html, dash_table, dcc, Output, Input, State, no_update, callback
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import dash_ag_grid as dag

import socket
from werkzeug.serving import WSGIRequestHandler

import numpy as np
from bs4 import BeautifulSoup
import requests, json
from pprint import pprint



url = "https://fantasy.premierleague.com/api/"
response = requests.get(url+'bootstrap-static/').json()

players = response["elements"]

pd.set_option('display.max_columns', None)
players = pd.json_normalize(response['elements'])

positions = pd.json_normalize(response['element_types'])

teams = pd.json_normalize(response['teams'])

fpl_df = pd.merge(
    left=players,
    right=teams,
    left_on='team',
    right_on='id'
)


fpl_df = fpl_df.merge(
    positions,
    left_on='element_type',
    right_on='id'
)

fpl_df = fpl_df.rename(
    columns={'name':'team_name', 'singular_name':'position_name', "id_x": "player_id",
             "id_y": "team_id", "id": "position_id", "ep_next": "predicted_points"}
)

fpl_df["Name"] = fpl_df["first_name"] + " " + fpl_df["second_name"]


fpl_df.drop(columns=["code_x","cost_change_event", "cost_change_event_fall", 
                 "cost_change_start", "cost_change_start_fall", "news", 
                 "news_added", "photo", "now_cost", "transfers_in_event", 
                 "transfers_out_event", "influence_rank", "influence_rank_type", 
                 "creativity_rank", "creativity_rank_type", "threat_rank", 
                 "threat_rank_type", "ict_index_rank", "ict_index_rank_type", 
                 "corners_and_indirect_freekicks_order", 
                 "corners_and_indirect_freekicks_text", 
                 "corners_and_indirect_freekicks_text", 
                 "direct_freekicks_order", "plural_name", 
                 "plural_name_short", "pulse_id", "team_division", 
                 "code_y", "first_name", "in_dreamteam", "second_name", 
                 "selected_by_percent", "special", "squad_number", "status",
                 "yellow_cards", "red_cards", "web_name", "yellow_cards", "red_cards", 
                 "web_name", "chance_of_playing_next_round",
                 "chance_of_playing_this_round", "dreamteam_count",
                 "element_type", "event_points", "form_x", "team",
                 "team_code", "value_form", "value_season", "region",
                 "influence", "creativity", "threat", "ict_index", "direct_freekicks_text",
                 "penalties_order", "penalties_text", "now_cost_rank", "now_cost_rank_type",
                 "form_rank", "form_rank_type", "points_per_game_rank",
                 "points_per_game_rank_type", "selected_rank", "selected_rank_type",
                 "draw", "form_y", "loss", "played", "position", "win", "strength_overall_home",
                 "strength_overall_away", "strength_attack_home", "strength_attack_away", 
                 "strength_defence_home", "strength_defence_away", "squad_select",
                 "squad_min_select", "squad_max_select", "squad_min_play",
                 "squad_max_play", "ui_shirt_specific", "sub_positions_locked",
                 "element_count", "unavailable", "singular_name_short"], axis=1, inplace=True)


total_underlying = fpl_df[["Name", "team_name", "position_name", "expected_goals", "expected_assists", "expected_goal_involvements", "expected_goals_conceded"]]

underlying_per_90 = fpl_df[["Name", "team_name", "position_name", "expected_goals_per_90", "expected_assists_per_90", "expected_goal_involvements_per_90", "expected_goals_conceded_per_90"]]

transfers = fpl_df[["Name", "team_name", "position_name", "transfers_in", "transfers_out"]]

player_record = fpl_df[["Name", "team_name", "position_name", "goals_scored", "assists", "clean_sheets", "goals_conceded", "saves", "bonus"]]

predictions = fpl_df[["Name", "team_name", "position_name", "predicted_points"]]



f_total_underlying = total_underlying.to_dict(orient="records")

f_underlying_per_90 = underlying_per_90.to_dict(orient="records")

f_transfers = transfers.to_dict(orient="records")

f_player_record = player_record.to_dict(orient="records")

f_predictions = predictions.to_dict(orient="records")



tu = px.histogram(total_underlying, x="Name", y={}, histfunc="sum")

up90 = px.histogram(underlying_per_90, x="Name", y={}, histfunc="sum")

tr = px.histogram(transfers, x="Name", y={}, histfunc="sum")

pr = px.histogram(player_record, x="Name", y={}, histfunc="sum")

pr = px.histogram(predictions, x="Name", y={}, histfunc="sum")


predictions["predicted_points"] = predictions["predicted_points"].astype(float)





app = Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)


app.layout = dbc.Container([
        dbc.Row(
            [
                dbc.Col([
                    dcc.Dropdown(
                    id="teams",
                    options= ['Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
                            'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Ipswich',
                            'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle',
                            "Nott'm Forest", 'Southampton', 'Spurs', 'West Ham', 'Wolves'],
                    value= "Arsenal",
                    multi=True
                    ),
                ], width=6),

                dbc.Col([
                    dcc.RadioItems(
                    id="positions",
                    options= ['Midfielder', 'Forward', 'Defender', 'Goalkeeper'],
                    value= "Goalkeeper",
                    ),
                ], width=6),
                dbc.Col([dbc.Button("Submit", color="danger", id="button", n_clicks=0)], width=6, className="text-center" ),
        dbc.Row(
            [
                dbc.Col([
                    html.H4("Player Records"),
                    dag.AgGrid(
                        id="grid1",
                        rowData= player_record.to_dict("records"),
                        columnDefs= [{"field": i} for i in player_record.columns],
                        dashGridOptions={"rowSelection": "single"},
                        ),
                    # dcc.Dropdown(
                    #         options= ['Name', 'team_name', 'position_name', 'goals_scored', 'assists',
                    #                     'clean_sheets', 'goals_conceded', 'saves', 'bonus'],
                    #         value="goals_scored",
                    #         id="dropdown1"
                    # ),
                    # dcc.Graph(figure= pr, id="graph1")
                ], width=12),
                dbc.Col([
                    html.H4("Underlying Statistics"),
                    dag.AgGrid(
                            id="grid2",
                            rowData= total_underlying.to_dict("records"),
                            columnDefs= [{"field": i} for i in total_underlying.columns],
                            dashGridOptions={"rowSelection": "single"},
                        ),
                    # dcc.Dropdown(
                    #         options= ['Name', 'team_name', 'position_name', 'expected_goals',
                    #                 'expected_assists', 'expected_goal_involvements',
                    #                 'expected_goals_conceded'],
                    #         value="expected_goals",
                    #         id="dropdown2"
                    # ),
                    # dcc.Graph(figure=tu, id="graph2")
                ], width=12),
                dbc.Col([
                    html.H4("Underlying Statistics Per 90"),
                    dag.AgGrid(
                            id="grid3",
                            rowData= underlying_per_90.to_dict("records"),
                            columnDefs= [{"field": i} for i in underlying_per_90.columns],
                            dashGridOptions={"rowSelection": "single"},
                        ),
                    # dcc.Dropdown(
                    #         options= ['Name', 'team_name', 'position_name', 'expected_goals_per_90',
                    #                     'expected_assists_per_90', 'expected_goal_involvements_per_90',
                    #                     'expected_goals_conceded_per_90'],
                    #         value="expected_goals",
                    #         id="dropdown3"
                    # ),
                    # dcc.Graph(figure=up90, id="graph3")
                ], width=12),
            ]
        ),
        dbc.Row(
            [
                dbc.Col([
                    html.H4("Transfer Activity"),
                    dag.AgGrid(
                            id="grid4",
                            rowData= transfers.to_dict("records"),
                            columnDefs= [{"field": i} for i in transfers.columns],
                            dashGridOptions={"rowSelection": "single"},
                        ),
                    # dcc.Dropdown(
                    #         options= ['Name', 'team_name', 'position_name', 'transfers_in', 'transfers_out'],
                    #         value="expected_goals",
                    #         id="dropdown4"
                    # ),
                    # dcc.Graph(figure=tr, id="graph4")
                ], width=12),
                dbc.Col([
                    html.H4("Predictions"),
                    dag.AgGrid(
                            id="grid5",
                            rowData= predictions.to_dict("records"),
                            columnDefs= [{"field": i} for i in predictions.columns],
                            dashGridOptions={"rowSelection": "single"},
                        ),
                    html.Label("Select top N values"),
                    dcc.Slider(
                        id="top_n",
                        min=1,
                        max=15,
                        step=1,
                        value=5,
                        marks={i: str(i) for i in range(1, 21)},
                        ),
                    dcc.Graph(figure=pr, id="graph5")
                ], width=12)
            ]
        )
    ])
])






@app.callback(
    Output(component_id="grid1", component_property="columnDefs"),
    Output(component_id="grid1", component_property="rowData"),
    # Output(component_id="graph1", component_property="figure"),
    Output(component_id="grid2", component_property="columnDefs"),
    Output(component_id="grid2", component_property="rowData"),
    # Output(component_id="graph2", component_property="figure"),
    Output(component_id="grid3", component_property="columnDefs"),
    Output(component_id="grid3", component_property="rowData"),
    # Output(component_id="graph3", component_property="figure"),
    Output(component_id="grid4", component_property="columnDefs"),
    Output(component_id="grid4", component_property="rowData"),
    # Output(component_id="graph4", component_property="figure"),
    Output(component_id="grid5", component_property="columnDefs"),
    Output(component_id="grid5", component_property="rowData"),
    Output(component_id="graph5", component_property="figure"),
    # Input(component_id="dropdown1", component_property="value"),
    # Input(component_id="dropdown2", component_property="value"),
    # Input(component_id="dropdown3", component_property="value"),
    # Input(component_id="dropdown4", component_property="value"),
    Input(component_id='button', component_property='n_clicks'),
    Input(component_id="top_n", component_property="value"),
    State(component_id="positions", component_property="value"),
    State(component_id="teams", component_property="value"),
    prevent_initial_call = True
)

def update_tables(n_clicks, top_n, selected_position, selected_clubs):

        if not selected_clubs:
            selected_clubs = []

        print(f"Selected club: {selected_clubs}, Selected position: {selected_position}")
    
        filtered_prr = player_record[(player_record['team_name'].isin(selected_clubs)) & (player_record['position_name'] == selected_position)]
        grid1_column_defs = [{"field": col} for col in filtered_prr.columns]
        # graph1 = px.histogram(filtered_prr, x="Name", y= dropdown1, histfunc="sum")

        filtered_tu = total_underlying[(fpl_df['team_name'].isin(selected_clubs)) & (total_underlying['position_name'] == selected_position)]
        grid2_column_defs = [{"field": col} for col in filtered_tu.columns]
        # graph2 = px.histogram(filtered_tu, x="Name", y=dropdown2, histfunc="sum")

        filtered_up90 = underlying_per_90[(fpl_df['team_name'].isin(selected_clubs)) & (underlying_per_90['position_name'] == selected_position)]
        grid3_column_defs = [{"field": col} for col in filtered_up90.columns]
        # graph3 = px.histogram(filtered_up90, x="Name", y=dropdown3, histfunc="sum")

        filtered_tr = transfers[(fpl_df['team_name'].isin(selected_clubs)) & (transfers['position_name'] == selected_position)]
        grid4_column_defs = [{"field": col} for col in filtered_tr.columns]
        # graph4 = px.histogram(filtered_tr, x="Name", y=dropdown4, histfunc="sum")

        filtered_pr = predictions[(predictions['team_name'].isin(selected_clubs)) & (predictions['position_name'] == selected_position)]
        filtered_pred = filtered_pr.nlargest(top_n, "predicted_points")
        grid5_column_defs = [{"field": col} for col in filtered_pr.columns]
        graph5 = px.histogram(filtered_pred, x="Name", y="predicted_points", histfunc="sum")


        return(
            grid1_column_defs, filtered_prr.to_dict("records"),
            grid2_column_defs, filtered_tu.to_dict("records"),
            grid3_column_defs, filtered_up90.to_dict("records"),
            grid4_column_defs, filtered_tr.to_dict("records"),
            grid5_column_defs, filtered_pr.to_dict("records"), graph5
        )



      




WSGIRequestHandler.address_family = socket.AF_INET
WSGIRequestHandler.allow_reuse_address = True

if __name__ == "__main__":
    app.run(debug=True, port=8052)