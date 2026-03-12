import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import math

# --- 1. PAGE SETUP (Website Settings) ---
# שינוי משמעותי: מעבר ל- "wide" layout כדי לנצל את כל המסך
st.set_page_config(page_title="Smart Investor Index", page_icon="🛡️", layout="wide")

# Website Header
st.title("🛡️ Smart Investor Index (SII)")
st.markdown("**Strategic Capital Compass for Long-Term Investors**")
st.markdown("---")
# --- SIDEBAR: CREATOR & COMMUNITY ---
with st.sidebar:
    st.markdown("### 🛡️ The Proactive Pension Manager")
    st.markdown("*I don't predict the market; I engineer portfolios to withstand it.*")
    
    st.markdown("---")
    
    st.markdown("**1. Join the Community**")
    st.markdown("[🐦 Follow on X (@ProactivePen)](https://x.com/ProactivePen)")
    
    st.markdown("**2. The Strategy Playbook**")
    st.markdown("[📓 Read my full framework on Notion](https://www.notion.so/)") # תחליף את הלינק הזה בלינק שלך
    
    st.markdown("---")
    
    # הכנה למוניטציה (Newsletter / Premium)
    st.markdown("**💎 Premium Insights**")
    st.info("Want to see exactly what assets I accumulate when the SII hits the 'Deep Fear' zone?")
    st.button("Join the Waitlist (Coming Soon)", use_container_width=True)
    
    st.markdown("---")
    st.caption("Disclaimer: This index is for informational purposes only and does not constitute financial advice. Skin in the game: I trade my own capital using these exact signals.")
# --- 2. DATA ACQUISITION (Live Data) ---
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = ['^VIX', 'SPY', 'RSP', 'HYG', 'IEF']
    try:
        # מושכים נתונים בצורה מוגנת
        df = yf.download(tickers, period="6mo", progress=False)
        
        # טיפול בשינויים של Yahoo Finance (מבנה MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            if 'Close' in df.columns.levels[0]:
                df = df['Close']
            elif 'Adj Close' in df.columns.levels[0]:
                df = df['Adj Close']
        
        return df
    except Exception:
        return pd.DataFrame()

with st.spinner('Fetching real-time market data...'):
    df = get_market_data()

# חגורת בטיחות ראשונה: בדיקה שהורדנו נתונים
if df is None or df.empty:
    st.warning("⚠️ Waiting for Yahoo Finance to sync data (Connection Issue)...")
    st.stop()

# חגורת בטיחות שנייה: וידוא שכל עמודות הטיקרים קיימות
required_tickers = ['^VIX', 'SPY', 'RSP', 'HYG', 'IEF']
missing_tickers = [t for t in required_tickers if t not in df.columns]

if missing_tickers:
    st.warning(f"⚠️ Yahoo Finance is temporarily missing data for: {', '.join(missing_tickers)}. Retrying soon...")
    st.stop()

# פקודת הקסם: ממלאת חללים (NaN) עם הנתון ההיסטורי האחרון הזמין
df_clean = df.ffill().dropna(how='all')

try:
    # שליפת הנתונים בצורה החסינה ביותר (חישוב -> סינון ריקים -> נתון אחרון)
    vix_val = df_clean['^VIX'].dropna().iloc[-1]
    
    breadth_series = (df_clean['RSP'] / df_clean['SPY']).dropna()
    breadth_val = breadth_series.iloc[-1]
    
    credit_series = (df_clean['HYG'] / df_clean['IEF']).dropna()
    credit_val = credit_series.iloc[-1]

except Exception as e:
    # במקרה נדיר של שגיאה, השרת יעצור באלגנטיות
    st.warning("⚠️ Market data is currently syncing. Please refresh the page in a few moments.")
    st.stop()

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


# --- 5. MAIN DASHBOARD LAYOUT (The Split View) ---
# חלוקת המסך לשתי עמודות: 40% שמאל, 60% ימין
col_left, col_right = st.columns([4, 6])

# --- צד שמאל: המדד הנוכחי והוראת פעולה ---
with col_left:
    st.subheader("SII Compass")
    
    # הגדרת השעון הבסיסי 
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = final_idx,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {'font': {'size': 40, 'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"}, # מחביא את הפס המקורי
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 35], 'color': 'red'},
                {'range': [35, 65], 'color': 'yellow'},
                {'range': [65, 100], 'color': 'green'}
            ],
        }
    ))

    # מתמטיקה של המחוג: חישוב הזווית
    angle = 180 - (final_idx / 100) * 180
    theta = math.radians(angle)

    # מיקום מרכז השעון ואורך המחוג
    x_center = 0.5
    y_center = 0.25 
    r = 0.35 

    # מיקום קצה המחוג
    x_tip = x_center + r * math.cos(theta)
    y_tip = y_center + r * math.sin(theta)

    # ציור המחוג בעזרת קו ועיגול (Shapes)
    fig.update_layout(
        height=280, # החזרנו קצת גובה כדי שהמספר ייכנס
        margin=dict(l=10, r=10, t=10, b=50), # הקסם כאן: b=50 נותן רווח למטה בדיוק עבור המספר
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        shapes=[
            dict(
                type='line', x0=x_center, y0=y_center, x1=x_tip, y1=y_tip,
                xref='paper', yref='paper', line=dict(color='white', width=5)
            ),
            dict(
                type='circle', x0=x_center-0.02, y0=y_center-0.02,
                x1=x_center+0.02, y1=y_center+0.02, xref='paper', yref='paper',
                fillcolor='white', line_color='white'
            )
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

    # Actionable Insights (ממש מתחת לשעון)
    if final_idx <= 35:
        action_text = "STRATEGIC ACCUMULATION: Build long-term positions in high-quality assets. Deep value zone."
        st.error(f"**Instruction:** {action_text}")
    elif final_idx > 65:
        action_text = "SWING TRADING MODE: Focus on momentum and short-term trends. Protect long-term gains."
        st.success(f"**Instruction:** {action_text}")
    else:
        action_text = "NEUTRAL MONITORING: Maintain current allocations. No major strategic shifts required."
        st.info(f"**Instruction:** {action_text}")


# --- צד ימין: גרף היסטורי ונתוני חדר מנועים ---
with col_right:
    st.subheader("📊 30-Day Index Trend")

    # חישוב המדד לכל יום בהיסטוריה
    hist_df = df.copy()
    vix_norm_h = 100 - ((hist_df['^VIX'] - 10) / (40 - 10) * 100).clip(0, 100)
    breadth_norm_h = ((hist_df['RSP'] / hist_df['SPY'] - 0.20) / (0.35 - 0.20) * 100).clip(0, 100)
    credit_norm_h = ((hist_df['HYG'] / hist_df['IEF'] - 0.75) / (0.95 - 0.75) * 100).clip(0, 100)
    hist_df['SII'] = (vix_norm_h * 0.4) + (breadth_norm_h * 0.3) + (credit_norm_h * 0.3)

    # יצירת הגרף ההיסטורי
    # יצירת הגרף ההיסטורי
    fig_hist = px.line(hist_df.tail(30), y='SII', title=None, labels={'SII': 'Index Value', 'Date': ''})
    
    # שינוי 1: הוספת נקודות (markers) על הקו
    fig_hist.update_traces(line_color='#00ff00', line_width=3, mode='lines+markers', marker=dict(size=5))
    
    # שינוי 2: מחיקת הנעילה של ציר Y כדי לאפשר זום אוטומטי
    fig_hist.update_layout(
        hovermode="x unified",
        height=200, 
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    st.markdown("---")
    
    # Engine Room - קוביות קטנות מתחת לגרף
    e_col1, e_col2, e_col3 = st.columns(3)
    e_col1.metric("VIX (Volatility)", f"{vix_val:.2f}", "Dominant" if weight_vix == 0.65 else "Balanced", delta_color="inverse")
    e_col2.metric("Credit Stress", f"{credit_val:.2f}", help="HYG/IEF Ratio")
    e_col3.metric("Market Breadth", f"{breadth_val:.2f}", help="RSP/SPY Ratio")


# --- 6. EXPLANATION FOOTER (Expander) ---
st.markdown("---")
with st.expander("📚 How to read the Smart Investor Index? (Click to expand)"):
    st.markdown("""
    **The Smart Investor Index (SII)** is an engineered compass for long-term and pension-oriented investors, designed to filter out market noise and emotional trading.
    
    **How to use the gauge:**
    * 🟥 **RED ZONE (0-35):** Strategic Accumulation. The market is panicking. This is historically the best time to accumulate high-quality assets at a discount for the long term.
    * 🟨 **YELLOW ZONE (35-65):** Neutral. Normal market conditions. Maintain your current asset allocation.
    * 🟩 **GREEN ZONE (65-100):** Euphoria / Swing Mode. The market is historically expensive. Protect long-term gains and shift focus to short-term momentum or hedging.
    
    **The Engine Room (What are we measuring?):**
    * **Volatility (VIX):** Measures fear in the options market. High VIX = High Fear.
    * **Credit Stress:** Measures capital flight from high-yield (junk) bonds to safe government bonds.
    * **Market Breadth:** Checks if the market rally is supported by many companies, or just a few mega-caps.
    """)

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | *Built for strategic asset allocation.*")
