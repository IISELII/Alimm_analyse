import dash
from dash import dcc, Output, Input
from dash import html
import pandas as pd
import numpy as np
import seaborn as sns
import plotly.graph_objs as go
import plotly.express as px
import page_1
from page_1 import layout as page_1_layout

# Create Dash app
app = dash.Dash(__name__)
server = app.server

# load data
population = pd.read_csv("data/population.csv")
sous_nutrition = pd.read_csv("data/sous_nutrition.csv")
dispo_alimentaire = pd.read_csv("data/dispo_alimentaire.csv")
aide_alimentaire = pd.read_csv("data/aide_alimentaire.csv")

# preprocess
aide_alimentaire = aide_alimentaire.rename(columns = {'Pays bénéficiaire': 'Zone', 'Valeur': 'Quantité (en tonne)'})
sous_nutrition = sous_nutrition.rename(columns = {'Valeur': 'sous_nutrition (million)'})
population = population.rename(columns = {'Valeur': 'nb_population (millier)'})
sous_nutrition["Année"] = sous_nutrition["Année"].map({'2012-2014': 2013,
                                                    '2013-2015': 2014,
                                                    '2014-2016': 2015,
                                                    '2015-2017': 2016,
                                                    '2016-2018': 2017,
                                                    '2017-2019': 2018})

population["population_en_million"] = population["nb_population (millier)"] / 1E3

sous_nutrition = sous_nutrition.dropna(subset =['Année'])
sous_nutrition["Année"] = sous_nutrition["Année"].astype(int)


app.validation_layout = html.Div([app.layout, page_1.layout])
app.config.suppress_callback_exceptions = True

# Define layout
app.layout =  html.Div([ html.H3("Partie 1"),
    dcc.Location(id='url', refresh=False),
    dcc.Link('passez à la partie 2', href='/page_1'),
    html.Br(),


    html.H1(children="Alimentation et Sous-Nutrition", style={'text-align': 'center'}),

    # Dropdown to select year
    dcc.Dropdown(
        id="year-dropdown",
        options=[{"label": y, "value": y} for y in range(2013, 2018)],
        value= "2017",
        clearable=False
    ),

    # Partie 1
    html.H2(children="Partie 1", style={'text-align': 'center'}),
    html.Br(),

    # Q1
    html.H3(children="Q1"),
    html.Div(id="q1"),
    html.Br(),

    # Q2
    html.H3(children="Q2"),
    html.Div(id="q2"),
    html.Br(),

    # Q3
    html.H3(children="Q3"),
    html.Div(id="q3"),
    html.Br(),

    # Q4
    html.H3(children="Q4"),
    html.Div(id="q4"),
    html.Br(),

], id = "page-content")

# @app.callback(Output('page-content', 'children'),
#               [Input('url', 'pathname')])
@app.callback(
    [
        dash.dependencies.Output("q1", "children"),
        dash.dependencies.Output("q2", "children"),
        dash.dependencies.Output("q3", "children"),
        dash.dependencies.Output("q4", "children"),
    ],
    [dash.dependencies.Input("year-dropdown", "value")],

)

# def display_page(pathname):
#     if pathname == '/page_1':
#         return page_1.layout
#     # else:
#     #     return html.Div([
#     #         html.H3('Page inconnue'),
#     #         dcc.Link('Retour à la page principale', href='/')
#     #     ])


def update_partie_1(Year):
    Year = int(Year)


    # Filter the dataframes by the selected year
    pop_year = population[population["Année"] == Year]
    sn_year = sous_nutrition[sous_nutrition["Année"] == Year]
    # da_year = dispo_alimentaire[dispo_alimentaire["Année"] == Year]
    aa_year = aide_alimentaire[aide_alimentaire["Année"] == Year]

    # preprocessing data
    population_Année = population.loc[population["Année"] == Year]
    gb_population = population_Année.groupby(by = "Zone")["population_en_million"].mean().reset_index()
    sous_nutrition_Année = sous_nutrition.loc[sous_nutrition["Année"] == Year]
    sous_nutrition_no_nan = sous_nutrition_Année.dropna()
    sous_nutrition_01 = sous_nutrition_no_nan.loc[sous_nutrition_no_nan["sous_nutrition (million)"] == "<0.1"]
    sous_nutrition_no_nan["sous_nutrition (million)"] = sous_nutrition_no_nan["sous_nutrition (million)"].replace("<0.1", "0.1")
    sous_nutrition_02 = sous_nutrition_no_nan.loc[sous_nutrition_no_nan["sous_nutrition (million)"] != "0.1"]
    gb_sous_nutrition = sous_nutrition_02.groupby(by = "Zone")["sous_nutrition (million)"].mean().reset_index()
    dispo_no_NaN = dispo_alimentaire.drop(["Traitement", "Semences", "Pertes", "Autres Utilisations", "Aliments pour animaux",
                                         "Variation de stock", "Production"],
                                        axis = 1)
    dispo = dispo_no_NaN.dropna()
    gb_aide_alimentaire = aide_alimentaire.groupby(by = "Zone")["Quantité (en tonne)"].sum().reset_index()
    df_merge = gb_sous_nutrition.merge(gb_population, on = "Zone", how = "left")
    df_merge["proportion_sous_nutrition"] = df_merge["sous_nutrition (million)"] / df_merge["population_en_million"]

    # total théorique
    gb_zone = dispo_alimentaire.groupby(by = "Zone")["Disponibilité alimentaire (Kcal/personne/jour)"].sum().reset_index()
    gb_des_deux = gb_zone.merge(gb_population, how='inner', on='Zone')
    gb_des_deux["total_calories"] = gb_des_deux["Disponibilité alimentaire (Kcal/personne/jour)"] * (gb_des_deux['population_en_million'] * 1e3)

    # total théorique végé
    dispo_végétale = dispo_alimentaire.loc[dispo_alimentaire["Origine"] == "vegetale"]
    gb_végé = dispo_végétale.groupby(by = "Zone")["Disponibilité alimentaire (Kcal/personne/jour)"].sum().reset_index()
    gb_végé_population = gb_végé.merge(gb_population, how='left', on='Zone')
    gb_végé_population["total_calories"] = gb_végé_population["Disponibilité alimentaire (Kcal/personne/jour)"] * (gb_végé_population['population_en_million'] * 1e3)

    # Calculate the necessary values
    proportion_sous_nutrition = df_merge["sous_nutrition (million)"].sum() / gb_population["population_en_million"].sum() * 100
    nbre_total_pers_theorique = round((gb_des_deux['total_calories'].sum() / 2500) / 1e6, 2)
    pourcentage = round(nbre_total_pers_theorique/ (gb_des_deux['population_en_million'].sum() / 1e3) * 100, 2)
    nbre_total_pers_theorique_végé = round((gb_végé_population['total_calories'].sum() / 2500) / 1e6, 2)
    pourcentage_végé = round(nbre_total_pers_theorique_végé/ (gb_végé_population['population_en_million'].sum() / 1e3) * 100, 2)

    # Format the outputs
    q1 = f"En {Year}, la proportion de personnes en état de sous-nutrition dans le monde est de {proportion_sous_nutrition}%."
    q2 = f"Le nombre théorique de personnes qui pourraient être nourries est de {nbre_total_pers_theorique} milliards, soit {pourcentage}% de la population mondiale."
    q3 = f"Le nombre théorique de personnes qui pourraient être nourries avec des produits végétaux est de {nbre_total_pers_theorique_végé} milliards, soit {pourcentage_végé}% de la population mondiale."
    q4 = "Top 5 des pays avec la pire proportion de sous-nutrition :"
    q5 = "Top 5 des pays avec la meilleur proportion de sous-nutrition :"

     # Create a bar chart for the top 5 worst countries
    gb_worse_sous_nutrition = df_merge.sort_values(by = ["proportion_sous_nutrition"], ascending = False)
    gb_worse_sous_nutrition = gb_worse_sous_nutrition.reset_index().sort_values(by=["proportion_sous_nutrition"], ascending=False)[:5]
    # Définir la palette de couleurs
    palette = px.colors.sequential.Viridis[:5]
    bar = go.Bar(
        x=gb_worse_sous_nutrition["Zone"],
        y=gb_worse_sous_nutrition["proportion_sous_nutrition"],
        marker={"color": palette}
        # ["#FF796C", "#DBB40C", "#E6DAA6", "#90EE90", "#7BC8F6"]
    )
    layout = go.Layout(
        title={
            "text": "Top 5 des pays avec le taux de sous-nutrition le plus mauvais",
            "x": 0.5},
        xaxis={"title": "Pays"},
        yaxis={"title": "Proportion de sous-nutrition"}
    )
    fig = go.Figure(data=[bar], layout=layout)

    # # Create a bar chart for the top 5 best countries
    # gb_best_sous_nutrition = df_merge.sort_values(by = ["proportion_sous_nutrition"], ascending = True)
    # gb_best_sous_nutrition = gb_best_sous_nutrition.reset_index().sort_values(by=["proportion_sous_nutrition"], ascending=False)[:5]
    # bar_1 = go.Bar(
    #     x=gb_best_sous_nutrition["Zone"],
    #     y=gb_best_sous_nutrition["proportion_sous_nutrition"],
    #     marker={"color": "green"}
    # )
    # layout_1 = go.Layout(
    #     title="Top 5 des pays avec la meilleur proportion de sous-nutrition",
    #     xaxis={"title": "Pays"},
    #     yaxis={"title": "Proportion de sous-nutrition"}
    # )
    # fig_1 = go.Figure(data=[bar_1], layout=layout_1)


    return q1, q2, q3, [q4, dcc.Graph(figure=fig)]



if __name__ == "__main__":
    app.run_server(debug=True)
