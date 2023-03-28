import dash
from dash import dcc, Output, Input
from dash import html
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px


page_1 = dash.Dash(__name__)
server = page_1.server

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

layout = html.Div([
    html.H1(children="Alimentation et Sous-Nutrition", style={'text-align': 'center'}),

    # Dropdown to select year
    dcc.Dropdown(
        id="year-dropdown",
        options=[{"label": y, "value": y} for y in range(2013, 2018)],
        value= "2017",
        clearable=False
    ),

    # Partie 1
    html.H2(children="Partie 2", style={'text-align': 'center'}),
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

], id = "page-1-content")


# Callback for Partie 1
def update_partie_2(Year):
    Year = int(Year)

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

    dispo_manioc = dispo.loc[(dispo["Produit"] == "Manioc") & (dispo["Zone"] == "Thaïlande")]
    sous_nutrition_thailande = df_merge.loc[df_merge["Zone"] == "Thaïlande"]

    best_aide = gb_aide_alimentaire.sort_values(by = ["Quantité (en tonne)"], ascending = False)
    top_5_best_aide = best_aide.loc[(best_aide["Zone"] == "République arabe syrienne")
                               |(best_aide["Zone"] == "Éthiopie")
                               |(best_aide["Zone"] == "Yémen")
                               |(best_aide["Zone"] == "Soudan du Sud")
                               |(best_aide["Zone"] == "Soudan") ]

    liste_cereales = ["Blé et produits", "Riz et produits", "Orge et produits", "Maïs et produits", "Seigle et produits", "Avoine", "Millet et produits", "Sorgho et produits", "Céréales, Autres"]
    df_cereales = dispo_alimentaire[dispo_alimentaire["Produit"].isin(liste_cereales)]
    df_sommes = df_cereales.groupby(df_cereales["Produit"])[["Nourriture", "Aliments pour animaux", "Disponibilité intérieure"]].sum().reset_index()
    Part_Aliments_pour_animaux = (df_sommes["Aliments pour animaux"] / df_sommes["Disponibilité intérieure"]) * 100
    Part_alimentation_humaine = (df_sommes["Nourriture"] / df_sommes["Disponibilité intérieure"]) * 100


    # calculate the necessary values
    exportation = round((dispo_manioc["Exportations - Quantité"] / (dispo_manioc["Disponibilité intérieure"] - dispo_manioc["Nourriture"] + dispo_manioc["Exportations - Quantité"])) * 100, 2).item()
    thaïlande_sous_nutrition = round(sous_nutrition_thailande["proportion_sous_nutrition"] * 100, 1).item()

    # output
    Q1 = f"La proportion de sous nutrition en Thaïlande est d'environ {thaïlande_sous_nutrition} %, \n la proportion de manioc exporté par rapport à la production totale de manioc en Thaïlande est de {exportation} %"
    Q2 = "Top 5 des pays qui on le plus bénéficié d’aide alimentaire"
    Q3 = f"Alimentation pour animaux : \n\n{Part_Aliments_pour_animaux} % \n\nAlimention humaine : \n\n{Part_alimentation_humaine} %"

    # Create the bar chart for Top 5 des pays qui on le plus bénéficié d’aide alimentaire
    gb_best_aide = top_5_best_aide.sort_values(by = ["Quantité (en tonne)"], ascending = False)
    gb_best_aide = gb_best_aide.reset_index().sort_values(by=["Quantité (en tonne)"], ascending=False)[:5]

    # Définir la palette de couleurs
    palette = px.colors.sequential.Viridis[:5]
    bar = go.Bar(
        x=gb_best_aide["Zone"],
        y=gb_best_aide["Quantité (en tonne)"],
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

    return Q1, [Q2, dcc.Graph(figure=fig)], Q3
