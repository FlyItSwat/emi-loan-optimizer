"""Interactive EMI and loan optimizer."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from loan import emi, amortize

st.set_page_config(page_title='EMI & Loan Optimizer', page_icon='🏦', layout='wide')
st.title('🏦 EMI & Loan Optimizer')
st.caption('Compare loans, model prepayments and explore interest savings.')
with st.sidebar:
    st.header('Loan A')
    principal = st.number_input('Principal (₹)', min_value=1000.0, value=2000000.0, step=50000.0)
    rate = st.number_input('Annual interest rate (%)', min_value=0.0, max_value=50.0, value=9.0, step=0.25)
    years = st.slider('Term (years)', 1, 40, 20)
    st.header('Prepayment strategy')
    extra = st.number_input('Extra monthly payment (₹)', min_value=0.0, value=5000.0, step=500.0)
    lump = st.number_input('One-time extra payment (₹)', min_value=0.0, value=0.0, step=10000.0)
    month = st.number_input('One-time payment month', min_value=1, max_value=years*12, value=12)
    mode = st.radio('Prepayment effect', ['reduce_term', 'reduce_emi'], format_func=lambda x: 'Shorten term' if x == 'reduce_term' else 'Reduce EMI')

base = amortize(principal, rate, years)
optimized = amortize(principal, rate, years, extra, lump, month, mode)
a,b,c,d = st.columns(4)
a.metric('Standard EMI', f'₹{base.emi:,.0f}')
b.metric('Baseline interest', f'₹{base.total_interest:,.0f}')
c.metric('Interest saved', f'₹{base.total_interest-optimized.total_interest:,.0f}')
d.metric('Months saved', f'{base.months-optimized.months}')
fig = go.Figure()
for name, result in [('Without prepayment', base), ('With prepayment', optimized)]:
    fig.add_trace(go.Scatter(x=[0]+[r['month'] for r in result.rows],
                             y=[principal]+[r['balance'] for r in result.rows],
                             name=name, mode='lines'))
fig.update_layout(title='Outstanding loan balance', xaxis_title='Month', yaxis_title='Balance (₹)')
st.plotly_chart(fig, use_container_width=True)
st.subheader('Loan B comparison')
c1,c2 = st.columns(2)
with c1:
    rate_b = st.number_input('Loan B annual interest rate (%)', 0.0, 50.0, 8.5, 0.25)
with c2:
    years_b = st.slider('Loan B term (years)', 1, 40, 15)
other = amortize(principal, rate_b, years_b)
st.dataframe(pd.DataFrame([
    {'Loan': 'A (standard)', 'Monthly EMI': base.emi, 'Total interest': base.total_interest, 'Total paid': base.total_paid, 'Months': base.months},
    {'Loan': 'A (with prepayment)', 'Monthly EMI': optimized.emi, 'Total interest': optimized.total_interest, 'Total paid': optimized.total_paid, 'Months': optimized.months},
    {'Loan': 'B (standard)', 'Monthly EMI': other.emi, 'Total interest': other.total_interest, 'Total paid': other.total_paid, 'Months': other.months}
]).style.format({'Monthly EMI':'₹{:,.2f}','Total interest':'₹{:,.2f}','Total paid':'₹{:,.2f}'}), hide_index=True, use_container_width=True)
st.subheader('Monthly repayment schedule')
df = pd.DataFrame(optimized.rows)
st.dataframe(df.style.format({c:'₹{:,.2f}' for c in df.columns if c != 'month'}), use_container_width=True, hide_index=True)
st.download_button('Download amortization schedule (CSV)', df.to_csv(index=False), 'loan_amortization.csv', 'text/csv')
st.info('Illustrative fixed-rate model. Interest accrues monthly on declining balance; payments occur at month-end. Excludes fees, insurance, taxes, rate resets and lender-specific prepayment rules. In reduce-EMI mode, monthly EMI is recalculated after an extra payment; the headline EMI metric remains the original EMI.')
