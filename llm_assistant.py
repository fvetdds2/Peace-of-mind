"""
Chat assistant for Peace of Mind — answers questions about net worth,
spending, budgets, and properties using the person's own data as context.
"""
import streamlit as st
import pandas as pd
import data_store as ds

SYSTEM_PROMPT = """You are a calm, precise personal finance assistant embedded in a net worth
tracker called Peace of Mind. Answer using ONLY the financial data provided below.

Rules:
- Be concrete: cite actual numbers, account names, categories, property nicknames.
- If asked about trends, compare the figures given rather than speculating.
- If asked for advice (e.g. "should I sell"), give balanced, factual considerations —
  note you're not a financial advisor and this isn't a recommendation.
- If the data needed to answer isn't present, say so plainly.
- Keep responses concise: a few sentences or a short list, unless more detail is requested.
"""


def build_financial_context() -> str:
    summary = ds.net_worth_summary()
    accounts = ds.load_table("accounts")
    properties = ds.load_table("properties")
    expenses = ds.load_table("expenses")
    income = ds.load_table("income")

    lines = [
        "=== NET WORTH SUMMARY ===",
        f"Liquid assets (cash/investment accounts): ${summary['liquid_assets']:,.2f}",
        f"Property value (avg of available estimates): ${summary['property_value_total']:,.2f}",
        f"Total assets: ${summary['total_assets']:,.2f}",
        f"Liability accounts (credit cards/loans): ${summary['liabilities_accounts']:,.2f}",
        f"Mortgage balances: ${summary['mortgage_total']:,.2f}",
        f"Total liabilities: ${summary['total_liabilities']:,.2f}",
        f"NET WORTH: ${summary['net_worth']:,.2f}",
        "",
    ]

    if not accounts.empty:
        lines.append("=== ACCOUNTS (latest balance each) ===")
        latest = accounts.sort_values("date").groupby("account_name").tail(1)
        for _, r in latest.iterrows():
            lines.append(f"- {r['account_name']} ({r['category']}): ${r['balance']:,.2f}")
        lines.append("")

    if not properties.empty:
        lines.append("=== PROPERTIES ===")
        for _, r in properties.iterrows():
            avg_val = ds.property_avg_value(r)
            mortgage = r["mortgage_balance"] if pd.notna(r["mortgage_balance"]) else 0
            rent = r["suggested_rent"] if pd.notna(r["suggested_rent"]) else 0
            lines.append(
                f"- {r['nickname'] or r['address']}: est. value ${avg_val:,.2f}, "
                f"mortgage ${mortgage:,.2f}, "
                f"suggested rent ${rent:,.2f}, "
                f"last updated {r['last_updated']}"
            )
        lines.append("")

    if not income.empty:
        lines.append("=== INCOME (last 6 entries) ===")
        for _, r in income.sort_values("date").tail(6).iterrows():
            lines.append(f"- {r['date'].date()}: {r['source']} — ${r['amount']:,.2f}")
        lines.append("")

    if not expenses.empty:
        lines.append("=== SPENDING BY CATEGORY (all-time) ===")
        by_cat = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
        for cat, amt in by_cat.items():
            lines.append(f"- {cat}: ${amt:,.2f}")
        lines.append("")

    return "\n".join(lines)


def _safe_secret(key: str, default=None):
    """st.secrets.get() raises if no secrets.toml exists at all; make it safe."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def _get_provider():
    return (_safe_secret("PROVIDER", "groq") or "groq").lower()


def ask(question: str, chat_history: list) -> str:
    provider = _get_provider()
    context = build_financial_context()
    if provider == "groq":
        return _call_groq(question, context, chat_history)
    return _call_anthropic(question, context, chat_history)


def _build_messages(question, context, chat_history):
    messages = [{"role": t["role"], "content": t["content"]} for t in chat_history[-8:]]
    messages.append({"role": "user", "content": f"FINANCIAL DATA:\n{context}\n\nQUESTION: {question}"})
    return messages


def _call_anthropic(question, context, chat_history):
    import anthropic
    api_key = _safe_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return "⚠️ No ANTHROPIC_API_KEY found in Streamlit secrets."
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=_build_messages(question, context, chat_history),
    )
    return resp.content[0].text


def _call_groq(question, context, chat_history):
    import requests
    api_key = _safe_secret("GROQ_API_KEY")
    if not api_key:
        return "⚠️ No GROQ_API_KEY found in Streamlit secrets."
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + _build_messages(question, context, chat_history)
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "llama-3.3-70b-versatile", "messages": messages, "max_tokens": 600},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
