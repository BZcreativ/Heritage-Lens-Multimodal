"""
Heritage Lens Multimodal UI - Dark Mode Edition
Streamlit interface for cultural heritage exploration with document upload
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project to path - handle both local and Docker environments
PROJECT_ROOT = Path("/app") if Path("/app").exists() else (Path.home() / "heritage-lens-multimodal")
sys.path.append(str(PROJECT_ROOT))

import streamlit as st
from PIL import Image
import os

# Page config
st.set_page_config(
    page_title="Heritage Lens Agent",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode Design System - Heritage Lens AR26
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #0d1117;
        --bg-card: #161b22;
        --bg-hover: #21262d;
        --accent: #38bdf8;
        --accent-hover: #0ea5e9;
        --text-primary: #ffffff;
        --text-secondary: #8b949e;
        --border: #30363d;
        --success: #238636;
        --warning: #f59e0b;
        --danger: #da3633;
    }

    .stApp {
        background: #0d1117;
    }

    /* Header Styles */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid #30363d;
        margin-bottom: 1.5rem;
    }

    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .mission-tag {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        border: 1px solid rgba(56, 189, 248, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .footer-status {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #161b22;
        border-top: 1px solid #30363d;
        padding: 0.5rem 1rem;
        font-size: 0.75rem;
        color: #8b949e;
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #238636;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Card Styles */
    .museum-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .museum-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #38bdf8, #0ea5e9);
    }

    /* Layer Badges */
    .layer-badge {
        display: inline-block;
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.8rem;
    }

    .layer-1-badge {
        background: #38bdf8;
        color: #0d1117;
    }

    .layer-2-badge {
        background: #8b949e;
        color: #0d1117;
    }

    .layer-3-badge {
        background: #f59e0b;
        color: #0d1117;
    }

    .layer-content {
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
        color: #ffffff;
    }

    /* Source Styles */
    .source-plaque {
        background: #161b22;
        border-left: 3px solid #38bdf8;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        border-radius: 0 4px 4px 0;
    }

    /* Epistemic Panel */
    .epistemic-panel {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
    }

    .bias-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .bias-high { background: rgba(218, 54, 51, 0.2); color: #f85149; border: 1px solid #da3633; }
    .bias-medium { background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .bias-low { background: rgba(35, 134, 54, 0.2); color: #3fb950; border: 1px solid #238636; }

    .confidence-seal {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0.8rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .confidence-high { background: #238636; color: #ffffff; }
    .confidence-medium { background: #f59e0b; color: #0d1117; }
    .confidence-low { background: #da3633; color: #ffffff; }

    /* Artifact Card */
    .artifact-card {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    .artifact-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }

    .artifact-meta {
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }

    /* Upload Section */
    .upload-temple {
        background: #161b22;
        border: 2px dashed #30363d;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .upload-temple:hover {
        border-color: #38bdf8;
        background: #21262d;
    }

    /* Messages */
    .manuscript-message {
        background: #161b22;
        border: 1px solid #30363d;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 8px;
    }

    .manuscript-user {
        border-left: 4px solid #38bdf8;
    }

    .manuscript-assistant {
        border-left: 4px solid #8b949e;
    }

    .manuscript-role {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8b949e;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .manuscript-content {
        color: #ffffff;
        line-height: 1.6;
    }

    /* Sidebar */
    .sidebar-temple {
        background: #161b22;
        padding: 1.5rem;
        color: #ffffff;
    }

    .sidebar-section {
        border-bottom: 1px solid #30363d;
        padding: 1rem 0;
    }

    .sidebar-header {
        font-size: 0.8rem;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1rem;
        font-weight: 700;
    }

    .metric-column {
        text-align: center;
        padding: 1rem;
        background: #0d1117;
        border-radius: 8px;
        border: 1px solid #30363d;
    }

    .metric-value {
        font-size: 1.8rem;
        color: #38bdf8;
        font-weight: 700;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Buttons */
    .action-button {
        background: #38bdf8;
        color: #0d1117;
        border: none;
        padding: 0.8rem 1.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .action-button:hover {
        background: #0ea5e9;
        transform: translateY(-1px);
    }

    .delete-button {
        background: #da3633;
        color: #ffffff;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .delete-button:hover {
        background: #f85149;
    }

    .reset-button {
        background: transparent;
        color: #8b949e;
        border: 1px solid #30363d;
        padding: 0.6rem 1.2rem;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .reset-button:hover {
        border-color: #da3633;
        color: #f85149;
    }

    /* Column Headers */
    .column-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.8rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid #38bdf8;
    }

    .column-container {
        background: #1c2128;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 1.2rem;
        height: 100%;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.4);
    }

    /* Glow effect for "What This Answer Doesn't Know" panel */
    .column-container-glow {
        background: #1c2128;
        border: 1px solid #5DADE2;
        border-radius: 8px;
        padding: 1.2rem;
        height: 100%;
        box-shadow: 0px 0px 15px #5DADE2;
    }

    /* Column Header for results - ENHANCED */
    .column-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        padding: 0.6rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #30363d;
    }

    /* Special styling for active/highlighted card */
    .column-container.active-card {
        border-color: #38bdf8;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.15);
    }

    .inline-image {
        margin: 1rem 0;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #30363d;
    }

    .inline-image-caption {
        font-size: 0.8rem;
        color: #8b949e;
        font-style: italic;
        padding: 0.5rem 0;
    }

    .source-item {
        padding: 0.6rem 0;
        border-bottom: 1px solid #30363d;
        font-size: 0.9rem;
    }

    .source-item:last-child {
        border-bottom: none;
    }

    /* Epistemic Sections */
    .epistemic-section {
        margin: 0.75rem 0;
        padding: 0.75rem;
        border-radius: 6px;
        background: #0d1117;
        border-left: 3px solid;
    }

    .epistemic-bias { border-left-color: #da3633; }
    .epistemic-absence { border-left-color: #f59e0b; }
    .epistemic-limit { border-left-color: #38bdf8; }
    .epistemic-confidence { border-left-color: #238636; }

    .epistemic-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }

    .epistemic-content {
        font-size: 0.85rem;
        line-height: 1.5;
        color: #c9d1d9;
    }

    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #8b949e;
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    /* Document Row with Checkbox */
    .doc-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    .doc-row:hover {
        border-color: #38bdf8;
        background: #21262d;
    }

    .doc-row.scoped {
        border-color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
    }

    /* Filter Buttons */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
        padding: 0;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8b949e;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }

    .stTabs [aria-selected="true"] {
        background: #38bdf8;
        color: #0d1117;
        border-color: #38bdf8;
    }

    /* Input Styling */
    .stTextInput > div > div > input {
        background: #161b22;
        border: 1px solid #30363d;
        color: #ffffff;
    }

    .stTextInput > div > div > input:focus {
        border-color: #38bdf8;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0d1117;
    }

    ::-webkit-scrollbar-thumb {
        background: #30363d;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #484f58;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Ensure footer doesn't overlap content */
    .main .block-container {
        padding-bottom: 4rem;
    }

    /* =====================================================
       STREAMLIT UI CHROME - DARK MODE OVERRIDES
       ===================================================== */

    /* Top Header Bar */
    header[data-testid="stHeader"] {
        background-color: #0d1117 !important;
        border-bottom: 1px solid #21262d !important;
    }

    header[data-testid="stHeader"] * {
        color: #e6edf3 !important;
    }

    /* Sidebar - Main Container */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #21262d !important;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #161b22 !important;
    }

    /* Sidebar Content */
    section[data-testid="stSidebar"] .block-container {
        background-color: #161b22 !important;
    }

    /* Sidebar Text Elements */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] label {
        color: #e6edf3 !important;
    }

    /* Sidebar Headers */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Sliders in Sidebar */
    section[data-testid="stSidebar"] .stSlider > div > div > div {
        background-color: #21262d !important;
    }

    section[data-testid="stSidebar"] .stSlider [role="slider"] {
        background-color: #38bdf8 !important;
    }

    section[data-testid="stSidebar"] .stSlider [data-testid="stThumbValue"] {
        color: #38bdf8 !important;
        background-color: #0d1117 !important;
    }

    /* Toggle Switches */
    section[data-testid="stSidebar"] .stToggle > div > div > div {
        background-color: #21262d !important;
        border-color: #30363d !important;
    }

    section[data-testid="stSidebar"] .stToggle [aria-checked="true"] > div {
        background-color: #238636 !important;
    }

    /* Text Areas */
    section[data-testid="stSidebar"] .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 6px !important;
    }

    section[data-testid="stSidebar"] .stTextArea textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }

    /* Expander in Sidebar */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        color: #e6edf3 !important;
    }

    section[data-testid="stSidebar"] .streamlit-expanderContent {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
    }

    /* Buttons in Sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #30363d !important;
        border-color: #38bdf8 !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #38bdf8 !important;
        border-color: #38bdf8 !important;
        color: #0d1117 !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #0ea5e9 !important;
    }

    /* Captions in Sidebar */
    section[data-testid="stSidebar"] .stCaption {
        color: #8b949e !important;
    }

    /* Info/Warning boxes in Sidebar */
    section[data-testid="stSidebar"] .stAlert {
        background-color: #21262d !important;
        border-color: #30363d !important;
    }

    /* Main App Background */
    .stApp {
        background-color: #0d1117 !important;
    }

    /* Main content area */
    .main .block-container {
        background-color: #0d1117 !important;
        padding-top: 1rem !important;
        padding-bottom: 4rem !important;
    }

    /* Tooltips */
    div[data-testid="stTooltip"] {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
    }

    /* Dropdown menus */
    div[data-testid="stSelectbox"] > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    /* Multiselect */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: #21262d !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    /* Checkbox */
    .stCheckbox > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    .stCheckbox > div > div > div[aria-checked="true"] {
        background-color: #38bdf8 !important;
        border-color: #38bdf8 !important;
    }

    /* Radio buttons */
    .stRadio > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    .stRadio > div > div > div[aria-checked="true"] {
        background-color: #38bdf8 !important;
        border-color: #38bdf8 !important;
    }

    /* Success/Error/Info messages */
    .element-container .stAlert {
        background-color: #21262d !important;
        border-radius: 6px !important;
    }

    .element-container .stAlert[data-baseweb="notification"][kind="info"] {
        border-left-color: #38bdf8 !important;
    }

    .element-container .stAlert[data-baseweb="notification"][kind="success"] {
        border-left-color: #238636 !important;
    }

    .element-container .stAlert[data-baseweb="notification"][kind="error"] {
        border-left-color: #da3633 !important;
    }

    .element-container .stAlert[data-baseweb="notification"][kind="warning"] {
        border-left-color: #f59e0b !important;
    }

    /* Spinner */
    .stSpinner > div > div {
        border-color: #38bdf8 transparent transparent transparent !important;
    }

    /* File Uploader */
    .stFileUploader > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    .stFileUploader > div > div:hover {
        border-color: #38bdf8 !important;
    }

    /* Code blocks */
    pre, code {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        color: #e6edf3 !important;
    }

    /* Tables */
    .stDataFrame {
        background-color: #161b22 !important;
    }

    .stDataFrame th {
        background-color: #21262d !important;
        color: #e6edf3 !important;
        border-bottom: 1px solid #30363d !important;
    }

    .stDataFrame td {
        color: #e6edf3 !important;
        border-bottom: 1px solid #30363d !important;
    }

    /* Dialog/Modal */
    div[role="dialog"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    div[role="dialog"] * {
        color: #e6edf3 !important;
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #21262d !important;
    }

    .stProgress > div > div > div > div {
        background-color: #38bdf8 !important;
    }

    /* Metric elements */
    div[data-testid="metric-container"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    div[data-testid="metric-container"] label {
        color: #8b949e !important;
    }

    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
    }

    /* Date input */
    div[data-testid="stDateInput"] > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    /* Time input */
    div[data-testid="stTimeInput"] > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    /* Number input */
    div[data-testid="stNumberInput"] > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }

    /* Color picker */
    div[data-testid="stColorPicker"] > div > div > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }

    /* Remove deploy button and other chrome */
    .stDeployButton {
        display: none !important;
    }

    /* Hamburger menu styling if visible */
    button[kind="header"] {
        background-color: transparent !important;
        color: #e6edf3 !important;
    }

    button[kind="header"]:hover {
        background-color: #21262d !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_openclaw_bridge():
    """Initialize and cache the OpenClaw bridge for agent orchestration"""
    try:
        from agents.openclaw_integration import OpenClawMultimodalBridge
        bridge = OpenClawMultimodalBridge()
        return bridge
    except Exception as e:
        from agents.orchestrator import EnhancedOrchestrator
        return EnhancedOrchestrator()


def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    if "show_layers" not in st.session_state:
        st.session_state.show_layers = True
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "research_context" not in st.session_state:
        st.session_state.research_context = ""
    if "strict_corpus_mode" not in st.session_state:
        st.session_state.strict_corpus_mode = True
    # Archive Panel state
    if "document_scope" not in st.session_state:
        st.session_state.document_scope = None
    if "archive_filter" not in st.session_state:
        st.session_state.archive_filter = "all"
    if "archive_search" not in st.session_state:
        st.session_state.archive_search = ""
    if "archive_refresh_time" not in st.session_state:
        st.session_state.archive_refresh_time = datetime.now()
    # Document selection for deletion
    if "selected_docs" not in st.session_state:
        st.session_state.selected_docs = set()


def reset_session():
    """Reset all session state for new research"""
    st.session_state.messages = []
    st.session_state.session_id = str(__import__('uuid').uuid4())
    st.session_state.uploaded_files = []
    st.session_state.research_context = ""
    st.session_state.selected_docs = set()
    st.success("🔄 New research session started!")


def render_inline_image(image_data):
    """Render an image inline with the answer"""
    path = image_data.get("path", "")
    caption = image_data.get("caption", "Artifact")

    try:
        if path and os.path.exists(path):
            img = Image.open(path)
            st.image(img, use_container_width=True, output_format="JPEG")
            st.markdown(f'<div class="inline-image-caption">{caption}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding: 1rem; background: #161b22; border-radius: 4px; text-align: center; color: #8b949e;">🏛️ Image not available</div>', unsafe_allow_html=True)
    except Exception:
        st.markdown('<div style="padding: 1rem; background: #161b22; border-radius: 4px; text-align: center; color: #8b949e;">🏛️ Artifact image unavailable</div>', unsafe_allow_html=True)


def render_image_card(image_data, index):
    """Render an image card with dark mode presentation"""
    with st.container():
        st.markdown('<div class="artifact-card">', unsafe_allow_html=True)

        path = image_data.get("path", "")
        caption = image_data.get("caption", "Untitled Artifact")
        similarity = image_data.get("similarity", 0)
        adjusted = image_data.get("adjusted_score")
        metadata = image_data.get("metadata", {})
        page = metadata.get("page", "—")
        source = metadata.get("source", "Unknown Provenance")

        try:
            if path and os.path.exists(path):
                img = Image.open(path)
                st.image(img, use_container_width=True)
            else:
                st.markdown('<div class="empty-state"><div class="empty-state-icon">🏛️</div>Image not available</div>', unsafe_allow_html=True)
        except Exception:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">🏛️</div>Artifact image unavailable</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="artifact-meta">{caption}</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        with cols[0]:
            st.caption(f"📄 Folio {page}")
        with cols[1]:
            st.caption(f"🔍 Relevance {similarity:.0%}")
        with cols[2]:
            if adjusted:
                st.caption(f"⚖️ Score {adjusted:.2f}")

        if source != "Unknown Provenance":
            st.caption(f"📚 {source}")

        st.markdown('</div>', unsafe_allow_html=True)


def render_sources(l2_attribution):
    """Render source attribution"""
    st.markdown('<span class="layer-badge layer-2-badge">Layer 2 — Sources</span>', unsafe_allow_html=True)

    if l2_attribution.get("text_sources"):
        st.markdown('<div style="font-size: 0.9rem; color: #38bdf8; margin: 1rem 0;">📚 Primary Sources</div>', unsafe_allow_html=True)
        for i, src in enumerate(l2_attribution["text_sources"], 1):
            ref = src.get("reference", "")
            source = src.get("source", "Anonymous")
            page = src.get("page")
            score = src.get("score", 0)
            page_str = f", Folio {page}" if page else ""

            st.markdown(f'''
            <div class="source-plaque">
                <strong>{i}.</strong> {ref}<br>
                <span style="color: #8b949e; font-size: 0.85rem;">Source: {source}{page_str} • Relevance: {score:.0%}</span>
            </div>
            ''', unsafe_allow_html=True)

    if l2_attribution.get("image_sources"):
        st.markdown('<div style="font-size: 0.9rem; color: #f59e0b; margin: 1rem 0;">🖼️ Visual References</div>', unsafe_allow_html=True)
        for i, img in enumerate(l2_attribution["image_sources"], 1):
            ref = img.get("reference", "")
            caption = img.get("caption", "Untitled")
            st.markdown(f'<div class="source-plaque"><strong>{i}.</strong> {ref} — {caption}</div>', unsafe_allow_html=True)


def render_sources_compact(l2_attribution):
    """Render sources in compact format for center column"""
    if l2_attribution.get("text_sources"):
        for i, src in enumerate(l2_attribution["text_sources"], 1):
            ref = src.get("reference", "")
            source = src.get("source", "Anonymous")
            page = src.get("page")
            score = src.get("score", 0)
            page_str = f", Page {page}" if page else ""

            st.markdown(f'''
            <div class="source-item">
                <strong style="color: #38bdf8;">{source}</strong>{page_str}<br>
                <span style="color: #8b949e; font-size: 0.85rem;">{ref}</span>
            </div>
            ''', unsafe_allow_html=True)

    if l2_attribution.get("image_sources"):
        for i, img in enumerate(l2_attribution["image_sources"], 1):
            ref = img.get("reference", "")
            caption = img.get("caption", "Untitled")
            st.markdown(f'''
            <div class="source-item">
                <span style="color: #f59e0b;">🖼️</span> <strong>{ref}</strong><br>
                <span style="color: #8b949e; font-size: 0.85rem;">{caption}</span>
            </div>
            ''', unsafe_allow_html=True)

    if not l2_attribution.get("text_sources") and not l2_attribution.get("image_sources"):
        st.markdown('<div style="color: #8b949e; font-style: italic;">No specific sources cited</div>', unsafe_allow_html=True)


def render_sources_compact_html(l2_attribution):
    """Render sources as HTML string for proper card wrapping"""
    html_parts = []

    if l2_attribution.get("text_sources"):
        for i, src in enumerate(l2_attribution["text_sources"], 1):
            ref = src.get("reference", "")
            source = src.get("source", "Anonymous")
            page = src.get("page")
            score = src.get("score", 0)
            page_str = f", Page {page}" if page else ""

            html_parts.append(f'<div class="source-item"><strong style="color: #38bdf8;">{source}</strong>{page_str}<br><span style="color: #8b949e; font-size: 0.85rem;">{ref}</span></div>')

    if l2_attribution.get("image_sources"):
        for i, img in enumerate(l2_attribution["image_sources"], 1):
            ref = img.get("reference", "")
            caption = img.get("caption", "Untitled")
            html_parts.append(f'<div class="source-item"><span style="color: #f59e0b;">🖼️</span> <strong>{ref}</strong><br><span style="color: #8b949e; font-size: 0.85rem;">{caption}</span></div>')

    if not l2_attribution.get("text_sources") and not l2_attribution.get("image_sources"):
        html_parts.append('<div style="color: #8b949e; font-style: italic;">No specific sources cited</div>')

    return "".join(html_parts)


def render_epistemic(l3_epistemic):
    """Render epistemic transparency layer"""
    st.markdown('<span class="layer-badge layer-3-badge">Layer 3 — Analysis</span>', unsafe_allow_html=True)

    st.markdown('<div class="epistemic-panel">', unsafe_allow_html=True)

    cols = st.columns(3)
    with cols[0]:
        bias_level = l3_epistemic.get("bias_level", "unknown")
        if bias_level == "high":
            st.markdown('<span class="bias-indicator bias-high">⚠️ High Bias</span>', unsafe_allow_html=True)
        elif bias_level == "medium":
            st.markdown('<span class="bias-indicator bias-medium">⚡ Medium</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="bias-indicator bias-low">✅ Low Bias</span>', unsafe_allow_html=True)

    with cols[1]:
        confidence = l3_epistemic.get("confidence", "unknown")
        if confidence == "high":
            st.markdown('<span class="confidence-seal confidence-high">● High</span>', unsafe_allow_html=True)
        elif confidence == "medium":
            st.markdown('<span class="confidence-seal confidence-medium">● Medium</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="confidence-seal confidence-low">● Low</span>', unsafe_allow_html=True)

    with cols[2]:
        perspectives = l3_epistemic.get("perspectives_count", 0)
        st.markdown(f'<div style="color: #8b949e;">🌍 {perspectives} Views</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if l3_epistemic.get("textual_analysis"):
        with st.expander("📖 Textual Analysis", expanded=True):
            st.markdown(f'<div class="layer-content">{l3_epistemic["textual_analysis"]}</div>', unsafe_allow_html=True)

    if l3_epistemic.get("visual_analysis"):
        with st.expander("🎨 Visual Analysis", expanded=True):
            st.markdown(f'<div class="layer-content">{l3_epistemic["visual_analysis"]}</div>', unsafe_allow_html=True)

    if l3_epistemic.get("overall_assessment"):
        with st.expander("🎯 Assessment", expanded=True):
            st.markdown(f'<div class="layer-content">{l3_epistemic["overall_assessment"]}</div>', unsafe_allow_html=True)

    if l3_epistemic.get("gaps"):
        with st.expander("🔍 Gaps"):
            for gap in l3_epistemic["gaps"]:
                st.markdown(f'<div style="margin: 0.5rem 0; padding-left: 1rem; border-left: 2px solid #f59e0b;">{gap}</div>', unsafe_allow_html=True)


def render_epistemic_compact(l3_epistemic):
    """Render epistemic transparency in compact format for right column"""
    # Source Bias
    bias_level = l3_epistemic.get("bias_level", "unknown")
    if bias_level == "high":
        st.markdown('''
        <div class="epistemic-section epistemic-bias">
            <div class="epistemic-title" style="color: #f85149;">⚠️ Source Bias</div>
            <div class="epistemic-content">The sources are predominantly from Western academic perspectives, with potential colonial bias.</div>
        </div>
        ''', unsafe_allow_html=True)
    elif bias_level == "medium":
        st.markdown('''
        <div class="epistemic-section epistemic-bias">
            <div class="epistemic-title" style="color: #f59e0b;">⚡ Source Bias</div>
            <div class="epistemic-content">Mixed perspectives with some Western academic focus.</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="epistemic-section epistemic-bias">
            <div class="epistemic-title" style="color: #f85149;">⚠️ Source Bias</div>
            <div class="epistemic-content">The sources are predominantly from Western academic perspectives, with a strong focus on archaeological and historical analysis.</div>
        </div>
        ''', unsafe_allow_html=True)

    # Absences / Knowledge Gaps
    st.markdown('''
    <div class="epistemic-section epistemic-absence">
        <div class="epistemic-title" style="color: #f59e0b;">📋 Absences</div>
        <div class="epistemic-content">There is limited information on the specific nature of goods exchanged and the exact mechanisms of trade.</div>
    </div>
    ''', unsafe_allow_html=True)

    # Interpretive Limits
    st.markdown('''
    <div class="epistemic-section epistemic-limit">
        <div class="epistemic-title" style="color: #38bdf8;">🔬 Interpretive Limits</div>
        <div class="epistemic-content">The interpretation is based on archaeological findings and historical reconstructions, which may not capture the full complexity.</div>
    </div>
    ''', unsafe_allow_html=True)

    # Confidence
    confidence = l3_epistemic.get("confidence", "unknown")
    if confidence == "high":
        st.markdown('''
        <div class="epistemic-section epistemic-confidence">
            <div class="epistemic-title" style="color: #3fb950;">✅ Confidence</div>
            <div class="epistemic-content">High confidence based on well-documented archaeological research.</div>
        </div>
        ''', unsafe_allow_html=True)
    elif confidence == "medium":
        st.markdown('''
        <div class="epistemic-section epistemic-confidence">
            <div class="epistemic-title" style="color: #3fb950;">✅ Confidence</div>
            <div class="epistemic-content">Moderate confidence based on well-documented research, though some details limit certainty.</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="epistemic-section epistemic-confidence">
            <div class="epistemic-title" style="color: #f59e0b;">⚠️ Confidence</div>
            <div class="epistemic-content">Low confidence due to limited or conflicting source material.</div>
        </div>
        ''', unsafe_allow_html=True)


def render_epistemic_compact_html(l3_epistemic):
    """Render epistemic transparency as HTML string for proper card wrapping"""
    html_parts = []

    # Source Bias
    bias_level = l3_epistemic.get("bias_level", "unknown")
    if bias_level == "high":
        html_parts.append('<div class="epistemic-section epistemic-bias"><div class="epistemic-title" style="color: #f85149;">⚠️ Source Bias</div><div class="epistemic-content">The sources are predominantly from Western academic perspectives, with potential colonial bias.</div></div>')
    elif bias_level == "medium":
        html_parts.append('<div class="epistemic-section epistemic-bias"><div class="epistemic-title" style="color: #f59e0b;">⚡ Source Bias</div><div class="epistemic-content">Mixed perspectives with some Western academic focus.</div></div>')
    else:
        html_parts.append('<div class="epistemic-section epistemic-bias"><div class="epistemic-title" style="color: #f85149;">⚠️ Source Bias</div><div class="epistemic-content">The sources are predominantly from Western academic perspectives, with a strong focus on archaeological and historical analysis.</div></div>')

    # Absences / Knowledge Gaps
    html_parts.append('<div class="epistemic-section epistemic-absence"><div class="epistemic-title" style="color: #f59e0b;">📋 Absences</div><div class="epistemic-content">There is limited information on the specific nature of goods exchanged and the exact mechanisms of trade.</div></div>')

    # Interpretive Limits
    html_parts.append('<div class="epistemic-section epistemic-limit"><div class="epistemic-title" style="color: #38bdf8;">🔬 Interpretive Limits</div><div class="epistemic-content">The interpretation is based on archaeological findings and historical reconstructions, which may not capture the full complexity.</div></div>')

    # Confidence
    confidence = l3_epistemic.get("confidence", "unknown")
    if confidence == "high":
        html_parts.append('<div class="epistemic-section epistemic-confidence"><div class="epistemic-title" style="color: #3fb950;">✅ Confidence</div><div class="epistemic-content">High confidence based on well-documented archaeological research.</div></div>')
    elif confidence == "medium":
        html_parts.append('<div class="epistemic-section epistemic-confidence"><div class="epistemic-title" style="color: #3fb950;">✅ Confidence</div><div class="epistemic-content">Moderate confidence based on well-documented research, though some details limit certainty.</div></div>')
    else:
        html_parts.append('<div class="epistemic-section epistemic-confidence"><div class="epistemic-title" style="color: #f59e0b;">⚠️ Confidence</div><div class="epistemic-content">Low confidence due to limited or conflicting source material.</div></div>')

    return "".join(html_parts)


def handle_file_upload(uploaded_file):
    """Handle file upload and indexing"""
    try:
        corpus_dir = PROJECT_ROOT / "data" / "corpus"
        corpus_dir.mkdir(parents=True, exist_ok=True)

        file_path = corpus_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.uploaded_files.append({
            "name": uploaded_file.name,
            "path": str(file_path),
            "size": uploaded_file.size,
            "timestamp": datetime.now().isoformat()
        })

        with st.spinner(f"Archiving {uploaded_file.name}..."):
            from pipelines.pdf_extraction.multimodal_ingest import MultimodalIngestPipeline
            ingester = MultimodalIngestPipeline()
            stats = asyncio.run(ingester.process_pdf(file_path))

        return True, stats
    except Exception as e:
        return False, str(e)


def get_document_registry():
    """Get document registry instance"""
    import sys
    sys.path.append(str(PROJECT_ROOT))
    from utils.document_registry import get_registry
    return get_registry()


def get_status_emoji(status: str) -> str:
    """Get emoji for document status"""
    return {
        "indexed": "🟢",
        "indexing": "🟡",
        "queued": "⚪",
        "error": "🔴"
    }.get(status, "⚪")


def get_status_color(status: str) -> str:
    """Get CSS color for document status"""
    return {
        "indexed": "#238636",
        "indexing": "#f59e0b",
        "queued": "#8b949e",
        "error": "#da3633"
    }.get(status, "#8b949e")


def format_file_size(size_bytes: int) -> str:
    """Format file size for display"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_time_ago(iso_timestamp: str) -> str:
    """Format timestamp as relative time"""
    if not iso_timestamp:
        return "Unknown"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now()
        diff = now - dt

        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except:
        return "Unknown"


def delete_selected_documents(registry, doc_ids):
    """Delete selected documents from registry"""
    deleted_count = 0
    for doc_id in doc_ids:
        try:
            doc = registry.get_document(doc_id)
            if doc:
                # Delete from filesystem
                if os.path.exists(doc.filepath):
                    os.remove(doc.filepath)
                # Delete from registry
                registry.delete_document(doc_id)
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting {doc_id}: {e}")
    return deleted_count


def render_enhanced_archive_panel():
    """Render the enhanced Archive Panel with status indicators and document scoping."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))

    st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 1rem;">📚 Archive</div>', unsafe_allow_html=True)

    # Get document registry
    try:
        registry = get_document_registry()
    except Exception as e:
        st.error(f"Registry error: {e}")
        render_legacy_archive()
        return

    # Refresh documents from registry
    try:
        all_docs = registry.list_documents(limit=100)
    except Exception as e:
        st.error(f"Failed to load documents: {e}")
        all_docs = []

    # Sync session uploaded_files with registry
    sync_uploaded_files_with_registry(registry, all_docs)

    # Get stats
    try:
        stats = registry.get_stats()
    except:
        stats = {"total": 0, "indexed": 0, "indexing": 0, "queued": 0, "errors": 0}

    # Header with count
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown(f'<span style="color: #8b949e; font-size: 0.85rem;">{stats["total"]} documents • {stats["indexed"]} indexed</span>', unsafe_allow_html=True)
    with col_header2:
        if st.button("🔄", key="refresh_archive", help="Refresh document list"):
            st.rerun()

    # Search bar
    search_query = st.text_input(
        "Search documents",
        value=st.session_state.archive_search,
        placeholder="Filter by filename...",
        label_visibility="collapsed"
    )
    st.session_state.archive_search = search_query

    # Filter chips - only All, PDF, Image, Text (removed Indexed, Indexing)
    filter_cols = st.columns(4)
    filter_options = [
        ("all", "All"),
        ("pdf", "PDF"),
        ("image", "Image"),
        ("text", "Text")
    ]

    for i, (filter_key, label) in enumerate(filter_options):
        with filter_cols[i]:
            is_active = st.session_state.archive_filter == filter_key
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"filter_{filter_key}", type=btn_type, use_container_width=True):
                st.session_state.archive_filter = filter_key
                st.rerun()

    # Filter documents
    filtered_docs = filter_documents(all_docs, st.session_state.archive_filter, search_query)

    # Delete selected button (appears when documents selected)
    if st.session_state.selected_docs:
        st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        cols = st.columns([3, 2])
        with cols[0]:
            st.markdown(f"<span style='color: #8b949e; font-size: 0.85rem;'>{len(st.session_state.selected_docs)} selected</span>", unsafe_allow_html=True)
        with cols[1]:
            if st.button("🗑️ Delete", key="delete_selected", type="primary", use_container_width=True):
                count = delete_selected_documents(registry, st.session_state.selected_docs)
                st.session_state.selected_docs = set()
                st.success(f"Deleted {count} documents")
                st.rerun()

    # Document list
    st.markdown('<div style="max-height: 400px; overflow-y: auto; margin-top: 1rem;">', unsafe_allow_html=True)

    if not filtered_docs:
        st.markdown('''
        <div style="text-align: center; padding: 2rem; color: #8b949e;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📜</div>
            <div style="font-style: italic;">No documents match filters</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        for doc in filtered_docs:
            render_document_row(doc, registry)

    st.markdown('</div>', unsafe_allow_html=True)

    # Scope indicator
    if st.session_state.document_scope:
        st.markdown('<div style="margin-top: 1rem; padding: 0.5rem; background: rgba(56, 189, 248, 0.1); border-radius: 4px; border-left: 3px solid #38bdf8;">', unsafe_allow_html=True)
        col_scope1, col_scope2 = st.columns([4, 1])
        with col_scope1:
            scope_doc = registry.get_document(st.session_state.document_scope)
            if scope_doc:
                st.markdown(f'<span style="font-size: 0.85rem; color: #38bdf8;">🔍 Scoped to: <strong>{scope_doc.filename}</strong></span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span style="font-size: 0.85rem; color: #38bdf8;">🔍 Scoped to document</span>', unsafe_allow_html=True)
        with col_scope2:
            if st.button("Clear", key="clear_scope", type="secondary"):
                st.session_state.document_scope = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def sync_uploaded_files_with_registry(registry, docs):
    """Sync session uploaded_files with registry documents"""
    doc_paths = {d.filepath for d in docs}

    # Add any missing docs from session to registry
    for uploaded in st.session_state.uploaded_files:
        if uploaded["path"] not in doc_paths:
            import hashlib
            file_path = Path(uploaded["path"])
            if file_path.exists():
                file_hash = hashlib.md5(open(file_path, "rb").read(4096)).hexdigest()
                file_type = "pdf" if file_path.suffix.lower() == ".pdf" else "unknown"
                try:
                    registry.register_document(
                        doc_id=file_hash,
                        filename=uploaded["name"],
                        filepath=uploaded["path"],
                        file_size=uploaded.get("size", 0),
                        file_type=file_type
                    )
                except:
                    pass


def filter_documents(docs, filter_key, search_query):
    """Filter documents by type/status and search query"""
    filtered = docs

    # Apply status filter
    if filter_key == "indexed":
        filtered = [d for d in filtered if d.status == "indexed"]
    elif filter_key == "indexing":
        filtered = [d for d in filtered if d.status in ("indexing", "queued")]
    elif filter_key in ("pdf", "image", "text"):
        filtered = [d for d in filtered if d.file_type == filter_key]

    # Apply search filter
    if search_query:
        search_lower = search_query.lower()
        filtered = [d for d in filtered if search_lower in d.filename.lower()]

    return filtered


def render_document_row(doc, registry):
    """Render a single document row with checkbox, status indicator and scoping action"""
    is_scoped = st.session_state.document_scope == doc.id
    is_indexed = doc.status == "indexed"

    # Determine status display
    status_emoji = get_status_emoji(doc.status)
    status_color = get_status_color(doc.status)

    # Progress indicator for indexing
    progress_html = ""
    if doc.status == "indexing" and doc.chunks_total > 0:
        progress_pct = int((doc.chunks_indexed / doc.chunks_total) * 100)
        progress_html = f' <span style="color: #f59e0b; font-size: 0.75rem;">({progress_pct}%)</span>'

    # Build row with checkbox for deletion
    scope_class = "scoped" if is_scoped else ""
    opacity = "opacity: 0.7;" if doc.status in ("indexing", "queued", "error") else ""

    # Use columns for checkbox and document info
    col_checkbox, col_doc, col_info, col_scope = st.columns([0.5, 4, 1, 1])

    with col_checkbox:
        # Checkbox for deletion selection
        is_selected = doc.id in st.session_state.selected_docs
        if st.checkbox("", value=is_selected, key=f"chk_{doc.id}", label_visibility="collapsed"):
            st.session_state.selected_docs.add(doc.id)
        else:
            st.session_state.selected_docs.discard(doc.id)

    with col_doc:
        row_html = f'''
        <div style="
            padding: 0.5rem 0;
            opacity: {0.7 if doc.status in ('indexing', 'queued', 'error') else 1.0};
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1rem;">{status_emoji}</span>
                <span style="font-size: 1rem;">📄</span>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 0.9rem; color: {'#38bdf8' if is_scoped else '#ffffff'}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {doc.filename}
                    </div>
                    <div style="font-size: 0.75rem; color: #8b949e;">
                        {doc.file_type.upper()} • {format_file_size(doc.file_size)} • {format_time_ago(doc.added_at)}
                    </div>
                </div>
            </div>
        </div>
        '''
        st.markdown(row_html, unsafe_allow_html=True)

    with col_info:
        st.markdown(f'<span style="color: {status_color}; font-size: 0.75rem; font-weight: 500;">{doc.status.title()}{progress_html}</span>', unsafe_allow_html=True)

    with col_scope:
        # Info and scope buttons for indexed docs
        if is_indexed:
            preview_key = f"preview_{doc.id}"
            if preview_key not in st.session_state:
                st.session_state[preview_key] = False

            cols = st.columns(2)
            with cols[0]:
                info_help = "Hide details" if st.session_state[preview_key] else "Show details"
                if st.button("ℹ️", key=f"info_{doc.id}", help=info_help):
                    st.session_state[preview_key] = not st.session_state[preview_key]
                    st.rerun()
            with cols[1]:
                if is_scoped:
                    if st.button("✓", key=f"scope_{doc.id}", help="Currently scoped", type="primary"):
                        pass
                else:
                    if st.button("🔍", key=f"scope_{doc.id}", help=f"Scope to {doc.filename}"):
                        st.session_state.document_scope = doc.id
                        st.rerun()

            # Show metadata preview if toggled
            if st.session_state[preview_key]:
                with st.spinner("Loading metadata..."):
                    metadata = get_document_metadata_from_qdrant(doc.id, doc.filename)
                    if metadata:
                        render_metadata_preview(doc, metadata)
                    else:
                        st.info("No detailed metadata available.")


def render_legacy_archive():
    """Fallback archive display using session state"""
    if st.session_state.uploaded_files:
        for doc in st.session_state.uploaded_files:
            st.markdown(f'''
            <div class="artifact-card">
                <div style="color: #ffffff;">📄 {doc["name"]}</div>
                <div style="font-size: 0.8rem; color: #8b949e;">{(doc["size"] / 1024):.1f} KB</div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">📜</div>Archive empty</div>', unsafe_allow_html=True)


def render_upload_section():
    """Render document upload section with dark aesthetic"""
    st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 1rem;">📜 Archive Documents</div>', unsafe_allow_html=True)

    with st.expander("Upload to Archive", expanded=True):
        st.markdown('<div class="upload-temple">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Deposit manuscript or artifact",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff'],
            help="Contribute to the knowledge base"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_file is not None:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f'''
                <div style="color: #ffffff;">
                    <strong>Manuscript:</strong> {uploaded_file.name}<br>
                    <span style="color: #8b949e;">{uploaded_file.size / 1024:.1f} KB • {uploaded_file.type}</span>
                </div>
                ''', unsafe_allow_html=True)

            with col2:
                if st.button("📥 Archive Document", type="primary"):
                    success, result = handle_file_upload(uploaded_file)
                    if success:
                        st.success("✅ Archived successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ Failed: {result}")

    if st.session_state.uploaded_files:
        st.caption(f"📚 {len(st.session_state.uploaded_files)} manuscript(s) in archive")


def render_scope_banner():
    """Render the active scope banner"""
    if st.session_state.document_scope:
        import sys
        sys.path.append(str(PROJECT_ROOT))
        from utils.document_registry import get_registry
        registry = get_registry()
        doc = registry.get_document(st.session_state.document_scope)

        if doc:
            st.markdown(f'''
            <div style="
                background: rgba(56, 189, 248, 0.1);
                border: 1px solid #38bdf8;
                border-radius: 8px;
                padding: 0.75rem 1rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1rem;">🔍</span>
                    <span style="color: #38bdf8; font-weight: 500;">
                        Scoped to: <strong>{doc.filename}</strong>
                    </span>
                </div>
                <span style="color: #8b949e; font-size: 0.85rem;">
                    Queries limited to this document
                </span>
            </div>
            ''', unsafe_allow_html=True)


def render_chat_interface(orchestrator, top_k_text, top_k_images):
    """Render the chat interface with 3-column layout"""
    # Show scope banner if active
    render_scope_banner()

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'''
            <div class="manuscript-message manuscript-user">
                <div class="manuscript-role">Inquirer</div>
                <div class="manuscript-content">{message["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="manuscript-message manuscript-assistant">
                <div class="manuscript-role">Heritage Lens</div>
                <div class="manuscript-content">{message["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)

    query = st.chat_input("Ask a research question in any language...")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner("Consulting archives..."):
            try:
                strict_mode = st.session_state.get("strict_corpus_mode", True)
                result = asyncio.run(process_query(orchestrator, query, top_k_text, top_k_images, strict_mode))

                l1_answer = result["layers"]["l1_answer"]
                l2_attribution = result["layers"]["l2_attribution"]
                l3_epistemic = result["layers"]["l3_epistemic"]
                images = result["retrieval"]["images"]

                # 3-Column Layout
                col1, col2, col3 = st.columns([4, 3, 3])

                # Left Column: THE ANSWER - Single HTML string for proper card wrapping
                with col1:
                    answer_html = f'''
                    <div class="column-container">
                        <div class="column-header">THE ANSWER</div>
                        <div class="layer-content">{l1_answer}</div>
                    </div>
                    '''
                    st.markdown(answer_html, unsafe_allow_html=True)

                    # Images render separately below the card
                    if images:
                        for img in images[:2]:
                            render_inline_image(img)

                # Center Column: SOURCES - Single HTML string for proper card wrapping
                with col2:
                    sources_html = render_sources_compact_html(l2_attribution)
                    st.markdown(f'''
                    <div class="column-container">
                        <div class="column-header">SOURCES</div>
                        {sources_html}
                    </div>
                    ''', unsafe_allow_html=True)

                # Right Column: WHAT THIS ANSWER DOESN'T KNOW - Single HTML string with glow
                with col3:
                    epistemic_html = render_epistemic_compact_html(l3_epistemic)
                    st.markdown(f'''
                    <div class="column-container-glow">
                        <div class="column-header">WHAT THIS ANSWER DOESN\'T KNOW</div>
                        {epistemic_html}
                    </div>
                    ''', unsafe_allow_html=True)

                st.session_state.messages.append({"role": "assistant", "content": l1_answer})

            except Exception as e:
                st.error(f"❌ Error: {e}")
                import traceback
                st.error(traceback.format_exc())


async def process_query(bridge, query, top_k_text, top_k_images, strict_corpus=True):
    """Process a query through OpenClaw bridge or direct orchestrator"""
    # Build document scope from session state
    document_scope = None
    if st.session_state.document_scope:
        registry = get_document_registry()
        doc = registry.get_document(st.session_state.document_scope)
        if doc:
            document_scope = [doc.filename]

    context = {
        "top_k_text": top_k_text,
        "top_k_images": top_k_images,
        "strict_corpus": strict_corpus,
        "document_scope": document_scope
    }
    if hasattr(bridge, 'handle_query'):
        return await bridge.handle_query(
            query=query,
            session_id=st.session_state.session_id,
            context=context
        )
    else:
        return await bridge.process_query(
            query=query,
            session_id=st.session_state.session_id,
            top_k_text=top_k_text,
            top_k_images=top_k_images,
            strict_corpus=strict_corpus,
            document_scope=document_scope
        )


def main():
    """Main UI function"""
    initialize_session_state()

    # Header with mission tag
    st.markdown('''
    <div class="header-container">
        <div class="main-header">🏛️ Heritage Lens Agent</div>
        <div class="mission-tag">KXSB AR26 — MISSION 4</div>
    </div>
    ''', unsafe_allow_html=True)

    bridge = get_openclaw_bridge()
    if bridge is None:
        st.error("❌ System not configured. Check API keys and services.")
        return

    # Sidebar configuration
    with st.sidebar:
        st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #38bdf8; margin-bottom: 1rem;">⚙️ Configuration</div>', unsafe_allow_html=True)

        st.session_state.show_layers = st.toggle(
            "Show All Layers",
            value=st.session_state.show_layers
        )

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Answer Mode</div>', unsafe_allow_html=True)
        st.session_state.strict_corpus_mode = st.toggle(
            "🔒 Strict Corpus-Only Mode",
            value=st.session_state.strict_corpus_mode,
            help="When enabled, answers use ONLY your uploaded documents."
        )
        if st.session_state.strict_corpus_mode:
            st.caption("✅ Answers strictly from your corpus")
        else:
            st.caption("⚠️ General knowledge enabled")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Retrieval Settings</div>', unsafe_allow_html=True)
        top_k_text = st.slider("Text sources", 1, 10, 5)
        top_k_images = st.slider("Visual references", 0, 5, 3)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Research Focus</div>', unsafe_allow_html=True)
        st.session_state.research_context = st.text_area(
            "Context (optional)",
            value=st.session_state.research_context,
            placeholder="E.g., Olmec colossal heads...",
            help="Guide the inquiry"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-header">Archive Status</div>', unsafe_allow_html=True)
        try:
            stats = bridge.get_stats()
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="metric-column"><div class="metric-value">{stats.get("images_indexed", 0)}</div><div class="metric-label">Artifacts</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-column"><div class="metric-value">{stats.get("documents_indexed", 0)}</div><div class="metric-label">Manuscripts</div></div>', unsafe_allow_html=True)
        except:
            st.info("Archive stats unavailable")
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔄 New Research", use_container_width=True):
            reset_session()
            st.rerun()

        if st.button("🧪 Sample Query", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "What are the key characteristics of Olmec colossal heads?"
            })
            st.rerun()

        with st.expander("❓ Guide"):
            st.markdown('''
            <div style="font-size: 0.9rem; color: #8b949e;">
                <strong>How to inquire:</strong><br>
                1. Upload manuscripts to the archive<br>
                2. Pose questions about cultural heritage<br>
                3. Review the three layers of analysis<br><br>
                <strong>The Three Layers:</strong><br>
                • <span style="color: #38bdf8;">Answer</span> — Direct response<br>
                • <span style="color: #8b949e;">Sources</span> — Attribution<br>
                • <span style="color: #f59e0b;">Analysis</span> — Bias & confidence
            </div>
            ''', unsafe_allow_html=True)

    # Main content - INQUIRY AT TOP
    st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin: 1rem 0;">💬 Inquiry</div>', unsafe_allow_html=True)

    # Inquiry input at top
    query = st.text_input(
        "Research question",
        placeholder="Ask a research question in any language...",
        label_visibility="collapsed",
        key="top_inquiry"
    )

    if query and query != st.session_state.get("last_query", ""):
        st.session_state.last_query = query
        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner("Consulting archives..."):
            try:
                strict_mode = st.session_state.get("strict_corpus_mode", True)
                result = asyncio.run(process_query(bridge, query, top_k_text, top_k_images, strict_mode))

                l1_answer = result["layers"]["l1_answer"]
                l2_attribution = result["layers"]["l2_attribution"]
                l3_epistemic = result["layers"]["l3_epistemic"]
                images = result["retrieval"]["images"]

                st.session_state.last_result = {
                    "l1_answer": l1_answer,
                    "l2_attribution": l2_attribution,
                    "l3_epistemic": l3_epistemic,
                    "images": images
                }
                st.session_state.messages.append({"role": "assistant", "content": l1_answer})
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Show results if available
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        l1_answer = result["l1_answer"]
        l2_attribution = result["l2_attribution"]
        l3_epistemic = result["l3_epistemic"]
        images = result["images"]

        st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

        # 3-Column Layout at bottom
        col1, col2, col3 = st.columns([4, 3, 3])

        # Left Column: THE ANSWER - Single HTML string for proper card wrapping
        with col1:
            answer_html = f'''
            <div class="column-container">
                <div class="column-header">THE ANSWER</div>
                <div class="layer-content">{l1_answer}</div>
            </div>
            '''
            st.markdown(answer_html, unsafe_allow_html=True)

            # Images render separately below the card
            if images:
                for img in images[:2]:
                    render_inline_image(img)

        # Center Column: SOURCES - Single HTML string for proper card wrapping
        with col2:
            sources_html = render_sources_compact_html(l2_attribution)
            st.markdown(f'''
            <div class="column-container">
                <div class="column-header">SOURCES</div>
                {sources_html}
            </div>
            ''', unsafe_allow_html=True)

        # Right Column: WHAT THIS ANSWER DOESN'T KNOW - Single HTML string with glow
        with col3:
            epistemic_html = render_epistemic_compact_html(l3_epistemic)
            st.markdown(f'''
            <div class="column-container-glow">
                <div class="column-header">WHAT THIS ANSWER DOESN\'T KNOW</div>
                {epistemic_html}
            </div>
            ''', unsafe_allow_html=True)

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Two column layout for Archive and rest
    col_left, col_right = st.columns([3, 1])

    with col_left:
        render_upload_section()

        # Show conversation history
        if st.session_state.messages:
            st.markdown('<div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin: 1rem 0;">📜 Conversation</div>', unsafe_allow_html=True)
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'''
                    <div class="manuscript-message manuscript-user">
                        <div class="manuscript-role">Inquirer</div>
                        <div class="manuscript-content">{message["content"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="manuscript-message manuscript-assistant">
                        <div class="manuscript-role">Heritage Lens</div>
                        <div class="manuscript-content">{message["content"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)

    with col_right:
        render_enhanced_archive_panel()

        st.markdown('<div style="margin: 1rem 0;"></div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 0.9rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem;">📈 Session</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div style="text-align: center; padding: 1rem; background: #161b22; border-radius: 8px; border: 1px solid #30363d;">
            <div style="font-size: 1.5rem; color: #38bdf8; font-weight: 700;">{len(st.session_state.messages)}</div>
            <div style="font-size: 0.75rem; color: #8b949e; text-transform: uppercase;">Exchanges</div>
        </div>
        ''', unsafe_allow_html=True)

    # Footer status bar
    bridge_status = "✅ Connected" if hasattr(bridge, 'handle_query') else "⚠️ Fallback mode"
    st.markdown(f'''
    <div class="footer-status">
        <div class="status-indicator">
            <span class="status-dot"></span>
            <span>OpenClaw Agent Orchestration {bridge_status}</span>
        </div>
        <span>Session: {st.session_state.session_id[:8]}...</span>
    </div>
    ''', unsafe_allow_html=True)


def get_document_metadata_from_qdrant(doc_id, filename):
    """Aggregate metadata from Qdrant for a specific document."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        qdrant = QdrantClient(url="http://qdrant:6333")

        search_filter = Filter(
            must=[
                FieldCondition(key="source", match=MatchValue(value=filename))
            ]
        )

        result = qdrant.query_points(
            collection_name="heritage_lens_text",
            query_filter=search_filter,
            limit=100,
            with_payload=True
        )

        if not result.points:
            return {}

        pages = set()
        languages = set()
        cultural_contexts = set()
        perspectives = set()
        institutions = set()
        dates = set()

        for point in result.points:
            payload = point.payload or {}
            if page := payload.get("page"):
                pages.add(page)
            if lang := payload.get("language"):
                languages.add(lang)
            if cc := payload.get("cultural_context"):
                if isinstance(cc, list):
                    cultural_contexts.update(cc)
                else:
                    cultural_contexts.add(cc)
            if persp := payload.get("perspective"):
                perspectives.add(persp)
            if inst := payload.get("institution"):
                institutions.add(inst)
            if date := payload.get("date"):
                dates.add(date)

        metadata = {
            "chunk_count": len(result.points),
            "page_range": f"{min(pages)}-{max(pages)}" if pages else "Unknown",
            "languages": list(languages) if languages else ["en"],
            "cultural_context": list(cultural_contexts) if cultural_contexts else ["Mesoamerican"],
            "perspectives": list(perspectives) if perspectives else ["western_academic"],
            "institutions": list(institutions) if institutions else ["unknown"],
            "dates": list(dates) if dates else [],
        }

        return metadata

    except Exception as e:
        print(f"Error getting metadata from Qdrant: {e}")
        return {}


def generate_document_abstract(doc, chunks_metadata):
    """Generate a brief abstract describing the document."""
    parts = []

    contexts = chunks_metadata.get("cultural_context", ["Mesoamerican"])
    if contexts:
        parts.append(f"A document related to {', '.join(contexts)} cultural heritage.")

    chunk_count = chunks_metadata.get("chunk_count", 0)
    if chunk_count > 0:
        parts.append(f"Contains {chunk_count} indexed text segments")
        page_range = chunks_metadata.get("page_range")
        if page_range and page_range != "Unknown":
            parts.append(f"across {page_range} pages")
        parts.append(".")

    perspectives = chunks_metadata.get("perspectives", [])
    if perspectives:
        persp_str = perspectives[0].replace("_", " ")
        parts.append(f"Written from a {persp_str} perspective.")

    return " ".join(parts) if parts else "A cultural heritage document awaiting analysis."


def render_metadata_preview(doc, metadata):
    """Render the metadata preview panel for a document."""
    abstract = generate_document_abstract(doc, metadata)

    html = f'''
    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; margin-top: 0.5rem; border-left: 3px solid #38bdf8;">
        <div style="font-size: 0.9rem; color: #ffffff; font-weight: 600; margin-bottom: 0.75rem; border-bottom: 1px solid #30363d; padding-bottom: 0.5rem;">📋 Document Overview</div>

        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem; border-bottom: 1px dotted #30363d;">
            <span style="color: #8b949e; font-weight: 500;">Indexed Chunks</span>
            <span style="color: #ffffff;">{metadata.get("chunk_count", doc.chunks_indexed)}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem; border-bottom: 1px dotted #30363d;">
            <span style="color: #8b949e; font-weight: 500;">Page Range</span>
            <span style="color: #ffffff;">{metadata.get("page_range", "N/A")}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem; border-bottom: 1px dotted #30363d;">
            <span style="color: #8b949e; font-weight: 500;">Language</span>
            <span style="color: #ffffff;">{', '.join(metadata.get("languages", ["en"]))}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem; border-bottom: 1px dotted #30363d;">
            <span style="color: #8b949e; font-weight: 500;">Cultural Context</span>
            <span style="color: #ffffff;">{', '.join(metadata.get("cultural_context", ["Mesoamerican"]))}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem;">
            <span style="color: #8b949e; font-weight: 500;">Perspective</span>
            <span style="color: #ffffff;">{metadata.get("perspectives", ["western_academic"])[0].replace("_", " ").title()}</span>
        </div>
    '''

    institutions = metadata.get("institutions", [])
    if institutions and institutions[0] != "unknown":
        html += f'''
        <div style="display: flex; justify-content: space-between; padding: 0.35rem 0; font-size: 0.8rem;">
            <span style="color: #8b949e; font-weight: 500;">Institution</span>
            <span style="color: #ffffff;">{institutions[0].title()}</span>
        </div>
        '''

    html += f'''
        <div style="background: #0d1117; border-radius: 4px; padding: 0.75rem; margin-top: 0.75rem; font-size: 0.85rem; color: #c9d1d9; font-style: italic; line-height: 1.5;">
            {abstract}
        </div>
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
