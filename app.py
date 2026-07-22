"""
Peace of Mind — Personal Finance & Net Worth Tracker
Accounts · Expenses · Income · Budgets · Properties (with automated
RentCast valuation refresh) · AI chat assistant
"""
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_store as ds
import valuation
import llm_assistant
import buddy

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
if "ollie_greeted" not in st.session_state:
    st.session_state.ollie_greeted = False

# ---- Ollie the Owl: compute mood from live financial state ----
def _current_month_over_budget() -> bool:
    month = datetime.date.today().strftime("%Y-%m")
    bva = ds.budget_vs_actual(month)
    if bva.empty:
        return False
    return bool((bva["actual"] > bva["budget_amount"]).any())

try:
    _summary = ds.net_worth_summary()
    _goals = ds.load_table("goals")
    _over_budget = _current_month_over_budget()
    _first_load = not st.session_state.ollie_greeted
    _mood = buddy.compute_mood(_summary, _goals, _over_budget, _first_load)
    st.session_state.ollie_greeted = True
except Exception:
    _mood = "neutral"

with st.sidebar:
    st.markdown(
        '<div style="display:flex; justify-content:center; padding:12px 0 4px 0;">'
        + buddy.owl_svg(_mood) + '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center; font-size:12px; color:#8A8F98; font-weight:600; '
        'letter-spacing:0.04em; margin-top:2px;">OLLIE · your money buddy</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="hero-label" style="font-size:13px;">🕊️ PEACE OF MIND</div>', unsafe_allow_html=True)
st.markdown('<p style="color:#8A8F98; margin-top:-8px; margin-bottom:24px;">Your net worth, budget, and properties — with an assistant that knows all of it.</p>', unsafe_allow_html=True)

tabs = st.tabs(["📊 Net Worth", "🎯 Goals", "🏦 Accounts", "🧾 Expenses & Income", "📋 Budget", "🏠 Properties", "💬 Ask the Assistant"])

# ---------------- Net Worth ----------------
with tabs[0]:
    summary = ds.net_worth_summary()
    accounts = ds.load_table("accounts")

    delta_html = ""
    history = ds.net_worth_history()
    if not history.empty and len(history) >= 2:
        change = history["value"].iloc[-1] - history["value"].iloc[-2]
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
    if not history.empty:
        st.markdown('<div class="hero-label" style="margin-top:24px;">Trend</div>', unsafe_allow_html=True)
        fig = px.area(history, x="date", y="value", title=None, color_discrete_sequence=[PLOTLY_BLUES[0]])
        fig.update_traces(
            line=dict(width=2.5, color="#2F6FED"),
            fillcolor="rgba(47, 111, 237, 0.10)",
        )
        fig.update_layout(
            plot_bgcolor="#FAFAFA", paper_bgcolor="#FAFAFA",
            margin=dict(l=0, r=0, t=16, b=0),
            xaxis=dict(showgrid=False, title=None),
            yaxis=dict(showgrid=True, gridcolor="#F0F1F3", title=None),
            font=dict(family="Inter", color="#8A8F98", size=12),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add account balances in the Accounts tab to see your net worth trend.")

    allocation = ds.asset_allocation()
    if allocation:
        st.markdown('<div class="hero-label" style="margin-top:32px;">Asset Allocation</div>', unsafe_allow_html=True)
        alloc_df = pd.DataFrame({"label": list(allocation.keys()), "amount": list(allocation.values())})
        donut = go.Figure(data=[go.Pie(
            labels=alloc_df["label"], values=alloc_df["amount"],
            hole=0.68, sort=False,
            marker=dict(colors=PLOTLY_BLUES, line=dict(color="#FAFAFA", width=3)),
            textinfo="none",
        )])
        total_assets_val = alloc_df["amount"].sum()
        donut.add_annotation(
            text=f"${total_assets_val:,.0f}<br><span style='font-size:11px;color:#8A8F98;'>ASSETS</span>",
            showarrow=False, font=dict(family="Inter", size=20, color="#16181D"),
        )
        donut.update_layout(
            showlegend=True,
            legend=dict(orientation="v", font=dict(family="Inter", size=12, color="#3C3F45")),
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="#FAFAFA", height=320,
        )
        st.plotly_chart(donut, use_container_width=True)

# ---------------- Goals ----------------
with tabs[1]:
    st.markdown('<div class="hero-label">Goals</div>', unsafe_allow_html=True)
    st.caption("Set a target and watch your progress — with a projected date based on your actual pace.")

    with st.expander("➕ Add a goal"):
        with st.form("add_goal", clear_on_submit=True):
            g_name = st.text_input("Goal name", placeholder="e.g. Emergency fund, Down payment, $500K net worth")
            g_target = st.number_input("Target amount", step=1000.0, min_value=0.0)
            g_track = st.selectbox("Track progress against", ["Net worth", "A specific account", "Manual entry"])

            g_track_target = ""
            g_manual_start = 0.0
            if g_track == "A specific account":
                acct_names = sorted(ds.load_table("accounts")["account_name"].dropna().unique().tolist())
                if acct_names:
                    g_track_target = st.selectbox("Which account?", acct_names)
                else:
                    st.caption("No accounts yet — add one in the Accounts tab first, or choose a different tracking option.")
            elif g_track == "Manual entry":
                g_manual_start = st.number_input("Current amount", step=100.0, min_value=0.0)

            g_date = st.date_input("Target date (optional)", value=None)

            if st.form_submit_button("Create goal") and g_name.strip() and g_target > 0:
                track_map = {"Net worth": "net_worth", "A specific account": "account", "Manual entry": "manual"}
                ds.append_row("goals", {
                    "name": g_name.strip(), "target_amount": g_target,
                    "target_date": g_date.isoformat() if g_date else None,
                    "track_type": track_map[g_track], "track_target": g_track_target,
                    "manual_current": g_manual_start,
                    "created_at": datetime.date.today().isoformat(),
                })
                st.rerun()

    goals = ds.load_table("goals")
    if goals.empty:
        st.info("No goals yet — add one above to start tracking progress toward something specific.")
    else:
        for idx, g in goals.iterrows():
            current, history = ds.goal_current_value(g)
            target = g["target_amount"]
            pct = min(current / target * 100, 100) if target > 0 else 0
            remaining = max(target - current, 0)

            _, projection = ds.project_goal(history, target) if not history.empty else (current, None)
            if current >= target:
                projection = "reached"

            bar_color = "#1E9E62" if pct >= 100 else "#2F6FED"

            if projection == "reached":
                status_line = "🎉 Goal reached!"
            elif isinstance(projection, datetime.date):
                status_line = f"On pace to reach this by ~{projection.strftime('%b %Y')}"
            elif g["track_type"] == "manual":
                status_line = "Update your progress manually below."
            else:
                status_line = "Add more history to project a timeline."

            with st.container(border=True):
                top = st.columns([3, 1])
                top[0].markdown(f"**{g['name']}**")
                if g["track_type"] == "manual":
                    if top[1].button("Update progress", key=f"upd_goal_{idx}"):
                        st.session_state[f"editing_goal_{idx}"] = True

                st.markdown(f"""
                <div style="display:flex; height:10px; border-radius:5px; overflow:hidden; background:#EEEFF1; margin:8px 0 6px 0;">
                    <div style="width:{pct:.1f}%; background:{bar_color};"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:13px; color:#8A8F98;">
                    <span>${current:,.0f} of ${target:,.0f} ({pct:.0f}%)</span>
                    <span>${remaining:,.0f} to go</span>
                </div>
                """, unsafe_allow_html=True)
                st.caption(status_line)

                if g["track_type"] == "manual" and st.session_state.get(f"editing_goal_{idx}"):
                    new_val = st.number_input("Current amount", value=float(current), key=f"manual_val_{idx}")
                    if st.button("Save", key=f"save_goal_{idx}"):
                        ds.update_row("goals", idx, {"manual_current": new_val})
                        st.session_state[f"editing_goal_{idx}"] = False
                        st.rerun()

                if st.button("Delete goal", key=f"del_goal_{idx}"):
                    ds.delete_row("goals", idx)
                    st.rerun()

# ---------------- Accounts ----------------
with tabs[2]:
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
with tabs[3]:
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
        st.markdown('<div class="hero-label">Spending by Category</div>', unsafe_allow_html=True)
        by_cat = expenses.groupby("category")["amount"].sum().sort_values(ascending=False).reset_index()
        donut = go.Figure(data=[go.Pie(
            labels=by_cat["category"], values=by_cat["amount"],
            hole=0.68, sort=False,
            marker=dict(colors=PLOTLY_BLUES, line=dict(color="#FAFAFA", width=3)),
            textinfo="none",
        )])
        total_spent = by_cat["amount"].sum()
        donut.add_annotation(
            text=f"${total_spent:,.0f}<br><span style='font-size:11px;color:#8A8F98;'>TOTAL SPENT</span>",
            showarrow=False, font=dict(family="Inter", size=18, color="#16181D"),
        )
        donut.update_layout(
            showlegend=True,
            legend=dict(orientation="v", font=dict(family="Inter", size=12, color="#3C3F45")),
            margin=dict(l=0, r=0, t=10, b=10),
            paper_bgcolor="#FAFAFA", height=320,
        )
        st.plotly_chart(donut, use_container_width=True)

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
with tabs[4]:
    month_pick = st.text_input("Budget month", value=datetime.date.today().strftime("%Y-%m"))

    planned_income = ds.get_planned_income(month_pick)
    line_items = ds.budget_line_items(month_pick)
    total_budgeted = line_items["budget_amount"].sum() if not line_items.empty else 0.0
    left_to_budget = planned_income - total_budgeted

    # --- Planned income input ---
    inc_col1, inc_col2 = st.columns([2, 1])
    new_income = inc_col1.number_input(
        "Planned income for this month", value=float(planned_income), step=100.0, min_value=0.0,
        key=f"income_{month_pick}",
    )
    if new_income != planned_income:
        ds.set_planned_income(month_pick, new_income)
        st.rerun()

    # --- Left-to-budget banner (the EveryDollar signature) ---
    if abs(left_to_budget) < 0.01:
        banner_color, banner_bg, banner_msg = "#1E9E62", "#E9F7EF", "🎉 Every dollar assigned — you're balanced!"
    elif left_to_budget > 0:
        banner_color, banner_bg, banner_msg = "#2F6FED", "#EAF1FE", f"${left_to_budget:,.0f} left to budget"
    else:
        banner_color, banner_bg, banner_msg = "#D64545", "#FCECEC", f"${abs(left_to_budget):,.0f} over budget"

    st.markdown(f"""
    <div style="background:{banner_bg}; border-radius:12px; padding:20px 24px; margin:16px 0 8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <div>
                <div style="font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:#8A8F98; font-weight:600;">Income</div>
                <div style="font-size:1.3rem; font-weight:700; color:#16181D;">${planned_income:,.0f}</div>
            </div>
            <div style="font-size:1.4rem; color:#C4C8CE;">−</div>
            <div>
                <div style="font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:#8A8F98; font-weight:600;">Budgeted</div>
                <div style="font-size:1.3rem; font-weight:700; color:#16181D;">${total_budgeted:,.0f}</div>
            </div>
            <div style="font-size:1.4rem; color:#C4C8CE;">=</div>
            <div style="text-align:right;">
                <div style="font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:{banner_color}; font-weight:600;">Left to budget</div>
                <div style="font-size:1.6rem; font-weight:800; color:{banner_color};">{banner_msg}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Add a budget line ---
    with st.expander("➕ Add a budget line"):
        with st.form("add_budget_line", clear_on_submit=True):
            cols = st.columns([2, 1])
            bl_cat = cols[0].text_input("Category", placeholder="e.g. Groceries, Rent, Gas")
            bl_amt = cols[1].number_input("Planned amount", step=25.0, min_value=0.0)
            if st.form_submit_button("Add line") and bl_cat.strip():
                ds.append_row("budgets", {"month": month_pick, "category": bl_cat.strip(), "budget_amount": bl_amt})
                st.rerun()

    # --- Line items with per-line spending progress ---
    if line_items.empty:
        st.info("No budget lines yet. Add your planned income above, then start assigning it into categories.")
    else:
        bva = ds.budget_vs_actual(month_pick)
        actual_map = dict(zip(bva["category"], bva["actual"])) if not bva.empty else {}

        st.markdown('<div class="hero-label" style="margin-top:8px;">Budget Lines</div>', unsafe_allow_html=True)
        for idx, row in line_items.iterrows():
            cat = row["category"]
            budgeted = float(row["budget_amount"])
            spent = float(actual_map.get(cat, 0.0))
            pct = min(spent / budgeted * 100, 100) if budgeted > 0 else 0
            over = spent > budgeted
            remaining = budgeted - spent
            bar_color = "#D64545" if over else "#1E9E62"

            with st.container(border=True):
                head = st.columns([3, 1])
                head[0].markdown(f"**{cat}**")
                # find this row's real index in the full budgets table for deletion
                if head[1].button("Delete", key=f"del_bline_{month_pick}_{cat}"):
                    full = ds.load_table("budgets")
                    match = full[(full["month"] == month_pick) & (full["category"] == cat)]
                    if not match.empty:
                        ds.delete_row("budgets", match.index[0])
                        st.rerun()

                st.markdown(f"""
                <div style="display:flex; height:8px; border-radius:4px; overflow:hidden; background:#EEEFF1; margin:6px 0 6px 0;">
                    <div style="width:{pct:.1f}%; background:{bar_color};"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:13px; color:#8A8F98;">
                    <span>${spent:,.0f} spent of ${budgeted:,.0f}</span>
                    <span style="color:{'#D64545' if over else '#8A8F98'};">
                        {'$' + format(abs(remaining), ',.0f') + (' over' if over else ' left')}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                new_amt = st.number_input(
                    f"Adjust {cat} budget", value=budgeted, step=25.0, min_value=0.0,
                    key=f"adj_{month_pick}_{cat}", label_visibility="collapsed",
                )
                if new_amt != budgeted:
                    full = ds.load_table("budgets")
                    match = full[(full["month"] == month_pick) & (full["category"] == cat)]
                    if not match.empty:
                        ds.update_row("budgets", match.index[0], {"budget_amount": new_amt})
                        st.rerun()

# ---------------- Properties ----------------
with tabs[5]:
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
            equity_val = max(avg_val - mortgage_val, 0.0)
            equity_pct = (equity_val / avg_val * 100) if avg_val > 0 else 0

            st.markdown(f"""
            <div style="display:flex; height:8px; border-radius:4px; overflow:hidden; margin:12px 0 6px 0; background:#EEEFF1;">
                <div style="width:{equity_pct:.1f}%; background:#2F6FED;"></div>
                <div style="width:{100-equity_pct:.1f}%; background:#D8DDE5;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px; color:#8A8F98;">
                <span><span style="color:#2F6FED;">●</span> Equity ${equity_val:,.0f} ({equity_pct:.0f}%)</span>
                <span><span style="color:#D8DDE5;">●</span> Mortgage ${mortgage_val:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"Last updated: {p['last_updated']}")

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
with tabs[6]:
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
