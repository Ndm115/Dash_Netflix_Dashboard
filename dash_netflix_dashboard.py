import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

df = pd.read_csv("C:\\Users\\User\\Downloads\\archive (3)\\netflix_titles.csv", encoding="latin1")
print(df)
df["date_added"] = pd.to_datetime(df["date_added"].str.strip(), errors='coerce')
df["years_added"] = df["date_added"].dt.year
df["release_year"] = df["release_year"].fillna(0)
df["country"] = df["country"].fillna("missing")
df["genre"] = df["listed_in"].str.split(",").str[0]
df['duration'] = df['duration'].fillna('0')

#Creating the dash app:
app = dash.Dash(__name__)
app.title = "Netflix Dashboard"

#filtering layout
app.layout = html.Div([
    html.H2("Netflix Dashboard", style={'textAlign': 'center'}),

    # Simple filters
    html.Div([
        dcc.Dropdown(id='year_filter',
                     options=[{'label': int(y), 'value': y} for y in sorted(df['release_year'].unique()) if y > 0],
                     placeholder="Filter by Year",
                     style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

        dcc.Dropdown(id='type_filter',
                     options=[{'label': t, 'value': t} for t in df['type'].unique()],
                     placeholder="Filter by Type",
                     style={'width': '48%', 'display': 'inline-block'})
    ], style={'padding': '10px'}),

    # Graphs
    dcc.Graph(id='genre_chart'),
    dcc.Graph(id='timeline_chart'),
    dcc.Graph(id='type_pie_chart'),
    dcc.Graph(id='duration_scatter'),
    dcc.Graph(id='country_map')
])

#A helper which is used to function data inserted into app
def get_data_filtered(year, content_type):
    #Copy to ensure main dataset is changed in a wrong way
    data = df.copy()
    #Takes selected year in dropdown, and filters data to include rows of year
    if year:
        data = data[data['release_year'] == year]
    #Takes a movie type, and filters to only show based on that type
    if content_type:
        data = data[data['type'] == content_type]
    return data

#Creating a genre chart
@app.callback(Output("genre_chart", "figure"),
              [Input("year_filter", "value"), Input("type_filter", "value")])
def genre_update(year, content_type):
    dd = get_data_filtered(year, content_type)
    top_genre = dd["genre"].value_counts().nlargest(10)
    return px.bar(
        x=top_genre.index,
        y=top_genre.values,
        title="Top 10 Genres",
        labels={"x": "Genre", "y": "Count"}
    )

#Timeline chart callback
@app.callback(Output("timeline_chart", "figure"),
              [Input("year_filter", "value"), Input("type_filter", "value")])
def update_timeline_chart(year, content_type):
    dd = get_data_filtered(year, content_type)
    timeline = dd['date_added'].dropna().dt.to_period('M').value_counts().sort_index()
    timeline_df = timeline.reset_index()
    timeline_df.columns = ['Month', 'Count']
    timeline_df['Month'] = timeline_df['Month'].astype(str)
    return px.line(timeline_df, x='Month', y='Count', title='Content Added Over Time')

#Pie chart for type of contents:
@app.callback(Output("type_pie_chart", "figure"),
              Input("year_filter", "value"))
def update_type_pie(year):
    dd = get_data_filtered(year, None)
    return px.pie(dd, names='type', title='Movies vs TV Shows')

#Duration trends chart (scatter)
@app.callback(Output("duration_scatter", "figure"),
              Input("type_filter", "value"))
def update_duration_scatter(content_type):
    dd = get_data_filtered(None, content_type)
    if content_type == "Movie":
        dd["minutes"] = dd["duration"].str.extract(r"(\d+)").astype(float)
    else:
        dd["minutes"] = dd["duration"].str.extract(r"(\d+)").astype(float) * 45
    return px.scatter(dd, x='release_year', y='minutes', color='type',
                      title='Duration Trends', labels={'minutes': 'Duration (min)'})

#Choropleth map:
@app.callback(Output('country_map', 'figure'),
              [Input('year_filter', 'value'), Input('type_filter', 'value')])
def update_country_map(year, content_type):
    dd = get_data_filtered(year, content_type)
    countries = dd['country'].str.split(', ')
    flat_countries = [c for sublist in countries.dropna() for c in sublist]
    country_counts = pd.Series(flat_countries).value_counts().reset_index()
    country_counts.columns = ['country', 'count']
    return px.choropleth(country_counts, locations='country',
                         locationmode='country names', color='count',
                         color_continuous_scale='Reds', title='Content by Country')

if __name__ == '__main__':
    app.run(debug=True)
