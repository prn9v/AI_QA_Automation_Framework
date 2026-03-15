import streamlit as st
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# Add src to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ai_generator import AITestGenerator
from src.parser import TestCaseParser
from src.test_runner import TestRunner

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Test-Case Generator",
    page_icon="🤖",
    layout="wide"
)

# ─── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .tc-card {
        background: #f8f9fa;
        border-left: 4px solid #1f77b4;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .tc-id { 
        font-size: 0.8rem; 
        color: #888; 
        font-weight: 600;
        text-transform: uppercase;
    }
    .tc-title { 
        font-size: 1.1rem; 
        font-weight: 700; 
        color: #1a1a2e;
        margin: 0.2rem 0;
    }
    .badge-high { background:#ffe0e0; color:#c0392b; padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-medium { background:#fff3cd; color:#856404; padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .badge-low { background:#d4edda; color:#155724; padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:600; }
    .stat-box {
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ────────────────────────────────────────────────────
st.markdown('<div class="main-header">🤖 AI Test-Case Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by Hugging Face • Llama 3.1 • pytest Automation</div>', unsafe_allow_html=True)
st.divider()

# ─── Session State Init ────────────────────────────────────────
if "test_cases" not in st.session_state:
    st.session_state.test_cases = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_feature" not in st.session_state:
    st.session_state.last_feature = ""
if "report_path" not in st.session_state:
    st.session_state.report_path = ""
if "run_results" not in st.session_state:
    st.session_state.run_results = None

# ─── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://huggingface.co/front/assets/huggingface_logo-noborder.svg", width=40)
    st.markdown("### ⚙️ Configuration")
    
    
    env_key = os.getenv("HF_API_KEY", "")

    # Streamlit Cloud stores secrets here
    try:
        cloud_key = st.secrets["HF_API_KEY"]
    except:
        cloud_key = ""

    if env_key:
        hf_key = env_key
        st.success("✅ API key loaded automatically")
    elif cloud_key:
        hf_key = cloud_key
        st.success("✅ API key loaded from cloud secrets")
    else:
        # Only show input box if no key found anywhere
        hf_key = st.text_input( 
            "Hugging Face API Key",
            type="password",
            placeholder="hf_...",
            help="Get your free key at huggingface.co/settings/tokens"
        )
        
    if not hf_key:
        st.warning("⚠️ Enter your HF API key to continue")
    
    num_cases = st.slider("Number of test cases", min_value=2, max_value=10, value=5)
    
    st.divider()
    st.markdown("### 📋 Quick Examples")
    examples = [
        "User login page",
        "Payment gateway",
        "User registration form",
        "Password reset flow",
        "Search & filter functionality",
        "Shopping cart checkout",
        "File upload feature",
        "API rate limiting"
    ]
    for ex in examples:
        if st.button(f"▶ {ex}", use_container_width=True, key=f"ex_{ex}"):
            st.session_state.quick_example = ex

    st.divider()
    st.markdown("### 📊 Session Stats")
    st.metric("Total Test Cases", len(st.session_state.test_cases))
    st.metric("Chat Refinements", len(st.session_state.chat_history))

# ─── Main Tabs ─────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🧪 Generate Tests", "💬 Chat & Refine", "📄 Reports"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — GENERATE
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Describe the feature you want to test")
    
    # Pre-fill if quick example was clicked
    default_val = st.session_state.get("quick_example", "")
    feature = st.text_area(
        "Feature description",
        value=default_val,
        placeholder="e.g. Payment gateway with credit card validation, 3D secure, and refund handling",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button("🚀 Generate", type="primary", use_container_width=True)
    with col2:
        run_btn = st.button("▶️ Run Tests", use_container_width=True, 
                           disabled=len(st.session_state.test_cases) == 0)

    # ── Generate ──
    if generate_btn:
        if not hf_key:
            st.error("⚠️ Please enter your Hugging Face API key in the sidebar.")
        elif not feature.strip():
            st.error("⚠️ Please enter a feature description.")
        else:
            os.environ["HF_API_KEY"] = hf_key
            
            with st.spinner("🤖 AI is generating test cases..."):
                try:
                    generator = AITestGenerator()
                    raw = generator.generate_test_cases(feature, num_cases)
                    
                    parser = TestCaseParser()
                    test_cases = parser.parse(raw)
                    
                    st.session_state.test_cases = test_cases
                    st.session_state.last_feature = feature
                    st.session_state.chat_history = []
                    st.success(f"✅ Generated {len(test_cases)} test cases!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ── Run Tests ──
    if run_btn and st.session_state.test_cases:
        if not hf_key:
            st.error("⚠️ Please enter your Hugging Face API key in the sidebar.")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            feature_slug = st.session_state.last_feature.replace(" ", "_")[:25]
            pytest_path = f"tests/generated/test_{feature_slug}_{timestamp}.py"
            report_path = f"reports/report_{feature_slug}_{timestamp}.html"
            
            os.makedirs("tests/generated", exist_ok=True)
            os.makedirs("reports", exist_ok=True)
            
            with st.spinner("🔬 Running tests with pytest..."):
                try:
                    runner = TestRunner()
                    runner.generate_pytest_file(st.session_state.test_cases, pytest_path)
                    results = runner.run_tests(pytest_path, report_path)
                    
                    st.session_state.run_results = results
                    st.session_state.report_path = os.path.abspath(report_path)
                    
                except Exception as e:
                    st.error(f"❌ Error running tests: {str(e)}")

    # ── Display Results ──
    if st.session_state.run_results:
        r = st.session_state.run_results
        st.divider()
        st.markdown("### 📊 Test Run Results")
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Passed", r["passed"])
        c2.metric("❌ Failed", r["failed"])
        c3.metric("📋 Total", r["total"])
        
        if st.session_state.report_path and os.path.exists(st.session_state.report_path):
            with open(st.session_state.report_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.download_button(
                "📥 Download HTML Report",
                data=html_content,
                file_name="test_report.html",
                mime="text/html",
                use_container_width=True
            )

    # ── Display Test Cases ──
    if st.session_state.test_cases:
        st.divider()
        st.markdown(f"### 📋 Generated Test Cases ({len(st.session_state.test_cases)})")
        
        # Export JSON button
        json_str = json.dumps(st.session_state.test_cases, indent=2)
        st.download_button(
            "📥 Export as JSON",
            data=json_str,
            file_name="test_cases.json",
            mime="application/json"
        )
        
        for tc in st.session_state.test_cases:
            priority = tc.get("priority", "Medium")
            badge_class = f"badge-{priority.lower()}"
            
            with st.expander(f"**{tc['id']}** — {tc['title']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**📌 Preconditions:** {tc['preconditions']}")
                    st.markdown("**🔢 Steps:**")
                    for i, step in enumerate(tc.get("steps", []), 1):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;{i}. {step}")
                    st.markdown(f"**✅ Expected Result:** {tc['expected_result']}")
                with col2:
                    st.markdown(f"**Priority:** `{priority}`")
                    st.markdown(f"**Type:** `{tc.get('test_type', 'Functional')}`")

# ══════════════════════════════════════════════════════════════
# TAB 2 — CHAT & REFINE
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 💬 Refine your test cases conversationally")
    
    if not st.session_state.test_cases:
        st.info("👆 First generate some test cases in the **Generate Tests** tab.")
    else:
        st.success(f"Working on: **{st.session_state.last_feature}** — {len(st.session_state.test_cases)} test cases so far")
        
        # Chat history display
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Suggested prompts
        st.markdown("**💡 Try these:**")
        sc1, sc2, sc3, sc4 = st.columns(4)
        suggestions = [
            ("➕ Edge cases", "add edge cases"),
            ("➖ Negative tests", "add negative tests"),
            ("🔒 Security tests", "add security test cases"),
            ("⚡ Performance", "add performance test cases")
        ]
        for col, (label, prompt) in zip([sc1, sc2, sc3, sc4], suggestions):
            with col:
                if st.button(label, use_container_width=True, key=f"sug_{prompt}"):
                    st.session_state.chat_input_val = prompt

        # Chat input
        user_input = st.chat_input("Ask AI to refine tests... e.g. 'add edge cases for network timeout'")
        
        if user_input:
            if not hf_key:
                st.error("⚠️ Please enter your Hugging Face API key in the sidebar.")
            else:
                os.environ["HF_API_KEY"] = hf_key
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                with st.spinner("🤖 AI is generating more test cases..."):
                    try:
                        generator = AITestGenerator()
                        refine_prompt = f"Feature: {st.session_state.last_feature}. User request: {user_input}. Generate 3 test cases."
                        raw = generator.generate_test_cases(refine_prompt, 3)
                        
                        parser = TestCaseParser()
                        new_cases = parser.parse(raw)
                        
                        # Re-ID the new cases to avoid conflicts
                        existing_count = len(st.session_state.test_cases)
                        for i, tc in enumerate(new_cases):
                            tc["id"] = f"TC{existing_count + i + 1:03d}"
                        
                        st.session_state.test_cases.extend(new_cases)
                        
                        reply = f"Added {len(new_cases)} new test cases! Total is now {len(st.session_state.test_cases)}."
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ══════════════════════════════════════════════════════════════
# TAB 3 — REPORTS
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📄 Test Reports")
    
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        report_files = [f for f in os.listdir(reports_dir) if f.endswith(".html")]
        
        if not report_files:
            st.info("No reports yet. Generate and run tests first.")
        else:
            st.success(f"Found {len(report_files)} report(s)")
            for rf in sorted(report_files, reverse=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"📄 `{rf}`")
                with col2:
                    with open(os.path.join(reports_dir, rf), "r", encoding="utf-8") as f:
                        st.download_button(
                            "Download",
                            data=f.read(),
                            file_name=rf,
                            mime="text/html",
                            key=f"dl_{rf}"
                        )
    else:
        st.info("No reports yet. Generate and run tests first.")

# ─── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center; color:#888; font-size:0.85rem'>"
    "AI Test-Case Generator • Built with Streamlit + Hugging Face + pytest"
    "</div>",
    unsafe_allow_html=True
)