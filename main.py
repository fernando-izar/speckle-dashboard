import streamlit as st
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
import pandas as pd
import plotly.express as px
from decouple import config

API_TOKEN = config("TOKEN")
print(API_TOKEN)

# PAGE CONFIG
st.set_page_config(page_title="Specke Stream Activity", page_icon="")

# CONTAINERS
header = st.container()
input = st.container()
viewer = st.container()
report = st.container()
graphs = st.container()

# HEADER
# Page Header
with header:
    st.title("Atividade do App Speckle Stream")
# about app
with header.expander("About this app", expanded=True):
    st.markdown(
        "Este é um aplicativo inicial usando Streamlit. O objetivo é entender como interagir com a API do Speckle usando SpecklePy"
    )

# INPUTS
with input:
    st.subheader("Inputs")

    # Columns for inputs
    serverCol, tokenCol = st.columns([1, 2])
    # user input boxes
    speckleServer = serverCol.text_input("Server URL", "speckle.xyz")
    speckleToken = tokenCol.text_input("Speckle Token", API_TOKEN)

    # CLIENT
    client = SpeckleClient(host=speckleServer)
    # get account from token
    account = get_account_from_token(speckleToken, speckleServer)
    # Authenticate
    client.authenticate_with_account(account)

    # streams list
    streams = client.stream.list()
    streamNames = [s.name for s in streams]
    # Dropdown for stream selection
    sName = st.selectbox(label="Select your streams", options=streamNames)
    # Selected Stream
    stream = client.stream.search(sName)[0]
    # Stream Branches
    branches = client.branch.list(stream.id)
    # Stream Commits
    commits = client.commit.list(stream.id, limit=100)


# DEFINITIONS
# Python list to markdown list
def listToMarkdown(list, column):
    list = ["- " + i + "\n" for i in list]
    list = "".join(list)
    return column.markdown(list)


# creates an iframe from commit
def commit2viewer(stream, commit):
    embed_src = "https://speckle.xyz/embed?stream=" + stream.id + "&commit=" + commit.id
    return st.components.v1.iframe(src=embed_src, height=400)


# VIEWER
with viewer:
    st.subheader("Último Commit")
    commit2viewer(stream, commits[0])

# REPORT
with report:
    st.subheader("Estatísticas")
    # Colums for cards
    branchCol, commitCol, connectCol, contributorCol = st.columns(4)

    # Branch Card
    branchCol.metric(label="Número de branches", value=stream.branches.totalCount)
    # List of branches
    listToMarkdown([b.name for b in branches], branchCol)

    # Commit Card
    commitCol.metric(label="Numero de Commits", value=len(commits))

    # Connector Card
    # Connector list
    connectorList = [c.sourceApplication for c in commits]
    # Connector names
    connectorNames = list(dict.fromkeys(connectorList))
    # Numbers of connectors
    connectCol.metric(
        label="Número de conectores", value=len(dict.fromkeys(connectorList))
    )
    # Connectors list
    listToMarkdown(connectorNames, connectCol)

    # Contributor Card
    contributorCol.metric(
        label="Número de colaboradores", value=len(stream.collaborators)
    )
    # Contributor names
    contributorNames = list(dict.fromkeys([col.name for col in stream.collaborators]))
    # Contributor list
    listToMarkdown(contributorNames, contributorCol)

# Graphs
with graphs:
    st.subheader("Gráficos")
    # columns for charts
    branch_graph_col, connector_graph_col, collaborator_graph_col = st.columns(
        [2, 1, 1]
    )

    # BRANCH GRAPH
    # Branch count
    branch_counts = pd.DataFrame([[b.name, b.commits.totalCount] for b in branches])
    # Rename columns
    branch_counts.columns = ["branchName", "totalCommits"]
    # Create graph
    branch_count_graph = px.bar(
        branch_counts,
        x=branch_counts.branchName,
        y=branch_counts.totalCommits,
        color=branch_counts.branchName,
    )
    branch_count_graph.update_layout(
        showlegend=False,
        height=220,
        margin=dict(l=1, r=1, t=1, b=1),
    )
    branch_graph_col.plotly_chart(branch_count_graph, use_container_width=True)

    # CONNECTOR CHART
    commits = pd.DataFrame.from_dict([c.dict() for c in commits])
    # Get apps from dataframe
    apps = commits["sourceApplication"]
    # Reset index apps
    apps = apps.value_counts().reset_index()
    # Rename columns
    apps.columns = ["app", "count"]
    # Donut chart
    fig = px.pie(apps, names=apps["app"], values=apps["count"], hole=0.5)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=2, r=2, t=2, b=2),
        height=200,
    )
    connector_graph_col.plotly_chart(fig, use_container_width=True)

    # COLLABORATOR CHART
    authors = commits["authorName"].value_counts().reset_index()
    # Rename columns
    authors.columns = ["Autor", "Contagem"]
    # Create chart
    authorFig = px.pie(
        authors, names=authors["Autor"], values=authors["Contagem"], hole=0.5
    )
    authorFig.update_layout(
        showlegend=False,
        margin=dict(l=2, r=2, t=2, b=2),
        height=200,
    )
    collaborator_graph_col.plotly_chart(authorFig, use_container_width=True)
