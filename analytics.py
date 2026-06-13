from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


REQUIRED_COLUMNS = [
    "Player Name",
    "Team",
    "Grade",
    "Position",
    "Event Name",
    "Event Date",
    "Growth Upside",
    "Overall Score",
]

NUMERIC_COLUMNS = ["Growth Upside", "Overall Score"]

DEFAULT_DATA_FILES = [
    Path("bball_talent_index/scouting_database.csv"),
    Path("bball_talent_index/AAU_Scouting_System.xlsx"),
]


def _extract_event_start_date(value: object) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if not text:
        return pd.NaT

    return pd.to_datetime(text.split(" - ", maxsplit=1)[0].strip(), errors="coerce")


def _normalize_workbook(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    evaluations = sheets["Player_Evaluations"].copy()
    events = sheets["Event_Log"].copy()

    evaluations.columns = [str(column).strip() for column in evaluations.columns]
    events.columns = [str(column).strip() for column in events.columns]

    merged = evaluations.merge(events[["Event ID", "Event Name", "Date"]], on="Event ID", how="left")
    return pd.DataFrame(
        {
            "Player Name": merged["Player Name"],
            "Team": merged["Team"],
            "Grade": merged["Level"],
            "Position": merged["Position"],
            "Event Name": merged["Event Name"],
            "Event Date": merged["Date"].map(_extract_event_start_date),
            "Growth Upside": merged["Growth Upside (1-5)"],
            "Overall Score": merged["Overall Grade"],
        }
    )


def _read_dataframe(source) -> pd.DataFrame:
    source_name = getattr(source, "name", str(source))
    suffix = Path(source_name).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source)

    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(source, sheet_name=None)
        normalized = {str(sheet_name).strip(): dataframe for sheet_name, dataframe in sheets.items()}

        if "Player_Evaluations" in normalized and "Event_Log" in normalized:
            return _normalize_workbook(normalized)

        for dataframe in normalized.values():
            candidate = dataframe.copy()
            candidate.columns = [str(column).strip() for column in candidate.columns]
            if all(column in candidate.columns for column in REQUIRED_COLUMNS):
                return candidate

    raise ValueError("Unsupported file type. Upload a CSV or Excel scouting database export.")


def prepare_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [str(column).strip() for column in df.columns]

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing_text}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Event Date"] = pd.to_datetime(df["Event Date"], errors="coerce")

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in ["Player Name", "Team", "Grade", "Position", "Event Name"]:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()
        df.loc[df[column] == "", column] = "Unknown"

    df = df.dropna(subset=["Event Name", "Overall Score", "Growth Upside"])
    df = df.sort_values(["Event Date", "Event Name", "Player Name"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_data_from_path(path: str) -> pd.DataFrame:
    return prepare_dataframe(_read_dataframe(path))


def load_data_from_upload(uploaded_file) -> pd.DataFrame:
    return prepare_dataframe(_read_dataframe(uploaded_file))


def find_default_data_file() -> Path | None:
    for path in DEFAULT_DATA_FILES:
        if path.exists():
            return path
    return None


def load_event_data() -> tuple[pd.DataFrame, str]:
    uploaded_file = st.sidebar.file_uploader(
        "Upload scouting database",
        type=["csv", "xlsx", "xls"],
        help="Upload a scouting database CSV export. Excel files are also supported.",
    )

    if uploaded_file is not None:
        return load_data_from_upload(uploaded_file), uploaded_file.name

    default_file = find_default_data_file()
    if default_file is not None:
        return load_data_from_path(str(default_file)), default_file.name

    raise FileNotFoundError("No data file found. Upload a scouting database export to continue.")


def apply_event_filters(
    df: pd.DataFrame,
    grades: list[str] | None = None,
    positions: list[str] | None = None,
    teams: list[str] | None = None,
) -> pd.DataFrame:
    filtered_df = df.copy()
    filters = {
        "Grade": grades or [],
        "Position": positions or [],
        "Team": teams or [],
    }

    for column, values in filters.items():
        if values:
            filtered_df = filtered_df[filtered_df[column].isin(values)]

    return filtered_df.reset_index(drop=True)
