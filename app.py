import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PAGE SETUP (Website Settings) ---
st.set_page_config(page_title="Smart Investor Index", page_icon="🛡️", layout="centered")

# Website Header
st.title("🛡️ Smart Investor Index (SII)")
st.markdown("**Strategic Capital Compass for Long-Term Investors**")
st.markdown("---")

# --- 2. DATA ACQUISITION (Live Data) ---
@st.cache_data(ttl=3600)
def get_market_data():
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365)
    tickers = ['^VIX', 'SPY', 'RSP', 'HYG', 'IEF']
    
    # משיכת הנתונים
    df = yf.download(tickers, start=start_dt, end=end_dt, progress=False)['Close']
    
    # השלמת חוסרים (לוקח את יום שישי ומעתיק ליום שני) בלי למחוק את הטבלה
    df = df.ffill() 
    return df

with st.spinner('Fetching real-time market data...'):
    df = get_market_data()

# בדיקה קריטית: האם יאהו לא החזיר נתונים בכלל?
if df.empty or len(df) == 0:
    st.error("🚨 Yahoo Finance connection issue. No data received.")
    st.stop()

# לקיחת הנתון התקין האחרון לכל מדד בנפרד
vix_val = df['^VIX'].dropna().iloc[-1]
breadth_val = (df['RSP'] / df['SPY']).dropna().iloc[-1]
credit_val = (df['HYG'] / df['IEF']).dropna().iloc[-1]


# --- 3. SCORING ENGINE (The Math) ---
def calculate_vix_score(v):
    if v <= 20: return 100 * np.exp(-0.02 * (v - 10))
    else: return 100 * np.exp(-0.12 * (v - 12))

v_score = calculate_vix_score(vix_val)
b_score = ((breadth_val - (df['RSP']/df['SPY']).min()) / ((df['RSP']/df['SPY']).max() - (df['RSP']/df['SPY']).min())) * 100
c_score = ((credit_val - (df['HYG']/df['IEF']).min()) / ((df['HYG']/df['IEF']).max() - (df['HYG']/df['IEF']).min())) * 100

# Robust Dynamic Weighting
weight_vix = 0.65 if (vix_val > 25 or vix_val < 18) else 0.45
weight_br = 0.20 if weight_vix == 0.65 else 0.35
weight_cr = 1.0 - weight_vix - weight_br

final_idx = (v_score * weight_vix) + (b_score * weight_br) + (c_score * weight_cr)

# --- 4. TACTICAL INFERENCE LOGIC ---
if final_idx <= 25.0:
    status, action, color = "DEEP FEAR", "EXECUTE BUY: Aggressively scale into Value segments.", "#ff4b4b"
elif final_idx <= 35.0:
    status, action, color = "FEAR WARNING", "PREPARE TO BUY: Start screening high-quality stocks.", "#ffb347"
elif final_idx <= 65.0:
    status, action, color = "NEUTRAL", "HOLD: No tactical changes required.", "#e0e0e0"
elif final_idx <= 75.0:
    status, action, color = "GREED WARNING", "PREPARE TO SELL: Review winners & stops.", "#90ee90"
else:
    status, action, color = "EUPHORIA", "EXECUTE HARVEST: Take partial profits & hedge.", "#4bff4b"

# --- 5. INTERACTIVE GAUGE CHART (Plotly) ---
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = final_idx,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': f"Current Status: {status}", 'font': {'size': 24}},
    number = {'font': {'size': 60, 'color': 'black'}, 'valueformat': ".1f"},
    gauge = {
        'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "black", 'tickfont': {'size': 18, 'color': 'black', 'family': 'Arial Black'}},
        'bar': {'color': "black", 'thickness': 0.15},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 25], 'color': '#ff4b4b'},    # Deep Fear
            {'range': [25, 35], 'color': '#ffb347'},   # Fear Warning
            {'range': [35, 65], 'color': '#e0e0e0'},   # Neutral
            {'range': [65, 75], 'color': '#90ee90'},   # Greed Warning
            {'range': [75, 100], 'color': '#4bff4b'}   # Euphoria
        ],
    }
))

fig.update_layout(height=400, margin=dict(l=50, r=50, t=50, b=20))
st.plotly_chart(fig, use_container_width=True)

# --- 6. ACTIONABLE INSIGHTS UI ---
if final_idx <= 35:
    st.error(f"**Strategic Instruction:** {action}")
elif final_idx > 65:
    st.success(f"**Strategic Instruction:** {action}")
else:
    st.info(f"**Strategic Instruction:** {action}")

st.markdown("---")
st.subheader("⚙️ The Engine Room (Real-Time Metrics)")
col1, col2, col3 = st.columns(3)
col1.metric("VIX (Volatility)", f"{vix_val:.2f}", "Dominant" if weight_vix == 0.65 else "Balanced", delta_color="inverse")
col2.metric("Credit Stress (HYG/IEF)", f"{credit_val:.2f}")
col3.metric("Market Breadth (RSP/SPY)", f"{breadth_val:.2f}")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | *Built for strategic asset allocation.*")

# --- 7. HISTORICAL TREND GRAPH ---
st.markdown("---")
st.subheader("📊 30-Day Index Trend")

# חישוב המדד לכל יום בהיסטוריה
hist_df = df.copy()
# נרמול הנתונים כמו שעשינו למדד הראשי, רק על כל הטבלה
vix_norm_h = 100 - ((hist_df['^VIX'] - 10) / (40 - 10) * 100).clip(0, 100)
breadth_norm_h = ((hist_df['RSP'] / hist_df['SPY'] - 0.20) / (0.35 - 0.20) * 100).clip(0, 100)
credit_norm_h = ((hist_df['HYG'] / hist_df['IEF'] - 0.75) / (0.95 - 0.75) * 100).clip(0, 100)

hist_df['SII'] = (vix_norm_h * 0.4) + (breadth_norm_h * 0.3) + (credit_norm_h * 0.3)

# יצירת הגרף
import plotly.express as px
fig_hist = px.line(hist_df.tail(30), y='SII', title=None, labels={'SII': 'Index Value', 'Date': ''})
fig_hist.update_traces(line_color='#00ff00', line_width=3) # קו ירוק זוהר שמתאים ל-Dark Mode
fig_hist.update_layout(
    hovermode="x unified",
    yaxis_range=[0, 100],
    height=300,
    margin=dict(l=20, r=20, t=20, b=20),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig_hist, use_container_width=True)
