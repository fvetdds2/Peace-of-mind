"""
CSV-backed storage for Peace of Mind.
Kept deliberately simple: one CSV per table under data/.
"""
from pathlib import Path
import pandas as pd

DATA_ROOT = Path("data")
DATA_ROOT.mkdir(exist_ok=True)

# Each signed-in user gets their own folder under data/, so one person's
# records are never readable from another person's session.
_CURRENT_USER = "default"


def _safe_name(username: str) -> str:
    """Filesystem-safe folder name derived from a username."""
    import re
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", (username or "default").strip().lower())
    return cleaned or "default"


def set_user(username: str) -> None:
    """Point all reads/writes at this user's private folder."""
    global _CURRENT_USER
    _CURRENT_USER = _safe_name(username)
    user_dir().mkdir(parents=True, exist_ok=True)


def current_user() -> str:
    return _CURRENT_USER


def user_dir() -> Path:
    return DATA_ROOT / _CURRENT_USER


def _file(name: str) -> Path:
    return user_dir() / f"{name}.csv"

# Reserved category name used to stash the month's planned income in the budgets table.
PLANNED_INCOME_KEY = "__planned_income__"

TABLES = ["accounts", "expenses", "income", "budgets", "properties", "goals"]

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
    "goals": [
        "name", "target_amount", "target_date",
        "track_type", "track_target", "manual_current", "created_at",
    ],
}

DATE_COLS = {
    "accounts": ["date"], "expenses": ["date"], "income": ["date"],
    "budgets": [], "properties": ["last_updated"],
    "goals": ["target_date", "created_at"],
}

TEXT_COLS = {
    "accounts": ["account_name", "category"],
    "expenses": ["category", "description"],
    "income": ["source"],
    "budgets": ["month", "category"],
    "properties": ["address", "nickname", "notes"],
    "goals": ["name", "track_type", "track_target"],
}

NUM_COLS = {
    "accounts": ["balance"],
    "expenses": ["amount"],
    "income": ["amount"],
    "budgets": ["budget_amount"],
    "properties": ["zillow_estimate", "redfin_estimate", "homes_estimate",
                    "rentcast_estimate", "suggested_rent", "mortgage_balance"],
    "goals": ["target_amount", "manual_current"],
}


import streamlit as st


@st.cache_data(show_spinner=False)
def _read_csv_cached(name: str, path_str: str, mtime: float) -> pd.DataFrame:
    """
    Cached CSV parse keyed on (file, modification time). When the file is
    written, its mtime changes, which busts the cache automatically — so
    edits always show up, but unchanged files parse only once.
    """
    cols = SCHEMAS[name]
    df = pd.read_csv(path_str)
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[cols]
    for c in DATE_COLS[name]:
        df[c] = pd.to_datetime(df[c], errors="coerce", format="mixed")
    for c in NUM_COLS[name]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    for c in TEXT_COLS.get(name, []):
        df[c] = df[c].fillna("").astype(str).replace("nan", "")
    if name in {"expenses", "income"} and not df.empty:
        df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def load_table(name: str) -> pd.DataFrame:
    path = _file(name)
    cols = SCHEMAS[name]
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=cols)
    return _read_csv_cached(name, str(path), path.stat().st_mtime).copy()


def save_table(name: str, df: pd.DataFrame) -> None:
    cols = SCHEMAS[name]
    out = df[[c for c in cols if c in df.columns]].copy()
    for c in DATE_COLS[name]:
        out[c] = pd.to_datetime(out[c], errors="coerce", format="mixed").dt.strftime("%Y-%m-%d")
    out.to_csv(_file(name), index=False)


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


def net_worth_history() -> pd.DataFrame:
    """
    Net worth reconstructed at each date an account balance was updated.
    Forward-fills each account's most recent known balance so updates
    replace prior values rather than stacking as if every entry were a
    new deposit.
    """
    accounts = load_table("accounts")
    if accounts.empty:
        return pd.DataFrame(columns=["date", "value"])
    df = accounts.copy()
    df["signed_balance"] = df.apply(
        lambda r: r["balance"] if str(r["category"]).lower() not in ("credit card", "loan", "liability") else -r["balance"],
        axis=1,
    )
    pivot = df.pivot_table(index="date", columns="account_name", values="signed_balance", aggfunc="last")
    pivot = pivot.sort_index().ffill()
    totals = pivot.sum(axis=1).reset_index()
    totals.columns = ["date", "value"]
    return totals


def account_history(account_name: str) -> pd.DataFrame:
    accounts = load_table("accounts")
    df = accounts[accounts["account_name"] == account_name].sort_values("date")[["date", "balance"]]
    return df.rename(columns={"balance": "value"})


def project_goal(history_df: pd.DataFrame, target: float):
    """
    Returns (current_value, status):
    - status == 'reached' if current already meets target
    - status == a datetime.date if a projection could be made from trend
    - status is None if not enough data, or trend is flat/declining
    """
    import numpy as np
    import datetime as _dt

    if history_df.empty:
        return None, None
    current = float(history_df["value"].iloc[-1])
    if current >= target:
        return current, "reached"
    if len(history_df) < 2:
        return current, None
    x = history_df["date"].map(pd.Timestamp.toordinal).values.astype(float)
    y = history_df["value"].values.astype(float)
    slope, _ = np.polyfit(x, y, 1)
    if slope <= 0:
        return current, None
    days_needed = (target - current) / slope
    if days_needed > 365 * 50:  # implausibly far out — not a meaningful projection
        return current, None
    projected_date = _dt.date.today() + _dt.timedelta(days=days_needed)
    return current, projected_date


def goal_current_value(goal_row):
    """Returns (current_value, history_df) for a goal based on its tracking type."""
    track_type = goal_row["track_type"]
    if track_type == "net_worth":
        hist = net_worth_history()
        current = net_worth_summary()["net_worth"] if hist.empty else float(hist["value"].iloc[-1])
        return current, hist
    elif track_type == "account":
        hist = account_history(goal_row["track_target"])
        current = float(hist["value"].iloc[-1]) if not hist.empty else 0.0
        return current, hist
    else:  # manual
        current = goal_row["manual_current"] if pd.notna(goal_row["manual_current"]) else 0.0
        return float(current), pd.DataFrame(columns=["date", "value"])


def asset_allocation() -> dict:
    """Returns {label: amount} for assets only (liquid categories + real estate equity)."""
    accounts = load_table("accounts")
    properties = load_table("properties")
    alloc = {}

    if not accounts.empty:
        latest = accounts.sort_values("date").groupby("account_name").tail(1)
        for _, r in latest.iterrows():
            cat = str(r["category"]).lower()
            if cat in ("credit card", "loan", "liability"):
                continue
            bal = r["balance"] if pd.notna(r["balance"]) else 0.0
            if bal <= 0:
                continue
            label = cat.title() if cat != "nan" else "Other"
            alloc[label] = alloc.get(label, 0.0) + float(bal)

    if not properties.empty:
        property_total = sum(property_avg_value(r) for _, r in properties.iterrows())
        if property_total > 0:
            alloc["Real Estate"] = alloc.get("Real Estate", 0.0) + property_total

    return alloc


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


def month_totals(month: str) -> dict:
    """Income and expense totals for a 'YYYY-MM' month."""
    income = load_table("income")
    expenses = load_table("expenses")
    inc = float(income[income["month"] == month]["amount"].sum()) if not income.empty else 0.0
    exp = float(expenses[expenses["month"] == month]["amount"].sum()) if not expenses.empty else 0.0
    return {"income": inc, "expenses": exp, "net": inc - exp}


def income_total() -> float:
    df = load_table("income")
    return float(df["amount"].sum()) if not df.empty else 0.0


def budget_vs_actual(month: str):
    """month format 'YYYY-MM'. Returns DataFrame of category, budget, actual, remaining."""
    budgets = load_table("budgets")
    expenses = load_table("expenses")
    b = budgets[budgets["month"] == month]
    b = b[b["category"] != PLANNED_INCOME_KEY][["category", "budget_amount"]]
    if not expenses.empty:
        exp_month = expenses[expenses["month"] == month]
        actual = exp_month.groupby("category")["amount"].sum().reset_index()
        actual.columns = ["category", "actual"]
    else:
        actual = pd.DataFrame(columns=["category", "actual"])
    merged = pd.merge(b, actual, on="category", how="outer").fillna(0)
    merged["remaining"] = merged["budget_amount"] - merged["actual"]
    return merged


def get_planned_income(month: str) -> float:
    budgets = load_table("budgets")
    row = budgets[(budgets["month"] == month) & (budgets["category"] == PLANNED_INCOME_KEY)]
    if row.empty:
        return 0.0
    val = row["budget_amount"].iloc[0]
    return float(val) if pd.notna(val) else 0.0


def set_planned_income(month: str, amount: float) -> None:
    budgets = load_table("budgets")
    mask = (budgets["month"] == month) & (budgets["category"] == PLANNED_INCOME_KEY)
    if mask.any():
        budgets.loc[mask, "budget_amount"] = amount
        save_table("budgets", budgets)
    else:
        append_row("budgets", {"month": month, "category": PLANNED_INCOME_KEY, "budget_amount": amount})


def budget_line_items(month: str):
    """Real budget line items for a month (excludes the reserved planned-income row)."""
    budgets = load_table("budgets")
    b = budgets[(budgets["month"] == month) & (budgets["category"] != PLANNED_INCOME_KEY)]
    return b.sort_values("category").reset_index(drop=True)
