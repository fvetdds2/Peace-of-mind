"""
CSV-backed storage for Peace of Mind.
Kept deliberately simple: one CSV per table under data/.
"""
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FILES = {
    "accounts": DATA_DIR / "accounts.csv",
    "expenses": DATA_DIR / "expenses.csv",
    "income": DATA_DIR / "income.csv",
    "budgets": DATA_DIR / "budgets.csv",
    "properties": DATA_DIR / "properties.csv",
}

SCHEMAS = {
    "accounts": ["date", "account_name", "category", "balance"],
    "expenses": ["date", "category", "description", "amount"],
    "income": ["date", "source", "amount"],
    "budgets": ["month", "category", "budget_amount"],
    "properties": [
        "address", "nickname",
        "zillow_estimate", "redfin_estimate", "homes_estimate", "rentcast_estimate",
        "suggested_rent", "mortgage_balance", "last_updated", "notes",
    ],
}

DATE_COLS = {
    "accounts": ["date"], "expenses": ["date"], "income": ["date"],
    "budgets": [], "properties": ["last_updated"],
}

NUM_COLS = {
    "accounts": ["balance"],
    "expenses": ["amount"],
    "income": ["amount"],
    "budgets": ["budget_amount"],
    "properties": ["zillow_estimate", "redfin_estimate", "homes_estimate",
                    "rentcast_estimate", "suggested_rent", "mortgage_balance"],
}


def load_table(name: str) -> pd.DataFrame:
    path = FILES[name]
    cols = SCHEMAS[name]
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[cols]
    for c in DATE_COLS[name]:
        df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed")
    for c in NUM_COLS[name]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    if name in {"expenses", "income"} and not df.empty:
        df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def save_table(name: str, df: pd.DataFrame) -> None:
    cols = SCHEMAS[name]
    out = df[[c for c in cols if c in df.columns]].copy()
    for c in DATE_COLS[name]:
        out[c] = pd.to_datetime(out[c], errors="coerce", format="mixed").dt.strftime("%Y-%m-%d")
    out.to_csv(FILES[name], index=False)


def append_row(name: str, row: dict) -> None:
    df = load_table(name)
    new = pd.DataFrame([row])
    df = pd.concat([df[SCHEMAS[name]], new], ignore_index=True)
    save_table(name, df)


def update_row(name: str, index: int, updates: dict) -> None:
    df = load_table(name)
    for k, v in updates.items():
        df.at[index, k] = v
    save_table(name, df)


def delete_row(name: str, index: int) -> None:
    df = load_table(name)
    df = df.drop(index=index).reset_index(drop=True)
    save_table(name, df)


# ---------------- Derived values ----------------

def property_avg_value(row) -> float:
    """Average available valuation estimates, ignoring missing/zero values."""
    vals = []
    for c in ["zillow_estimate", "redfin_estimate", "homes_estimate", "rentcast_estimate"]:
        v = row.get(c)
        if pd.notna(v) and v > 0:
            vals.append(float(v))
    return sum(vals) / len(vals) if vals else 0.0


def net_worth_summary():
    accounts = load_table("accounts")
    properties = load_table("properties")

    # latest balance per account
    liquid_assets = 0.0
    liabilities_accounts = 0.0
    if not accounts.empty:
        latest = accounts.sort_values("date").groupby("account_name").tail(1)
        for _, r in latest.iterrows():
            bal = r["balance"] if pd.notna(r["balance"]) else 0.0
            if str(r["category"]).lower() in ("credit card", "loan", "liability"):
                liabilities_accounts += abs(bal)
            else:
                liquid_assets += bal

    property_value_total = 0.0
    mortgage_total = 0.0
    if not properties.empty:
        property_value_total = properties.apply(property_avg_value, axis=1).sum()
        mortgage_total = properties["mortgage_balance"].fillna(0).sum()

    total_assets = liquid_assets + property_value_total
    total_liabilities = liabilities_accounts + mortgage_total
    net_worth = total_assets - total_liabilities

    return {
        "liquid_assets": liquid_assets,
        "property_value_total": property_value_total,
        "total_assets": total_assets,
        "liabilities_accounts": liabilities_accounts,
        "mortgage_total": mortgage_total,
        "total_liabilities": total_liabilities,
        "net_worth": net_worth,
    }


def budget_vs_actual(month: str):
    """month format 'YYYY-MM'. Returns DataFrame of category, budget, actual, remaining."""
    budgets = load_table("budgets")
    expenses = load_table("expenses")
    b = budgets[budgets["month"] == month][["category", "budget_amount"]]
    if not expenses.empty:
        exp_month = expenses[expenses["month"] == month]
        actual = exp_month.groupby("category")["amount"].sum().reset_index()
        actual.columns = ["category", "actual"]
    else:
        actual = pd.DataFrame(columns=["category", "actual"])
    merged = pd.merge(b, actual, on="category", how="outer").fillna(0)
    merged["remaining"] = merged["budget_amount"] - merged["actual"]
    return merged
