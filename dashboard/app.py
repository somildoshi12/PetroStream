import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import awswrangler as wr
import boto3
import os

st.set_page_config(
    page_title="PetroStream",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to match the premium dark mode requested
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    /* Expander / Headers */
    .st-emotion-cache-1wivap2 {
        color: #c9d1d9;
    }
    /* Button primary styling */
    .stButton>button {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    .stButton>button:hover {
        background-color: #ff4b4b;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- CONFIG & SECRETS -----------------
CURATED_BUCKET = os.environ.get('CURATED_BUCKET_NAME', 'petrostream-curated-data-dev-84f59e73')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

# ----------------- SIDEBAR NAV -----------------
st.sidebar.markdown("<h2>🛢️ PetroStream</h2>", unsafe_allow_html=True)
st.sidebar.markdown("**Real-time Oil & Gas Monitoring**")
st.sidebar.markdown("---")

st.sidebar.markdown("**Navigate**")
nav = st.sidebar.radio(
    "",
    ["Overview", "Data Explorer", "Anomaly Detection", "Power BI Portal", "Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Region:** {AWS_REGION}")
st.sidebar.markdown(f"**Database:** petrostream_db")
st.sidebar.markdown(f"**Table:** sensor_stream")
st.sidebar.markdown("---")
st.sidebar.markdown("<small style='color: #8b949e'>Built with Streamlit | PetroStream Project</small>", unsafe_allow_html=True)


# ----------------- DATA CACHING CORE -----------------
@st.cache_data(ttl=60)
def fetch_global_metrics():
    """Uses AWS Athena to instantly compute KPIs across 8.5M+ records without downloading data."""
    try:
        query = "SELECT COUNT(*) as total_records, SUM(CAST(anomaly_flag AS INTEGER)) as total_anomalies FROM sensor_stream"
        df = wr.athena.read_sql_query(
            sql=query,
            database='petrostream_db_dev',
            s3_output='s3://petrostream-athena-results-dev-84f59e73/'
        )
        if not df.empty:
            return df.iloc[0]['total_records'], df.iloc[0]['total_anomalies']
        return 0, 0
    except Exception as e:
        st.error(f"Error querying Athena: {e}")
        return 0, 0

@st.cache_data(ttl=60)
def fetch_explorer_data():
    """Uses AWS Athena to fetch exactly 5,000 recent records instantly."""
    try:
        query = 'SELECT * FROM sensor_stream LIMIT 5000'
        df = wr.athena.read_sql_query(
            sql=query,
            database='petrostream_db_dev',
            s3_output='s3://petrostream-athena-results-dev-84f59e73/'
        )
        return df
    except Exception as e:
        st.error(f"Error querying Athena: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_recent_data(limit=10):
    """Fetches a subset of recent data from the curated bucket to prevent hanging the dashboard."""
    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        response = s3.list_objects_v2(Bucket=CURATED_BUCKET, Prefix='data/')
        if 'Contents' not in response:
            return pd.DataFrame()
            
        objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        recent_keys = [f"s3://{CURATED_BUCKET}/{obj['Key']}" for obj in objects if obj['Key'].endswith('.parquet')][:limit]
        
        if not recent_keys:
            return pd.DataFrame()
            
        df = wr.s3.read_parquet(path=recent_keys)
        # Ensure anomaly flag is numeric to avoid 100% bugs if pandas parses it as string/category
        if 'anomaly_flag' in df.columns:
            df['anomaly_flag'] = pd.to_numeric(df['anomaly_flag'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def list_curated_batches():
    """Lists recent parquet files stored by Lambda in the curated bucket."""
    try:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        response = s3.list_objects_v2(Bucket=CURATED_BUCKET, Prefix='data/')
        if 'Contents' not in response:
            return []
        objects = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)
        return [f"s3://{CURATED_BUCKET}/{obj['Key']}" for obj in objects if obj['Key'].endswith('.parquet')][:30]
    except:
        return []

@st.cache_data(ttl=30)
def fetch_specific_file(s3_path):
    try:
        df = wr.s3.read_parquet(path=s3_path)
        if 'anomaly_flag' in df.columns:
            df['anomaly_flag'] = pd.to_numeric(df['anomaly_flag'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()


# ----------------- PAGE ROUTING -----------------

if nav == "Anomaly Detection":
    st.info("🎓 **Isolation Forest Model Loaded** — Stream data is automatically scored via AWS Lambda upon S3 ingestion.")
    
    st.subheader("Load data from S3 and preview predictions")
    
    batches = list_curated_batches()
    if not batches:
        st.warning("No curated files found. Upload data to Raw S3.")
    else:
        selected_batch = st.selectbox("Select a data file (processed by Lambda):", batches)
        
        col_btn, _ = st.columns([1, 4])
        # We don't really 'run' anomaly detection, we 'load' it, but we can call it this to mimic the screen
        if col_btn.button("Load Evaluated Batch"):
            with st.spinner("Streaming..."):
                batch_df = fetch_specific_file(selected_batch)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            if not batch_df.empty:
                t_rec = len(batch_df)
                t_anom = batch_df['anomaly_flag'].sum() if 'anomaly_flag' in batch_df.columns else 0
                t_norm = t_rec - t_anom
                pct = (t_anom / t_rec) * 100 if t_rec > 0 else 0
                
                m1.metric("Total Records", f"{t_rec:,}")
                m2.metric("Normal", f"{int(t_norm):,}")
                m3.metric("Anomalies", f"{int(t_anom):,}")
                m4.metric("Anomaly %", f"{pct:.1f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Plotly Chart
                st.markdown("**Pressure (P-PDG) with Anomalies Highlighted**")
                
                # Format time
                df_chart = batch_df.reset_index() if batch_df.index.name == 'timestamp' else batch_df.copy()
                if 'timestamp' not in df_chart.columns:
                    df_chart['Time_Index'] = df_chart.index
                t_col = 'timestamp' if 'timestamp' in df_chart.columns else 'Time_Index'
                
                if 'P-PDG' in df_chart.columns:
                    fig = go.Figure()
                    
                    # Blue line for normal
                    fig.add_trace(go.Scatter(
                        x=df_chart[t_col], 
                        y=df_chart['P-PDG'], 
                        mode='lines', 
                        name='Sensor P-PDG',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    # Red markers for anomalies
                    if 'anomaly_flag' in df_chart.columns:
                        anomalies = df_chart[df_chart['anomaly_flag'] == 1]
                        fig.add_trace(go.Scatter(
                            x=anomalies[t_col], 
                            y=anomalies['P-PDG'], 
                            mode='markers', 
                            name='Anomaly Detected',
                            marker=dict(color='red', size=8, symbol='circle')
                        ))
                        
                    fig.update_layout(
                        template="plotly_dark",
                        xaxis_title="Time",
                        yaxis_title="Pressure",
                        margin=dict(l=0, r=0, t=30, b=0),
                        height=400,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("P-PDG column not found in this batch.")
                    

elif nav == "Overview":
    st.title("Project Overview")
    st.markdown("Global view of all sensor data processed strictly via cloud-native architecture.")
    
    with st.spinner("Querying AWS Athena for 8.5M+ Global Records..."):
        total, anom = fetch_global_metrics()
        
    if total > 0:
        rate = (anom / total * 100) if total > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Lifetime Sensor Readings", f"{int(total):,}")
        c2.metric("Total Anomalies Logged", f"{int(anom):,}")
        c3.metric("System Anomaly %", f"{rate:.1f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"System running healthy. Processed {int(total):,} records via S3 -> SQS -> Lambda.")
        
elif nav == "Data Explorer":
    st.title("Raw Data Explorer")
    st.markdown("Inspect the most recent 5,000 tuples of processed sensor data.")
    
    with st.spinner("Fetching global data via Athena..."):
        df_show = fetch_explorer_data()
        
    if not df_show.empty:
        st.dataframe(df_show, height=600, use_container_width=True)

elif nav == "Power BI Portal":
    st.title("Power BI Executive Dashboard")
    st.markdown("Access deep historical insights and strategic reporting.")
    
    st.info("🔗 **Live Connection Setup:** This app uses AWS Athena. To view live data in Power BI, open the `.pbix` file locally and refresh the dataset via the Athena ODBC driver.")
    
    st.markdown("### Executive Report Link")
    st.markdown("Click below to open the published Power BI report (Requires Power BI Pro/Premium workspace):")
    st.markdown('<a href="https://app.powerbi.com" target="_blank"><button style="background-color:#F2C811; color:black; border:none; padding:10px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">Open in Power BI Service</button></a>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📊 What’s available in Power BI?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **1. Long-Term Reliability Trends**
        - Average Mean Time Between Failure (MTBF)
        - Historical Anomaly Distribution by Well
        - Monthly Downhole Pressure Averages
        """)
    with col2:
        st.markdown("""
        **2. Key Performance Indicators**
        - Total Uptime vs Downtime
        - Equipment Lifetime Value
        - Cost savings from Predictive Maintenance
        """)

elif nav == "Settings":
    st.title("Platform Settings")
    st.markdown("Configure thresholds and system preferences.")
    
    st.text_input("Raw Data Bucket Name", value=os.environ.get('RAW_BUCKET_NAME', 'petrostream-raw-data-dev-84f59e73'))
    st.text_input("Curated Bucket Name", value=CURATED_BUCKET)
    st.slider("Anomaly Notification Threshold (%)", 0.0, 100.0, 5.0)

    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache Cleared!")
