import streamlit as st
import sys
from pathlib import Path
import time
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# Add scr directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'scr'))

from scr.config import Config
from scr.ingestion import DataIngestion
from scr.graph_bulider import GraphBuilder
from scr.pipeline import GraphRAGPipeline
from loguru import logger

# Configure page
st.set_page_config(
    page_title="🏭 FMCG GraphRAG - Warehouse Risk Analyzer",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Choose UI Template (Change this variable to switch themes)
UI_TEMPLATE = "minimalist"  # Options: "minimalist", "dark", "material", "retro"

# Template Styles
if UI_TEMPLATE == "minimalist":
    # Clean Minimalist Template
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.8rem;
            font-weight: 300;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
            letter-spacing: -1px;
        }
        .feature-card {
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #495057;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.08);
            transform: translateY(-1px);
        }
        .metric-card {
            background: #ffffff;
            border-radius: 6px;
            padding: 1rem;
            border-left: 3px solid #6c757d;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .answer-container {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #495057;
        }
        .answer-content {
            background: #ffffff;
            border-radius: 6px;
            padding: 1rem;
            color: #212529;
            border: 1px solid #e9ecef;
            font-size: 1rem;
            line-height: 1.5;
        }
        .recommendation-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid #6c757d;
        }
        .priority-high { border-left-color: #dc3545; background: #fff5f5; }
        .priority-medium { border-left-color: #ffc107; background: #fffbf0; }
        .priority-low { border-left-color: #28a745; background: #f8fff9; }
    .demo-query-card {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #6c757d;
        transition: all 0.2s ease;
        cursor: pointer;
        font-weight: 500;
        color: #495057;
    }
    .demo-query-card:hover {
        background: #f8f9fa;
        border-left-color: #495057;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
        .demo-queries-container {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }
        .stButton>button {
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }
        .stButton>button:hover {
            background: #5a6268;
        }
        .stTextInput>div>div>input {
            border-radius: 4px;
            border: 1px solid #ced4da;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .stTextInput>div>div>input:focus {
            border-color: #6c757d;
            box-shadow: 0 0 0 2px rgba(108,117,125,0.25);
        }
        .analysis-header {
            color: #2c3e50;
            font-size: 1.5rem;
            font-weight: 500;
            margin: 1rem 0;
            text-align: center;
        }
        .success-message {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.75rem 0;
            font-weight: 500;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

elif UI_TEMPLATE == "dark":
    # Dark Theme Template
    st.markdown("""
    <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #ffffff;
            text-align: center;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #e2e8f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            background: #374151;
            box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        }
        .metric-card {
            background: #1a202c;
            border-radius: 6px;
            padding: 1rem;
            border-left: 3px solid #63b3ed;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .answer-container {
            background: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #e2e8f0;
        }
        .answer-content {
            background: #1a202c;
            border-radius: 6px;
            padding: 1rem;
            color: #f7fafc;
            border: 1px solid #4a5568;
            font-size: 1rem;
            line-height: 1.5;
        }
        .recommendation-card {
            background: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 6px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid #63b3ed;
        }
        .priority-high { border-left-color: #fc8181; background: #2d1b1b; }
        .priority-medium { border-left-color: #f6e05e; background: #2d2a1b; }
        .priority-low { border-left-color: #68d391; background: #1b2d1b; }
        .demo-query-card {
            background: #1a202c;
            border: 1px solid #4a5568;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            border-left: 3px solid #63b3ed;
            transition: all 0.2s ease;
            cursor: pointer;
            color: #e2e8f0;
            font-weight: 500;
        }
        .demo-query-card:hover {
            background: #2d3748;
            border-left-color: #4299e1;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .demo-queries-container {
            background: #1a202c;
            border: 1px solid #4a5568;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
        }
        .stButton>button {
            background: #4299e1;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: background-color 0.2s ease;
        }
        .stButton>button:hover {
            background: #3182ce;
        }
        .stTextInput>div>div>input {
            border-radius: 4px;
            border: 1px solid #4a5568;
            padding: 0.5rem;
            font-size: 1rem;
            background: #2d3748;
            color: #e2e8f0;
        }
        .stTextInput>div>div>input:focus {
            border-color: #4299e1;
            box-shadow: 0 0 0 2px rgba(66,153,225,0.25);
        }
        .analysis-header {
            color: #ffffff;
            font-size: 1.5rem;
            font-weight: 500;
            margin: 1rem 0;
            text-align: center;
        }
        .success-message {
            background: #2d3748;
            border: 1px solid #68d391;
            color: #68d391;
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.75rem 0;
            font-weight: 500;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

elif UI_TEMPLATE == "material":
    # Material Design Template
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.8rem;
            font-weight: 400;
            color: #1976d2;
            text-align: center;
            margin-bottom: 2rem;
            font-family: 'Roboto', sans-serif;
        }
        .feature-card {
            background: #ffffff;
            border-radius: 4px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #424242;
            box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14), 0 3px 1px -2px rgba(0,0,0,0.12), 0 1px 5px 0 rgba(0,0,0,0.2);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            border: 1px solid #e0e0e0;
        }
        .feature-card:hover {
            box-shadow: 0 8px 16px 0 rgba(0,0,0,0.14), 0 12px 8px -4px rgba(0,0,0,0.12), 0 4px 20px 0 rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        .metric-card {
            background: #ffffff;
            border-radius: 4px;
            padding: 1rem;
            border-left: 4px solid #1976d2;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        .answer-container {
            background: #ffffff;
            border-radius: 4px;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #424242;
            box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14), 0 3px 1px -2px rgba(0,0,0,0.12), 0 1px 5px 0 rgba(0,0,0,0.2);
        }
        .answer-content {
            background: #fafafa;
            border-radius: 4px;
            padding: 1rem;
            color: #212529;
            border: 1px solid #e0e0e0;
            font-size: 1rem;
            line-height: 1.5;
        }
        .recommendation-card {
            background: #ffffff;
            border-radius: 4px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #1976d2;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        .priority-high { border-left-color: #d32f2f; background: #ffebee; }
        .priority-medium { border-left-color: #f57c00; background: #fff3e0; }
        .priority-low { border-left-color: #388e3c; background: #e8f5e8; }
        .demo-query-card {
            background: #ffffff;
            border-radius: 4px;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #1976d2;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            font-weight: 500;
            color: #424242;
        }
        .demo-query-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.14), 0 6px 4px -2px rgba(0,0,0,0.12), 0 2px 10px 0 rgba(0,0,0,0.2);
            transform: translateY(-1px);
        }
        .demo-queries-container {
            background: #fafafa;
            border-radius: 4px;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        .stButton>button {
            background: #1976d2;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        }
        .stButton>button:hover {
            background: #1565c0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.16), 0 2px 4px rgba(0,0,0,0.12);
        }
        .stTextInput>div>div>input {
            border-radius: 4px;
            border: 1px solid #bdbdbd;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .stTextInput>div>div>input:focus {
            border-color: #1976d2;
            box-shadow: 0 0 0 2px rgba(25,118,210,0.25);
        }
        .analysis-header {
            color: #1976d2;
            font-size: 1.5rem;
            font-weight: 500;
            margin: 1rem 0;
            text-align: center;
        }
        .success-message {
            background: #e8f5e8;
            border: 1px solid #4caf50;
            color: #2e7d32;
            border-radius: 4px;
            padding: 0.75rem;
            margin: 0.75rem 0;
            font-weight: 500;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

elif UI_TEMPLATE == "retro":
    # Retro/Classic Template
    st.markdown("""
    <style>
        .main-header {
            font-size: 3.2rem;
            font-weight: bold;
            color: #8b4513;
            text-align: center;
            margin-bottom: 2rem;
            font-family: 'Courier New', monospace;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .feature-card {
            background: linear-gradient(145deg, #f5deb3, #deb887);
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #8b4513;
            box-shadow: 4px 4px 8px rgba(0,0,0,0.3);
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 12px rgba(0,0,0,0.4);
        }
        .metric-card {
            background: #f5deb3;
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 1rem;
            border-left: 4px solid #8b4513;
            box-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        }
        .answer-container {
            background: linear-gradient(145deg, #f5deb3, #deb887);
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 1.5rem;
            margin: 1rem 0;
            color: #8b4513;
            box-shadow: 4px 4px 8px rgba(0,0,0,0.3);
        }
        .answer-content {
            background: #faf0e6;
            border: 1px solid #daa520;
            border-radius: 0;
            padding: 1rem;
            color: #654321;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        .recommendation-card {
            background: #f5deb3;
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #8b4513;
            box-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        }
        .priority-high { border-left-color: #b22222; background: #ffe4e1; }
        .priority-medium { border-left-color: #daa520; background: #fffacd; }
        .priority-low { border-left-color: #228b22; background: #f0fff0; }
        .demo-query-card {
            background: #faf0e6;
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #8b4513;
            transition: all 0.2s ease;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #654321;
        }
        .demo-query-card:hover {
            background: #f5deb3;
            transform: translate(-1px, -1px);
            box-shadow: 4px 4px 8px rgba(0,0,0,0.3);
        }
        .demo-queries-container {
            background: #faf0e6;
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 1.5rem;
            margin: 1.5rem 0;
            box-shadow: 3px 3px 6px rgba(0,0,0,0.2);
        }
        .stButton>button {
            background: linear-gradient(145deg, #daa520, #b8860b);
            color: #8b4513;
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 0.5rem 1rem;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            transition: all 0.2s ease;
            box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .stButton>button:hover {
            background: linear-gradient(145deg, #b8860b, #daa520);
            transform: translate(-1px, -1px);
            box-shadow: 3px 3px 6px rgba(0,0,0,0.4);
        }
        .stTextInput>div>div>input {
            border: 2px solid #daa520;
            border-radius: 0;
            padding: 0.5rem;
            font-size: 1rem;
            font-family: 'Courier New', monospace;
            background: #faf0e6;
        }
        .stTextInput>div>div>input:focus {
            border-color: #8b4513;
            box-shadow: 2px 2px 4px rgba(139,69,19,0.3);
        }
        .analysis-header {
            color: #8b4513;
            font-size: 1.5rem;
            font-weight: bold;
            margin: 1rem 0;
            text-align: center;
            font-family: 'Courier New', monospace;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        .success-message {
            background: #e6f3e6;
            border: 2px solid #228b22;
            color: #006400;
            border-radius: 0;
            padding: 0.75rem;
            margin: 0.75rem 0;
            font-weight: bold;
            text-align: center;
            font-family: 'Courier New', monospace;
        }
    </style>
    """, unsafe_allow_html=True)

def setup_logging():
    """Configure logging for Streamlit"""
    log_path = Path(Config.LOG_FILE)
    log_path.parent.mkdir(exist_ok=True, parents=True)
    
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=Config.LOG_LEVEL
    )
    logger.add(
        Config.LOG_FILE,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )

def initialize_graph_with_progress():
    """Initialize graph database with progress bars"""
    with st.spinner("🚀 Initializing Graph Database..."):
        progress_bar = st.progress(0)
        
        # Step 1: Data Ingestion
        st.info("📥 Step 1: Data Ingestion")
        progress_bar.progress(25)
        ingestion = DataIngestion()
        df, entities = ingestion.run_pipeline()
        progress_bar.progress(50)
        
        # Step 2: Graph Construction
        st.info("🔗 Step 2: Graph Construction")
        progress_bar.progress(75)
        builder = GraphBuilder()
        try:
            builder.build_graph(entities, clear_existing=True)
            progress_bar.progress(100)
            st.success("✅ Graph initialization completed!")
            return df, entities
        finally:
            builder.close()

def display_data_insights(df):
    """Display data insights and visualizations"""
    st.header("📊 Data Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Warehouses", len(df))
    
    with col2:
        risk_warehouses = len(df[df['flood_impacted'] == 1])
        st.metric("Flood-Prone Warehouses", risk_warehouses)
    
    with col3:
        avg_breakdowns = df['wh_breakdown_l3m'].mean()
        st.metric("Avg Breakdowns (3M)", ".1f")
    
    with col4:
        high_capacity = len(df[df['WH_capacity_size'] == 'Large'])
        st.metric("Large Capacity WH", high_capacity)
    
    # Zone distribution
    st.subheader("🏭 Warehouse Distribution by Zone")
    zone_counts = df['zone'].value_counts()
    fig_zone = px.bar(zone_counts, 
                     title="Warehouses by Zone",
                     labels={'index': 'Zone', 'value': 'Count'},
                     color_discrete_sequence=['#1e3c72'])
    st.plotly_chart(fig_zone, use_container_width=True)
    
    # Risk analysis
    st.subheader("⚠️ Risk Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        flood_risk = df.groupby('zone')['flood_impacted'].sum()
        fig_flood = px.bar(flood_risk, 
                          title="Flood Risk by Zone",
                          labels={'value': 'Flood-Prone Warehouses'},
                          color_discrete_sequence=['#ff6b6b'])
        st.plotly_chart(fig_flood, use_container_width=True)
    
    with col2:
        breakdown_risk = df.groupby('zone')['wh_breakdown_l3m'].mean()
        fig_breakdown = px.bar(breakdown_risk, 
                              title="Average Breakdowns by Zone",
                              labels={'value': 'Avg Breakdowns (3M)'},
                              color_discrete_sequence=['#ffa726'])
        st.plotly_chart(fig_breakdown, use_container_width=True)

def main():
    setup_logging()
    
    # Main header
    st.markdown('<h1 class="main-header">🏭 FMCG Supply Chain GraphRAG</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #666;">Warehouse Risk Analysis & Intelligence Platform</h2>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Navigation")
        page = st.radio("Choose a section:", 
                       ["🏠 Home", "🔍 Query Analyzer", "📊 Data Insights", "⚙️ System Setup"])
        
        st.header("🔧 Configuration")
        with st.expander("System Status"):
            try:
                Config.validate()
                st.success("✅ Configuration Valid")
                st.write(f"**Model:** {Config.GROQ_MODEL}")
                st.write(f"**Database:** {Config.NEO4J_DATABASE}")
            except Exception as e:
                st.error(f"❌ Configuration Error: {e}")
    
    if page == "🏠 Home":
        # Hero section
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h3>🌟 Revolutionizing FMCG Supply Chain Intelligence</h3>
            <p style="font-size: 1.2rem; color: #666;">
            Transform your warehouse risk assessment with AI-powered graph analytics
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key features
        st.header("🚀 Key Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>🧠 Natural Language Queries</h4>
                <p>Ask questions in plain English about warehouse risks, performance, and recommendations</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>🔗 Graph-Powered Analytics</h4>
                <p>Neo4j graph database reveals complex relationships between warehouses, zones, and risk factors</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>📈 Risk Intelligence</h4>
                <p>AI-generated insights and actionable recommendations for risk mitigation</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>⚡ Real-time Processing</h4>
                <p>Groq-powered LLM for fast, accurate analysis of your supply chain data</p>
            </div>
            """, unsafe_allow_html=True)
        
        # How it works
        if UI_TEMPLATE == "minimalist":
            st.header("🔄 How It Works")
            st.markdown("""
            <div style="background: #ffffff; border: 2px solid #dee2e6; border-radius: 8px; padding: 2rem; margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <ol style="font-size: 1.1rem; line-height: 2; margin: 0; padding-left: 1.5rem; color: #212529;">
                    <li style="margin-bottom: 1rem;"><strong style="color: #495057;">📊 Data Ingestion:</strong> <span style="color: #6c757d;">Process FMCG warehouse data from CSV files with intelligent preprocessing</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #495057;">🔗 Graph Construction:</strong> <span style="color: #6c757d;">Build knowledge graph with Neo4j database connecting warehouses and relationships</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #495057;">🧠 Query Processing:</strong> <span style="color: #6c757d;">Convert natural language to Cypher queries using advanced AI understanding</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #495057;">🤖 AI Analysis:</strong> <span style="color: #6c757d;">Generate comprehensive insights using Groq LLM for risk assessment</span></li>
                    <li><strong style="color: #495057;">📋 Recommendations:</strong> <span style="color: #6c757d;">Provide actionable risk mitigation strategies with priority scoring</span></li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        elif UI_TEMPLATE == "dark":
            st.markdown('<h2 style="color: #ffffff; text-align: center; font-size: 2.2rem; margin: 2rem 0 1rem 0;">🔄 How It Works</h2>', unsafe_allow_html=True)
            st.markdown("""
            <div style="background: #1a202c; border: 2px solid #4a5568; border-radius: 8px; padding: 2rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                <ol style="font-size: 1.1rem; line-height: 2; margin: 0; padding-left: 1.5rem; color: #f7fafc;">
                    <li style="margin-bottom: 1rem;"><strong style="color: #63b3ed;">📊 Data Ingestion:</strong> <span style="color: #e2e8f0;">Process FMCG warehouse data from CSV files with intelligent preprocessing</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #63b3ed;">🔗 Graph Construction:</strong> <span style="color: #e2e8f0;">Build knowledge graph with Neo4j database connecting warehouses and relationships</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #63b3ed;">🧠 Query Processing:</strong> <span style="color: #e2e8f0;">Convert natural language to Cypher queries using advanced AI understanding</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #63b3ed;">🤖 AI Analysis:</strong> <span style="color: #e2e8f0;">Generate comprehensive insights using Groq LLM for risk assessment</span></li>
                    <li><strong style="color: #63b3ed;">📋 Recommendations:</strong> <span style="color: #e2e8f0;">Provide actionable risk mitigation strategies with priority scoring</span></li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        elif UI_TEMPLATE == "material":
            st.markdown('<h2 style="color: #1976d2; text-align: center; font-size: 2.2rem; margin: 2rem 0 1rem 0;">🔄 How It Works</h2>', unsafe_allow_html=True)
            st.markdown("""
            <div style="background: #ffffff; border-radius: 8px; padding: 2rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 1px solid #e0e0e0;">
                <ol style="font-size: 1.1rem; line-height: 2; margin: 0; padding-left: 1.5rem; color: #424242;">
                    <li style="margin-bottom: 1rem;"><strong style="color: #1976d2;">📊 Data Ingestion:</strong> <span style="color: #616161;">Process FMCG warehouse data from CSV files with intelligent preprocessing</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #1976d2;">🔗 Graph Construction:</strong> <span style="color: #616161;">Build knowledge graph with Neo4j database connecting warehouses and relationships</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #1976d2;">🧠 Query Processing:</strong> <span style="color: #616161;">Convert natural language to Cypher queries using advanced AI understanding</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #1976d2;">🤖 AI Analysis:</strong> <span style="color: #616161;">Generate comprehensive insights using Groq LLM for risk assessment</span></li>
                    <li><strong style="color: #1976d2;">📋 Recommendations:</strong> <span style="color: #616161;">Provide actionable risk mitigation strategies with priority scoring</span></li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        elif UI_TEMPLATE == "retro":
            st.markdown('<h2 style="color: #8b4513; text-align: center; font-size: 2.2rem; margin: 2rem 0 1rem 0; font-family: \'Courier New\', monospace; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🔄 How It Works</h2>', unsafe_allow_html=True)
            st.markdown("""
            <div style="background: linear-gradient(145deg, #f5deb3, #deb887); border: 3px solid #daa520; border-radius: 0; padding: 2rem; margin: 1rem 0; box-shadow: 4px 4px 12px rgba(0,0,0,0.5);">
                <ol style="font-size: 1.1rem; line-height: 2; margin: 0; padding-left: 1.5rem; font-family: 'Courier New', monospace; color: #654321;">
                    <li style="margin-bottom: 1rem;"><strong style="color: #8b4513;">📊 Data Ingestion:</strong> <span style="color: #654321;">Process FMCG warehouse data from CSV files with intelligent preprocessing</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #8b4513;">🔗 Graph Construction:</strong> <span style="color: #654321;">Build knowledge graph with Neo4j database connecting warehouses and relationships</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #8b4513;">🧠 Query Processing:</strong> <span style="color: #654321;">Convert natural language to Cypher queries using advanced AI understanding</span></li>
                    <li style="margin-bottom: 1rem;"><strong style="color: #8b4513;">🤖 AI Analysis:</strong> <span style="color: #654321;">Generate comprehensive insights using Groq LLM for risk assessment</span></li>
                    <li><strong style="color: #8b4513;">📋 Recommendations:</strong> <span style="color: #654321;">Provide actionable risk mitigation strategies with priority scoring</span></li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
        
        # Demo queries
        if UI_TEMPLATE == "minimalist":
            st.header("💡 Sample Queries")
            st.markdown('<div style="text-align: center; color: #495057; margin-bottom: 1.5rem; font-size: 1.1rem; font-weight: 500;">Click on any query below to get started with your analysis</div>', unsafe_allow_html=True)
        elif UI_TEMPLATE == "dark":
            st.markdown('<h2 style="color: #ffffff; text-align: center; font-size: 2.2rem; margin: 3rem 0 1.5rem 0;">💡 Sample Queries</h2>', unsafe_allow_html=True)
            st.markdown('<div style="text-align: center; color: #e2e8f0; margin-bottom: 1.5rem; font-size: 1.1rem; font-weight: 500;">Click on any query below to get started with your analysis</div>', unsafe_allow_html=True)
        elif UI_TEMPLATE == "material":
            st.markdown('<h2 style="color: #1976d2; text-align: center; font-size: 2.2rem; margin: 3rem 0 1.5rem 0;">💡 Sample Queries</h2>', unsafe_allow_html=True)
            st.markdown('<div style="text-align: center; color: #424242; margin-bottom: 1.5rem; font-size: 1.1rem; font-weight: 500;">Click on any query below to get started with your analysis</div>', unsafe_allow_html=True)
        elif UI_TEMPLATE == "retro":
            st.markdown('<h2 style="color: #8b4513; text-align: center; font-size: 2.2rem; margin: 3rem 0 1.5rem 0; font-family: \'Courier New\', monospace; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">💡 Sample Queries</h2>', unsafe_allow_html=True)
            st.markdown('<div style="text-align: center; color: #daa520; margin-bottom: 1.5rem; font-size: 1.1rem; font-weight: bold; font-family: \'Courier New\', monospace; text-shadow: 1px 1px 2px rgba(0,0,0,0.7);">Click on any query below to get started with your analysis</div>', unsafe_allow_html=True)

        demo_queries = [
            "Show me the top 5 highest risk warehouses",
            "Which warehouses are in flood-prone areas without flood protection?",
            "Compare risk levels across different zones",
            "What warehouses have had the most breakdowns?",
            "Show me warehouses with poor infrastructure in high-competitor markets"
        ]

        # Container for demo queries
        st.markdown('<div class="demo-queries-container">', unsafe_allow_html=True)

        for i, query in enumerate(demo_queries):
            icon = ["🔥", "🌊", "📊", "⚙️", "🏗️"][i]  # Different icons for each query
            if UI_TEMPLATE == "minimalist":
                st.markdown(f"""
                <div class="demo-query-card" style="background: #ffffff; color: #495057; border: 2px solid #dee2e6;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.2rem; margin-right: 0.75rem;">{icon}</span>
                        <span style="flex: 1; font-weight: 500; color: #212529;">{query}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif UI_TEMPLATE == "dark":
                st.markdown(f"""
                <div class="demo-query-card" style="background: #1a202c; color: #e2e8f0; border: 2px solid #4a5568;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.2rem; margin-right: 0.75rem;">{icon}</span>
                        <span style="flex: 1; font-weight: 500; color: #f7fafc;">{query}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif UI_TEMPLATE == "material":
                st.markdown(f"""
                <div class="demo-query-card" style="background: #ffffff; color: #424242; border: 1px solid #e0e0e0;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.2rem; margin-right: 0.75rem;">{icon}</span>
                        <span style="flex: 1; font-weight: 500; color: #212529;">{query}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif UI_TEMPLATE == "retro":
                st.markdown(f"""
                <div class="demo-query-card" style="background: #faf0e6; color: #654321; border: 2px solid #daa520; font-family: 'Courier New', monospace;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.2rem; margin-right: 0.75rem;">{icon}</span>
                        <span style="flex: 1; font-weight: bold; color: #8b4513;">{query}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    
    elif page == "🔍 Query Analyzer":
        st.header("🔍 Interactive Query Analyzer")
        
        # Initialize pipeline
        if 'pipeline' not in st.session_state:
            with st.spinner("🔄 Initializing GraphRAG Pipeline..."):
                try:
                    st.session_state.pipeline = GraphRAGPipeline()
                    st.success("✅ Pipeline ready!")
                except Exception as e:
                    st.error(f"❌ Pipeline initialization failed: {e}")
                    return
        
        # Query input
        st.subheader("💬 Ask Your Question")
        query = st.text_input("Enter your warehouse risk analysis query:", 
                            placeholder="e.g., Show me high-risk warehouses in flood zones")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            generate_recs = st.checkbox("Generate Recommendations", value=True)
        with col2:
            submit_button = st.button("🔍 Analyze", use_container_width=True)
        
        if submit_button and query:
            with st.spinner("🤖 Processing your query..."):
                try:
                    result = st.session_state.pipeline.process_query(
                        query, 
                        generate_recommendations=generate_recs
                    )
                    
                    # Display answer
                    st.markdown('<div class="success-message">✅ Analysis Complete! 🚀</div>', unsafe_allow_html=True)

                    st.markdown('<h3 class="analysis-header">🤖 AI Analysis Result</h3>', unsafe_allow_html=True)
                    if UI_TEMPLATE == "minimalist":
                        st.markdown(f"""
                        <div class="answer-container">
                            <div class="answer-content">
                                {result['answer']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif UI_TEMPLATE == "dark":
                        st.markdown(f"""
                        <div class="answer-container">
                            <div class="answer-content">
                                {result['answer']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif UI_TEMPLATE == "material":
                        st.markdown(f"""
                        <div class="answer-container">
                            <div class="answer-content">
                                {result['answer']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif UI_TEMPLATE == "retro":
                        st.markdown(f"""
                        <div class="answer-container">
                            <div class="answer-content">
                                {result['answer']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Display recommendations
                    if result.get('recommendations') and generate_recs:
                        st.markdown('<h3 class="analysis-header">📋 Smart Recommendations</h3>', unsafe_allow_html=True)
                        for rec in result['recommendations']:
                            priority_class = f"priority-{rec['priority'].lower()}"
                            with st.container():
                                st.markdown(f"""
                                <div class="recommendation-card {priority_class}">
                                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                                        <span style="font-size: 1.3rem; margin-right: 0.5rem;">🏭</span>
                                        <div>
                                            <strong style="font-size: 1.1rem; color: #2c3e50;">Warehouse: {rec['warehouse_id']}</strong><br>
                                            <span style="background: rgba(255,255,255,0.8); padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.9rem; font-weight: bold; color: #495057;">
                                                Priority: {rec['priority'].upper()}
                                            </span>
                                        </div>
                                    </div>
                                    <div style="margin-top: 0.5rem;">
                                        <strong style="color: #2c3e50;">Recommended Actions:</strong>
                                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                                """, unsafe_allow_html=True)
                                for action in rec['actions']:
                                    st.markdown(f'<li style="margin-bottom: 0.25rem; color: #495057;">{action}</li>', unsafe_allow_html=True)
                                st.markdown("</ul></div></div>", unsafe_allow_html=True)
                    
                    # Metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Results Found", result['result_count'])
                    with col2:
                        st.metric("Processing Time", ".2f")
                    with col3:
                        st.metric("Query Type", "GraphRAG Analysis")
                        
                except Exception as e:
                    st.error(f"❌ Error processing query: {e}")
                    logger.error(f"Query processing error: {e}")
    
    elif page == "📊 Data Insights":
        st.header("📊 Data Insights & Analytics")
        
        if 'data_df' not in st.session_state:
            st.info("📥 Loading data for analysis...")
            try:
                ingestion = DataIngestion()
                df, _ = ingestion.run_pipeline()
                st.session_state.data_df = df
                display_data_insights(df)
            except Exception as e:
                st.error(f"❌ Error loading data: {e}")
        else:
            display_data_insights(st.session_state.data_df)
    
    elif page == "⚙️ System Setup":
        st.header("⚙️ System Setup & Initialization")
        
        # Configuration display
        st.subheader("🔧 Current Configuration")
        Config.print_config()
        
        # Graph initialization
        st.subheader("🚀 Graph Database Initialization")
        st.warning("⚠️ This will rebuild the entire graph database. Make sure your Neo4j instance is running.")
        
        if st.button("🔄 Initialize/Rebuild Graph Database", type="primary"):
            try:
                df, entities = initialize_graph_with_progress()
                st.session_state.data_df = df
                st.success("🎉 Graph database initialized successfully!")
                
                # Show initialization summary
                st.subheader("📊 Initialization Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Warehouses Processed", len(entities))
                with col2:
                    st.metric("Graph Nodes Created", len(entities))
                    
            except Exception as e:
                st.error(f"❌ Initialization failed: {e}")
                logger.error(f"Graph initialization error: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>Built with ❤️ using Streamlit, Neo4j, and Groq AI</p>
        <p>FMCG Supply Chain GraphRAG System - Revolutionizing Warehouse Risk Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()