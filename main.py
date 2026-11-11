import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Настройки
countries = ["RUS", "USA", "CHN", "IND", "BRA"]

indicators = {
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "SP.POP.TOTL": "population",
    "FP.CPI.TOTL.ZG": "inflation_pct",
    "SL.UEM.TOTL.ZS": "unemployment_pct",
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
}

url = (
    "https://api.worldbank.org/v2/country/"
    + ";".join(countries)
    + "/indicator/"
    + ";".join(indicators)
)

params = {
    "format": "json",
    "source": 2,
    "date": "2015:2025",
    "per_page": 1000,
    "page": 1,
}

# Автоматические повторы при временных ошибках
session = requests.Session()
retry = Retry(
    total=4,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods={"GET"},
    respect_retry_after_header=True,
)
session.mount("https://", HTTPAdapter(max_retries=retry))

def fetch_page(page):
    params["page"] = page
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected API response: {payload}")

    return payload

# Первая страница и количество страниц
first = fetch_page(1)
pages = int(first[0]["pages"])
records = first[1] or []

# Остальные страницы
for page in range(2, pages + 1):
    result = fetch_page(page)
    records.extend(result[1] or [])

# Приведение к табличному виду
rows = []

for item in records:
    rows.append({
        "country_code": item["countryiso3code"],
        "country_name": item["country"]["value"],
        "year": int(item["date"]),
        "indicator_code": item["indicator"]["id"],
        "indicator_name": indicators[item["indicator"]["id"]],
        "value": item["value"],
    })

df = pd.DataFrame(rows)
df["value"] = pd.to_numeric(df["value"], errors="coerce")
df["loaded_at"] = pd.Timestamp.now(tz="UTC")

df.to_csv("world_bank.csv", index=False, encoding="utf-8-sig")

print(f"Загружено строк: {len(df)}")
print(df.head())
