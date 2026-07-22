"""
Peace of Mind — Personal Finance & Net Worth Tracker
Accounts · Expenses · Income · Budgets · Properties (with automated
RentCast valuation refresh) · AI chat assistant
"""
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

import data_store as ds
import valuation
import llm_assistant

st.set_page_config(page_title="Peace of Mind", page_icon="🕊️", layout="wide")

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* kill default Streamlit chrome noise */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2.5rem; max-width: 880px; }

    /* remove every default bordered card */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: none !important;
        border-top: 1px solid #E8E9EC !important;
        border-radius: 0 !important;
        padding: 20px 0 !important;
    }
    div[data-testid="stMetric"] {
        background: none;
        border: none;
        padding: 0;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #8A8F98;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #16181D;
        font-variant-numeric: tabular-nums;
    }

    /* hero net worth block */
    .hero-label {
        font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase;
        color: #8A8F98; font-weight: 600; margin-bottom: 6px;
    }
    .hero-number {
        font-size: 3.4rem; font-weight: 800; color: #16181D;
        letter-spacing: -0.02em; font-variant-numeric: tabular-nums; line-height: 1.05;
    }
    .hero-delta { font-size: 15px; font-weight: 600; margin-top: 8px; }
    .hero-delta.pos { color: #1E9E62; }
    .hero-delta.neg { color: #D64545; }
    .hero-delta.flat { color: #8A8F98; }

    .stat-row { display: flex; gap: 48px; margin-top: 32px; }
    .stat-block .hero-label { margin-bottom: 4px; }
    .stat-block .stat-value {
        font-size: 1.5rem; font-weight: 700; color: #16181D;
        font-variant-numeric: tabular-nums;
    }

    hr, div[data-testid="stDivider"] { border-color: #E8E9EC !important; }

    /* buttons: crisp, low-radius, quiet */
    button[kind="secondary"], button[kind="primary"] {
        border-radius: 6px !important;
        font-weight: 500 !important;
        border: 1px solid #E8E9EC !important;
    }
    button[kind="primary"] {
        background-color: #2F6FED !important;
        border-color: #2F6FED !important;
    }

    /* chat bubbles: subtle, no heavy fill */
    div[data-testid="stChatMessage"] {
        background: #F5F6F8;
        border-radius: 10px;
        border: 1px solid #EEEFF1;
    }

    /* tabs: understated, accent underline only */
    button[data-baseweb="tab"] { font-weight: 500; color: #8A8F98; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #16181D; }
    div[data-baseweb="tab-highlight"] { background-color: #2F6FED !important; height: 2px !important; }
    div[data-baseweb="tab-border"] { background-color: #E8E9EC !important; }

    h1, h2, h3 { letter-spacing: -0.01em; }
</style>
""", unsafe_allow_html=True)

PLOTLY_BLUES = ["#2F6FED", "#7FA6F0", "#B7CCF5", "#16181D", "#5B8CE8", "#0F1218"]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown('<div class="hero-label" style="font-size:13px;">🕊️ PEACE OF MIND</div>', unsafe_allow_html=True)
st.markdown('<p style="color:#8A8F98; margin-top:-8px; margin-bottom:24px;">Your net worth, budget, and properties — with an assistant that knows all of it.</p>', unsafe_allow_html=True)

tabs = st.tabs(["📊 Net Worth", "🏦 Accounts", "🧾 Expenses & Income", "📋 Budget", "🏠 Properties", "💬 Ask the Assistant"])

# ---------------- Net Worth ----------------
with tabs[0]:
    summary = ds.net_worth_summary()
    accounts = ds.load_table("accounts")

    delta_html = ""
    if not accounts.empty:
        history = accounts.groupby("date").apply(
            lambda g: g.apply(
                lambda r: r["balance"] if str(r["category"]).lower() not in ("credit card", "loan", "liability") else -r["balance"],
                axis=1,
            ).sum()
        ).cumsum().reset_index(name="net_worth_delta")
        if len(history) >= 2:
            change = history["net_worth_delta"].iloc[-1] - history["net_worth_delta"].iloc[-2]
            cls = "pos" if change > 0 else ("neg" if change < 0 else "flat")
            arrow = "▲" if change > 0 else ("▼" if change < 0 else "—")
            delta_html = f'<div class="hero-delta {cls}">{arrow} ${abs(change):,.0f} vs previous entry</div>'

    st.markdown(f"""
    <div class="hero-label">Net Worth</div>
    <div class="hero-number">${summary['net_worth']:,.0f}</div>
    {delta_html}
    <div class="stat-row">
        <div class="stat-block">
            <div class="hero-label">Total Assets</div>
            <div class="stat-value">${summary['total_assets']:,.0f}</div>
        </div>
        <div class="stat-block">
            <div class="hero-label">Total Liabilities</div>
            <div class="stat-value">${summary['total_liabilities']:,.0f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    if not accounts.empty:
        st.markdown('<div class="hero-label" style="margin-top:24px;">Trend</div>', unsafe_allow_html=True)
        fig = px.line(history, x="date", y="net_worth_delta", title=None, color_discrete_sequence=[PLOTLY_BLUES[0]])
        fig.update_layout(
            plot_bgcolor="#FAFAFA", paper_bgcolor="#FAFAFA",
            margin=dict(l=0, r=0, t=16, b=0),
            xaxis=dict(showgrid=False, title=None),
            yaxis=dict(showgrid=True, gridcolor="#F0F1F3", title=None),
            font=dict(family="Inter", color="#8A8F98", size=12),
        )
        fig.update_traces(line=dict(width=2.5))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add account balances in the Accounts tab to see your net worth trend.")

# ---------------- Accounts ----------------
with tabs[1]:
    with st.form("add_account", clear_on_submit=True):
        cols = st.columns([2, 1.2, 1, 1])
        acc_name = cols[0].text_input("Account name")
        acc_cat = cols[1].selectbox("Category", ["checking", "savings", "investment", "credit card", "loan", "other"])
        acc_bal = cols[2].number_input("Balance", step=100.0)
        acc_date = cols[3].date_input("Date", value=datetime.date.today())
        if st.form_submit_button("Add / update balance") and acc_name.strip():
            ds.append_row("accounts", {
                "date": acc_date.isoformat(), "account_name": acc_name.strip(),
                "category": acc_cat, "balance": acc_bal,
            })
            st.rerun()

    accounts = ds.load_table("accounts")
    if not accounts.empty:
        latest = accounts.sort_values("date").groupby("account_name").tail(1)
        st.subheader("Current balances")
        st.dataframe(latest[["account_name", "category", "balance", "date"]], use_container_width=True, hide_index=True)

        st.subheader("Full history — edit or delete entries")
        st.caption("Edit any cell directly, or use the 🗑️ icon on a row to delete it, then click Save.")
        edited = st.data_editor(
            accounts.sort_values("date", ascending=False),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "account_name": st.column_config.TextColumn("Account name"),
                "category": st.column_config.SelectboxColumn(
                    "Category", options=["checking", "savings", "investment", "credit card", "loan", "other"]
                ),
                "balance": st.column_config.NumberColumn("Balance", format="$%.2f"),
            },
            key="accounts_editor",
        )
        if st.button("💾 Save changes", key="save_accounts"):
            ds.save_table("accounts", edited)
            st.success("Accounts updated.")
            st.rerun()
    else:
        st.caption("No accounts yet.")

# ---------------- Expenses & Income ----------------
with tabs[2]:
    ecol, icol = st.columns(2)
    with ecol:
        st.subheader("Add expense")
        with st.form("add_expense", clear_on_submit=True):
            e_date = st.date_input("Date", value=datetime.date.today(), key="e_date")
            e_cat = st.text_input("Category", key="e_cat", placeholder="e.g. groceries, rent, travel")
            e_desc = st.text_input("Description", key="e_desc")
            e_amt = st.number_input("Amount", step=10.0, key="e_amt")
            if st.form_submit_button("Add expense") and e_cat.strip():
                ds.append_row("expenses", {
                    "date": e_date.isoformat(), "category": e_cat.strip(),
                    "description": e_desc.strip(), "amount": e_amt,
                })
                st.rerun()
    with icol:
        st.subheader("Add income")
        with st.form("add_income", clear_on_submit=True):
            i_date = st.date_input("Date", value=datetime.date.today(), key="i_date")
            i_src = st.text_input("Source", key="i_src", placeholder="e.g. salary, rental income")
            i_amt = st.number_input("Amount", step=10.0, key="i_amt")
            if st.form_submit_button("Add income") and i_src.strip():
                ds.append_row("income", {"date": i_date.isoformat(), "source": i_src.strip(), "amount": i_amt})
                st.rerun()

    st.divider()
    expenses = ds.load_table("expenses")
    income = ds.load_table("income")

    if not expenses.empty:
        st.subheader("Spending by category")
        by_cat = expenses.groupby("category")["amount"].sum().reset_index()
        fig = px.pie(by_cat, names="category", values="amount", color_discrete_sequence=PLOTLY_BLUES)
        fig.update_layout(paper_bgcolor="#FAFAFA")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Expense log — edit or delete entries")
        st.caption("Edit any cell directly, or use the 🗑️ icon on a row to delete it, then click Save.")
        edited_exp = st.data_editor(
            expenses.sort_values("date", ascending=False).drop(columns=["month"]),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "category": st.column_config.TextColumn("Category"),
                "description": st.column_config.TextColumn("Description"),
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            },
            key="expenses_editor",
        )
        if st.button("💾 Save changes", key="save_expenses"):
            ds.save_table("expenses", edited_exp)
            st.success("Expenses updated.")
            st.rerun()

    if not income.empty:
        st.subheader("Income log — edit or delete entries")
        st.caption("Edit any cell directly, or use the 🗑️ icon on a row to delete it, then click Save.")
        edited_inc = st.data_editor(
            income.sort_values("date", ascending=False).drop(columns=["month"]),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "source": st.column_config.TextColumn("Source"),
                "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            },
            key="income_editor",
        )
        if st.button("💾 Save changes", key="save_income"):
            ds.save_table("income", edited_inc)
            st.success("Income updated.")
            st.rerun()

# ---------------- Budget ----------------
with tabs[3]:
    with st.form("add_budget", clear_on_submit=True):
        cols = st.columns([1, 2, 1])
        b_month = cols[0].text_input("Month (YYYY-MM)", value=datetime.date.today().strftime("%Y-%m"))
        b_cat = cols[1].text_input("Category")
        b_amt = cols[2].number_input("Budget amount", step=50.0)
        if st.form_submit_button("Set budget") and b_cat.strip():
            ds.append_row("budgets", {"month": b_month, "category": b_cat.strip(), "budget_amount": b_amt})
            st.rerun()

    month_pick = st.text_input("View month", value=datetime.date.today().strftime("%Y-%m"))
    bva = ds.budget_vs_actual(month_pick)
    if not bva.empty:
        st.dataframe(bva, use_container_width=True, hide_index=True)
        fig = px.bar(bva, x="category", y=["budget_amount", "actual"], barmode="group",
                     color_discrete_sequence=[PLOTLY_BLUES[3], PLOTLY_BLUES[0]])
        fig.update_layout(plot_bgcolor="#FAFAFA", paper_bgcolor="#FAFAFA")
        st.plotly_chart(fig, use_container_width=True)

    all_budgets = ds.load_table("budgets")
    if not all_budgets.empty:
        st.subheader("All budgets — edit or delete entries")
        st.caption("Edit any cell directly, or use the 🗑️ icon on a row to delete it, then click Save.")
        edited_budgets = st.data_editor(
            all_budgets.sort_values("month", ascending=False),
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "month": st.column_config.TextColumn("Month (YYYY-MM)"),
                "category": st.column_config.TextColumn("Category"),
                "budget_amount": st.column_config.NumberColumn("Budget amount", format="$%.2f"),
            },
            key="budgets_editor",
        )
        if st.button("💾 Save changes", key="save_budgets"):
            ds.save_table("budgets", edited_budgets)
            st.success("Budgets updated.")
            st.rerun()
    else:
        st.caption("No budget set for this month yet.")

# ---------------- Properties ----------------
with tabs[4]:
    with st.expander("➕ Add a property"):
        with st.form("add_property", clear_on_submit=True):
            p_addr = st.text_input("Full address (Street, City, State, Zip)")
            p_nick = st.text_input("Nickname", placeholder="e.g. Mayfair Ave")
            p_mortgage = st.number_input("Current mortgage balance", step=1000.0)
            if st.form_submit_button("Add property") and p_addr.strip():
                ds.append_row("properties", {
                    "address": p_addr.strip(), "nickname": p_nick.strip(),
                    "zillow_estimate": None, "redfin_estimate": None, "homes_estimate": None,
                    "rentcast_estimate": None, "suggested_rent": None,
                    "mortgage_balance": p_mortgage,
                    "last_updated": datetime.date.today().isoformat(), "notes": "",
                })
                st.rerun()

    properties = ds.load_table("properties")
    if properties.empty:
        st.caption("No properties yet. Add one above.")

    for idx, p in properties.iterrows():
        with st.container(border=True):
            top = st.columns([3, 1, 1])
            top[0].markdown(f"### {p['nickname'] or p['address']}")
            top[0].caption(p["address"])
            avg_val = ds.property_avg_value(p)
            top[1].metric("Est. value", f"${avg_val:,.0f}")

            if valuation.has_api_key():
                if top[2].button("🔄 Refresh valuation (RentCast)", key=f"refresh_{idx}"):
                    with st.spinner("Fetching current value + rent estimate..."):
                        val_result = valuation.get_value_estimate(p["address"])
                        rent_result = valuation.get_rent_estimate(p["address"])
                    if "error" in val_result:
                        st.error(val_result["error"])
                    if "error" in rent_result:
                        st.error(rent_result["error"])
                    updates = {"last_updated": datetime.date.today().isoformat()}
                    if "value" in val_result and val_result.get("value"):
                        updates["rentcast_estimate"] = val_result["value"]
                    if "rent" in rent_result and rent_result.get("rent"):
                        updates["suggested_rent"] = rent_result["rent"]
                    if len(updates) > 1:
                        ds.update_row("properties", idx, updates)
                        st.success("Valuation refreshed.")
                        st.rerun()
            else:
                top[2].caption("Enter estimates manually below ↓")

            def _n(v):
                return float(v) if pd.notna(v) else 0.0

            mcols = st.columns(5)
            mcols[0].caption(f"Zillow: ${_n(p['zillow_estimate']):,.0f}")
            mcols[1].caption(f"Redfin: ${_n(p['redfin_estimate']):,.0f}")
            mcols[2].caption(f"Homes.com: ${_n(p['homes_estimate']):,.0f}")
            mcols[3].caption(f"RentCast: ${_n(p['rentcast_estimate']):,.0f}")
            mcols[4].caption(f"Suggested rent: ${_n(p['suggested_rent']):,.0f}/mo")

            mortgage_val = _n(p['mortgage_balance'])
            st.caption(f"Mortgage balance: ${mortgage_val:,.0f} · Equity: ${avg_val - mortgage_val:,.0f} · Last updated: {p['last_updated']}")

            with st.expander("Manually edit estimates / mortgage"):
                ecols = st.columns(4)
                z = ecols[0].number_input("Zillow est.", value=_n(p["zillow_estimate"]), key=f"z_{idx}")
                r = ecols[1].number_input("Redfin est.", value=_n(p["redfin_estimate"]), key=f"r_{idx}")
                h = ecols[2].number_input("Homes.com est.", value=_n(p["homes_estimate"]), key=f"h_{idx}")
                m = ecols[3].number_input("Mortgage balance", value=_n(p["mortgage_balance"]), key=f"m_{idx}")
                if st.button("Save", key=f"save_{idx}"):
                    ds.update_row("properties", idx, {
                        "zillow_estimate": z, "redfin_estimate": r, "homes_estimate": h,
                        "mortgage_balance": m, "last_updated": datetime.date.today().isoformat(),
                    })
                    st.rerun()

            if st.button("Delete property", key=f"del_{idx}"):
                ds.delete_row("properties", idx)
                st.rerun()

# ---------------- Chat ----------------
with tabs[5]:
    st.caption("Ask about your net worth, spending, budget, or properties — e.g. \"how's my net worth trending?\" or \"what's my biggest expense category?\"")

    for turn in st.session_state.chat_history:
        with st.chat_message(turn["role"]):
            st.write(turn["content"])

    question = st.chat_input("Ask the assistant...")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = llm_assistant.ask(question, st.session_state.chat_history[:-1])
            st.write(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
