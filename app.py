from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import apply_event_filters, load_event_data
from event_scoring import calculate_event_summary, comparison_metrics, get_event_detail


st.set_page_config(page_title="Event Talent Index", layout="wide")


def render_overview(summary_df: pd.DataFrame) -> None:
    best_event = summary_df.iloc[0]
    col_one, col_two, col_three, col_four = st.columns(4)
    col_one.metric("Events Evaluated", int(summary_df["Event Name"].nunique()))
    col_two.metric("Average Talent Index", f"{summary_df['Talent Index'].mean():.2f}")
    col_three.metric("Highest-Ranked Event", str(best_event["Event Name"]))
    col_four.metric("Top Event Grade", str(best_event["Grade"]))


def render_leaderboard(summary_df: pd.DataFrame) -> None:
    st.subheader("Event Rankings Leaderboard")
    fig = px.bar(
        summary_df.sort_values("Talent Index", ascending=True),
        x="Talent Index",
        y="Event Name",
        color="Grade",
        orientation="h",
        text="Talent Index",
        color_discrete_sequence=["#0f4c5c", "#2c7da0", "#468faf", "#89c2d9", "#d9ed92"],
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(margin=dict(l=0, r=20, t=20, b=0))
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        summary_df[
            [
                "Event Name",
                "Talent Index",
                "Grade",
                "Players Evaluated",
                "Average Overall Score",
                "Average Growth Upside",
                "Top Performers",
                "Most Promising Prospects",
                "Position Breakdown",
            ]
        ],
        hide_index=True,
        width="stretch",
    )


def render_distributions(summary_df: pd.DataFrame) -> None:
    chart_one, chart_two = st.columns(2)

    with chart_one:
        st.subheader("Talent Distribution")
        fig = px.histogram(summary_df, x="Talent Index", nbins=12, color_discrete_sequence=["#1d3557"])
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, width="stretch")

    with chart_two:
        st.subheader("Upside Distribution")
        fig = px.box(summary_df, y="Average Growth Upside", points="all", color_discrete_sequence=["#e76f51"])
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, width="stretch")


def render_event_detail(df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    st.subheader("Event Comparison Dashboard")
    selected_events = st.multiselect(
        "Select events to compare",
        options=summary_df["Event Name"].tolist(),
        default=summary_df["Event Name"].head(min(3, len(summary_df))).tolist(),
    )

    if selected_events:
        metrics_df = comparison_metrics(summary_df, selected_events)
        comparison_fig = px.line_polar(
            metrics_df,
            r="Value",
            theta="Metric",
            color="Event Name",
            line_close=True,
        )
        comparison_fig.update_layout(margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(comparison_fig, width="stretch")

    selected_event = st.selectbox("Inspect an event", options=summary_df["Event Name"].tolist())
    detail = get_event_detail(df, selected_event)

    metric_one, metric_two, metric_three, metric_four = st.columns(4)
    metric_one.metric("Talent Index", f"{detail['Talent Index']:.2f}")
    metric_two.metric("Grade", str(detail["Grade"]))
    metric_three.metric("Players Evaluated", int(detail["Players Evaluated"]))
    metric_four.metric("Elite Player Density", f"{detail['Elite Player Density']:.2f}%")

    info_one, info_two = st.columns(2)
    with info_one:
        st.markdown(f"**Top Performers**\n\n{detail['Top Performers']}")
        st.markdown(f"**Most Promising Prospects**\n\n{detail['Most Promising Prospects']}")
    with info_two:
        st.markdown(f"**Position Breakdown**\n\n{detail['Position Breakdown']}")
        st.markdown(
            f"**Scoring Inputs**\n\n"
            f"Average Overall Score: {detail['Average Overall Score']:.2f}  \n"
            f"Average Growth Upside: {detail['Average Growth Upside']:.2f}  \n"
            f"Event Depth Score: {detail['Event Depth Score']:.2f}"
        )

    st.dataframe(
        detail["event_df"][["Player Name", "Team", "Grade", "Position", "Growth Upside", "Overall Score"]],
        hide_index=True,
        width="stretch",
    )


def main() -> None:
    st.title("Event Talent Index")
    st.write("Evaluate basketball tournaments by talent concentration, upside, diversity, and roster depth.")

    try:
        df, source_name = load_event_data()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.success(f"Loaded data source: {source_name}")
    st.sidebar.header("Filters")
    selected_grades = st.sidebar.multiselect("Grade", options=sorted(df["Grade"].unique()))
    selected_positions = st.sidebar.multiselect("Position", options=sorted(df["Position"].unique()))
    selected_teams = st.sidebar.multiselect("Team", options=sorted(df["Team"].unique()))

    filtered_df = apply_event_filters(df, grades=selected_grades, positions=selected_positions, teams=selected_teams)
    if filtered_df.empty:
        st.warning("No evaluations match the selected filters.")
        st.stop()

    summary_df = calculate_event_summary(filtered_df)
    if summary_df.empty:
        st.warning("No event summaries could be calculated from the filtered data.")
        st.stop()

    render_overview(summary_df)
    render_leaderboard(summary_df)
    render_distributions(summary_df)
    render_event_detail(filtered_df, summary_df)


if __name__ == "__main__":
    main()
