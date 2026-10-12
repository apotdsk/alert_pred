"""Project configuration constants."""

from pathlib import Path

RANDOM_SEED = 42
LOCAL_TIMEZONE = "Europe/Kyiv"
SOURCE_URL = ("https://raw.githubusercontent.com/Vadimkin/"
              "ukrainian-air-raid-sirens-dataset/master/datasets/official_data_en.csv")
VOLUNTEER_SOURCE_URL = ("https://raw.githubusercontent.com/Vadimkin/"
                        "ukrainian-air-raid-sirens-dataset/master/datasets/volunteer_data_en.csv")
RAW_DATA_PATH = Path("data/raw/official_data_en.csv")
VOLUNTEER_RAW_DATA_PATH = Path("data/raw/volunteer_data_en.csv")
AUDIT_PATH = Path("outputs/data_audit.md")
EDA_NOTES_PATH = Path("outputs/eda_notes.md")
FIGURES_DIR = Path("outputs/figures")
PANEL_PATH = Path("data/processed/panel.csv")
REFORM_DATES_PATH = Path("data/processed/reform_dates.csv")
EPISODE_MERGE_TOLERANCE_SECONDS = 60
BUSINESS_START_HOUR = 6
BUSINESS_END_HOUR = 22

# Exactly 23 forecast units. Values are exact source oblast and capital-name stem.
# Kyiv City and Kyiv oblast share the Kyiv forecast, but only Kyiv City records feed it.
UNIT_AREAS: dict[str, tuple[str, str]] = {
    "Cherkasy": ("Cherkaska oblast", "Cherkask"),
    "Chernihiv": ("Chernihivska oblast", "Chernihiv"),
    "Chernivtsi": ("Chernivetska oblast", "Cherniv"),
    "Dnipro": ("Dnipropetrovska oblast", "Dnipro"),
    "Donetsk": ("Donetska oblast", "Kramatorsk"),
    "Ivano-Frankivsk": ("Ivano-Frankivska oblast", "Ivano-Frankiv"),
    "Kharkiv": ("Kharkivska oblast", "Kharkiv"),
    "Kherson": ("Khersonska oblast", "Kherson"),
    "Khmelnytskyi": ("Khmelnytska oblast", "Khmelnytsk"),
    "Kropyvnytskyi": ("Kirovohradska oblast", "Kropyvnytsk"),
    "Kyiv": ("Kyiv City", "Kyiv"),
    "Lutsk": ("Volynska oblast", "Lutsk"),
    "Lviv": ("Lvivska oblast", "Lviv"),
    "Mykolaiv": ("Mykolaivska oblast", "Mykolaiv"),
    "Odesa": ("Odeska oblast", "Odes"),
    "Poltava": ("Poltavska oblast", "Poltav"),
    "Rivne": ("Rivnenska oblast", "Rivn"),
    "Sumy": ("Sumska oblast", "Sum"),
    "Ternopil": ("Ternopilska oblast", "Ternopil"),
    "Uzhhorod": ("Zakarpatska oblast", "Uzhhorod"),
    "Vinnytsia": ("Vinnytska oblast", "Vinnyts"),
    "Zaporizhzhia": ("Zaporizka oblast", "Zaporiz"),
    "Zhytomyr": ("Zhytomyrska oblast", "Zhytomyr"),
}
FORECAST_UNITS = tuple(UNIT_AREAS)
