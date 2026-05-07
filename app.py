from pathlib import Path

import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

from core import analyze_disclosure, clean_disclosure_text


st.set_page_config(
    page_title="Evidence-Grounded M&A Disclosure Risk Screener",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f5f8fc 0%, #eef3f8 100%);
    }
    .hero-card {
        background: linear-gradient(135deg, #12314d 0%, #1d4e73 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 18px;
        box-shadow: 0 12px 28px rgba(18, 49, 77, 0.14);
    }
    .hero-card h1 {
        margin: 0 0 8px 0;
        font-size: 2rem;
    }
    .hero-card p {
        margin: 0;
        font-size: 1rem;
        color: #e4eef7;
    }
    .chip-row {
        margin-top: 14px;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .chip {
        background: rgba(255,255,255,0.14);
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .subnote {
        margin-top: 10px;
        color: #cfe1f1 !important;
        font-size: 0.92rem !important;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #d7e3ef;
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 8px 24px rgba(20, 37, 63, 0.06);
    }
    .input-card {
        background: #ffffff;
        border: 2px solid #bcd2e8;
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 8px 24px rgba(20, 37, 63, 0.06);
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #d7e3ef;
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(20, 37, 63, 0.06);
    }
    .metric-label {
        color: #5d7387;
        font-size: 0.86rem;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #12314d;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .detail-card {
        background: #f3f6f9;
        border: 1px solid #dbe4ec;
        border-radius: 14px;
        padding: 16px 18px;
        color: #1e3548;
    }
    .claim-card {
        background: #eaf4ff;
        border: 1px solid #bfd7f2;
        border-radius: 14px;
        padding: 16px 18px;
        color: #12314d;
    }
    .evidence-card {
        background: #f7fbff;
        border-left: 4px solid #4a90c2;
        border-radius: 12px;
        padding: 14px 16px;
        border-top: 1px solid #d9e7f2;
        border-right: 1px solid #d9e7f2;
        border-bottom: 1px solid #d9e7f2;
        margin-bottom: 10px;
    }
    .badge {
        display: inline-block;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .badge-high {
        background: #fdeaea;
        color: #a63a3a;
        border: 1px solid #efc3c3;
    }
    .badge-medium {
        background: #fff3e7;
        color: #a05a13;
        border: 1px solid #f3d2a9;
    }
    .badge-low {
        background: #e9f7ef;
        color: #2f7a49;
        border: 1px solid #bddfc7;
    }
    .mini-label {
        color: #5d7387;
        font-size: 0.84rem;
        margin-bottom: 4px;
    }
    .label-badge {
        display: inline-block;
        background: #eaf4ff;
        color: #1d4e73;
        border: 1px solid #bfd7f2;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .scope-note {
        background: #f7fbff;
        border: 1px solid #d7e7f5;
        border-radius: 12px;
        padding: 12px 14px;
        color: #32506a;
        margin-top: 14px;
    }
    .flag-card {
        background: #ffffff;
        border: 1px solid #d7e3ef;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 8px 20px rgba(20, 37, 63, 0.05);
        margin-bottom: 10px;
    }
    .flag-preview {
        color: #4b657b;
        font-size: 0.9rem;
        margin-top: 8px;
    }
    .overview-card {
        background: #ffffff;
        border: 1px solid #d7e3ef;
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 8px 24px rgba(20, 37, 63, 0.06);
        height: 100%;
    }
    .workflow-card {
        background: #f7fbff;
        border: 1px solid #d9e7f2;
        border-radius: 16px;
        padding: 18px 20px;
        color: #173650;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

EXAMPLE_DISCLOSURE = """On April 15, 2024, Company A completed the acquisition of Company B for a total purchase price of $480 million, subject to customary working capital adjustments.

Management expects the acquisition to accelerate revenue growth, expand the company’s presence in the healthcare analytics market, and create cross-selling opportunities across its existing customer base.

The company anticipates achieving approximately $35 million in annual cost savings within 24 months through supply chain integration and operational efficiencies.

The acquired business contributed $120 million in revenue in the prior fiscal year and is expected to enhance the company’s data analytics capabilities.

The transaction will be accounted for as a business combination under applicable accounting standards, and goodwill is expected to be recognized."""


def load_results(path_str):
    path = Path(path_str)
    if path.exists():
        return pd.read_csv(path)
    return None


def extract_text_from_html(file):
    html_content = file.getvalue().decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    visible_text = soup.get_text(separator="\n")
    return clean_disclosure_text(visible_text)


if "disclosure_input" not in st.session_state:
    st.session_state["disclosure_input"] = ""
if "analysis_results" not in st.session_state:
    st.session_state["analysis_results"] = None
if "uploaded_file_token" not in st.session_state:
    st.session_state["uploaded_file_token"] = None


def render_screener_page():
    st.markdown(
        """
        <div class="hero-card">
            <h1>Evidence-Grounded M&amp;A Disclosure Risk Screener</h1>
            <p>Upload or paste an M&amp;A disclosure to identify optimistic claims, retrieve related evidence, and rank paragraphs for review.</p>
            <p class="subnote">Prototype tool for first-pass screening. Not audit or investment advice.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        """
        <div class="scope-note">
            This prototype focuses on optimistic M&amp;A claims, such as synergy, growth, market expansion, and value creation language. It does not attempt full positive/negative sentiment analysis.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown("### Upload or Paste Disclosure")
    st.markdown('<div class="label-badge">Text Input</div>', unsafe_allow_html=True)
    st.caption("You can paste raw copied text from an SEC 8-K or upload a plain .txt file.")
    st.caption("Supports .txt and SEC-style HTML filings. For best results, upload the M&A-related section.")
    st.caption("PDF support can be added in a future version.")

    uploaded_file = st.file_uploader("Upload a disclosure (.txt or .html)", type=["txt", "html"])
    if uploaded_file is not None:
        file_token = f"{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state["uploaded_file_token"] != file_token:
            file_name_lower = uploaded_file.name.lower()
            if file_name_lower.endswith(".html"):
                cleaned_text = extract_text_from_html(uploaded_file)
            else:
                uploaded_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                cleaned_text = clean_disclosure_text(uploaded_text)

            st.session_state["disclosure_input"] = cleaned_text
            st.session_state["analysis_results"] = None
            st.session_state["uploaded_file_token"] = file_token
            st.rerun()

    button_col_1, button_col_2 = st.columns(2)
    with button_col_1:
        if st.button("Try Example Disclosure", use_container_width=True):
            st.session_state["disclosure_input"] = EXAMPLE_DISCLOSURE
            st.session_state["analysis_results"] = None
            st.session_state["uploaded_file_token"] = None
            st.rerun()
    with button_col_2:
        if st.button("Clear Input", use_container_width=True):
            st.session_state["disclosure_input"] = ""
            st.session_state["analysis_results"] = None
            st.session_state["uploaded_file_token"] = None
            st.rerun()

    disclosure_text = st.text_area(
        "Paste disclosure text here",
        key="disclosure_input",
        height=360,
        placeholder="Paste M&A disclosure text here..."
    )
    st.caption("Paste the M&A-related section from an SEC 8-K, press release, or acquisition announcement.")

    if len(disclosure_text) > 30000:
        st.warning("This prototype works best with a selected M&A disclosure section rather than a full filing. Please paste the M&A-related section for better results.")

    if st.button("Analyze Disclosure", type="primary", use_container_width=True):
        input_text = st.session_state["disclosure_input"]
        cleaned_input = clean_disclosure_text(input_text)
        if cleaned_input.strip() == "":
            st.error("Please paste a disclosure or upload a .txt file.")
        else:
            st.session_state["analysis_results"] = analyze_disclosure(cleaned_input)
    st.markdown("</div>", unsafe_allow_html=True)

    results_df = st.session_state["analysis_results"]
    if isinstance(results_df, pd.DataFrame) and not results_df.empty:
        ranked_df = results_df.sort_values(
            by=["risk_score", "has_optimistic_claim", "paragraph_id"],
            ascending=[False, False, True]
        ).reset_index(drop=True)
        risk_color_map = {"high": "badge-high", "medium": "badge-medium", "low": "badge-low"}
        flagged_df = ranked_df[ranked_df["has_optimistic_claim"] == "yes"].copy()

        st.divider()

        metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
        metric_specs = [
            ("Paragraphs Analyzed", len(results_df)),
            ("Optimistic Paragraphs", int((results_df["has_optimistic_claim"] == "yes").sum())),
            ("High-Risk Paragraphs", int((results_df["risk_label"] == "high").sum())),
            ("Average Risk Score", f"{results_df['risk_score'].mean():.2f}"),
        ]
        for col, (label, value) in zip([metric_col_1, metric_col_2, metric_col_3, metric_col_4], metric_specs):
            with col:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

        st.subheader("Flagged Optimistic Paragraphs")
        if flagged_df.empty:
            st.info("No optimistic M&A claims were detected in this disclosure.")
        else:
            selected_jump = st.selectbox(
                "Jump to flagged paragraph",
                options=flagged_df["paragraph_id"].tolist(),
                index=0
            )

            for _, flagged_row in flagged_df.head(8).iterrows():
                badge_class = risk_color_map.get(flagged_row["risk_label"], "badge-low")
                preview = flagged_row["paragraph"]
                if len(preview) > 180:
                    preview = preview[:177] + "..."
                st.markdown(
                    f"""
                    <div class="flag-card">
                        <div class="mini-label">{flagged_row['paragraph_id']} | Score: {flagged_row['risk_score']}</div>
                        <div><span class="badge {badge_class}">{flagged_row['risk_label'].upper()} RISK</span></div>
                        <div style="margin-top:10px;"><strong>Claim:</strong> {flagged_row['claim']}</div>
                        <div class="flag-preview"><strong>Preview:</strong> {preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

        st.subheader("Ranked Paragraph Risk Table")
        st.caption("Rows are sorted by review priority.")
        display_df = ranked_df.copy()
        display_df["risk_label"] = display_df["risk_label"].str.upper()
        st.dataframe(
            display_df[
                [
                    "paragraph_id",
                    "risk_label",
                    "risk_score",
                    "has_optimistic_claim",
                    "claim",
                    "evidence_level",
                    "relationship",
                    "baseline_label",
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Results as CSV",
            data=ranked_df[
                [
                    "paragraph_id",
                    "paragraph",
                    "has_optimistic_claim",
                    "claim",
                    "evidence_level",
                    "relationship",
                    "risk_score",
                    "risk_label",
                    "baseline_label",
                    "top_evidence_1",
                    "top_evidence_2",
                    "top_evidence_3",
                    "explanation",
                ]
            ].to_csv(index=False).encode("utf-8"),
            file_name="disclosure_analysis_results.csv",
            mime="text/csv",
        )

        st.divider()

        st.subheader("Paragraph Detail")
        paragraph_options = flagged_df["paragraph_id"].tolist() + [
            pid for pid in ranked_df["paragraph_id"].tolist() if pid not in flagged_df["paragraph_id"].tolist()
        ]
        default_index = 0
        if not flagged_df.empty:
            default_selected = selected_jump if "selected_jump" in locals() else flagged_df.iloc[0]["paragraph_id"]
            default_index = paragraph_options.index(default_selected)
        selected_paragraph_id = st.selectbox(
            "Select a paragraph to inspect:",
            options=paragraph_options,
            index=default_index
        )
        selected_row = ranked_df[ranked_df["paragraph_id"] == selected_paragraph_id].iloc[0]

        st.markdown("**Original Paragraph**")
        st.markdown(
            f'<div class="detail-card">{selected_row["paragraph"]}</div>',
            unsafe_allow_html=True
        )

        st.markdown("**Extracted Optimistic Claim**")
        st.markdown(
            f'<div class="claim-card">{selected_row["claim"] if selected_row["claim"] else "No optimistic claim detected."}</div>',
            unsafe_allow_html=True
        )

        detail_col_1, detail_col_2 = st.columns(2)
        with detail_col_1:
            st.markdown("**Baseline Result**")
            st.write(f"Baseline label: {selected_row['baseline_label']}")
            st.write(f"Matched keywords: {selected_row['baseline_matched_keywords'] or 'None'}")
        with detail_col_2:
            st.markdown("**Risk Score and Label**")
            badge_class = risk_color_map.get(selected_row["risk_label"], "badge-low")
            st.markdown(
                f'<span class="badge {badge_class}">{selected_row["risk_label"].upper()} RISK</span>',
                unsafe_allow_html=True
            )
            st.write(f"Risk score: {selected_row['risk_score']}")

        st.markdown("**Retrieved External Evidence**")
        retrieved_df = selected_row["retrieved_evidence"]
        if isinstance(retrieved_df, pd.DataFrame) and not retrieved_df.empty:
            for _, evidence_row in retrieved_df.head(3).iterrows():
                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <div class="mini-label">Case {evidence_row['case_id']} | Direction: {evidence_row['expected_direction']} | Similarity: {float(evidence_row['similarity']):.3f}</div>
                        <div>{evidence_row['evidence_text']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No external evidence was retrieved for this paragraph.")

        st.markdown("**Evidence Relationship**")
        rel_col_1, rel_col_2 = st.columns(2)
        with rel_col_1:
            st.write(f"Relationship: {selected_row['relationship']}")
        with rel_col_2:
            st.write(f"Evidence level: {selected_row['evidence_level']}")

        st.markdown("**Explanation**")
        st.markdown(
            f'<div class="section-card">{selected_row["explanation"].replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True
        )


def render_project_overview_page():
    st.markdown(
        """
        <div class="hero-card">
            <h1>Project Overview</h1>
            <p>Business-oriented summary of the workflow, baseline comparison, evaluation, and human review role.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    row_1_col_1, row_1_col_2 = st.columns(2)
    with row_1_col_1:
        st.markdown('<div class="overview-card">', unsafe_allow_html=True)
        st.markdown("### What I Built")
        st.write("This is a Streamlit-based GenAI workflow tool that screens M&A disclosure text at the paragraph level. It identifies optimistic claims, retrieves related external evidence cases, assigns risk labels, and generates analyst-facing explanations.")
        st.markdown("</div>", unsafe_allow_html=True)
    with row_1_col_2:
        st.markdown('<div class="overview-card">', unsafe_allow_html=True)
        st.markdown("### Target User and Business Problem")
        st.write("Target users are financial analysts, auditors, disclosure reviewers, and accounting researchers. They often review long M&A disclosures and need to quickly identify promotional or optimistic language that lacks concrete support.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="overview-card">', unsafe_allow_html=True)
    st.markdown("### Workflow")
    st.markdown(
        """
        <div class="workflow-card">
            Disclosure input → Paragraph splitting → Optimistic claim extraction → Evidence retrieval → Evidence relationship classification → Rule-based risk scoring → Analyst-facing explanation
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    row_2_col_1, row_2_col_2 = st.columns(2)
    with row_2_col_1:
        st.markdown('<div class="overview-card">', unsafe_allow_html=True)
        st.markdown("### Why GenAI / Retrieval Is Useful")
        st.write("A prompt-only chatbot can summarize text, but this tool structures the task into a workflow. The retrieval step brings in external evidence cases, so the output is grounded beyond the pasted text. The explanation is designed for analyst review rather than general chat.")
        st.markdown("</div>", unsafe_allow_html=True)
    with row_2_col_2:
        st.markdown('<div class="overview-card">', unsafe_allow_html=True)
        st.markdown("### Baseline Comparison")
        comparison_df = pd.DataFrame(
            {
                "Baseline keyword model": pd.Series([
                    "Detects optimistic keywords only",
                    "No evidence retrieval",
                    "No risk ranking",
                    "No grounded explanation",
                ]),
                "Proposed workflow": pd.Series([
                    "Extracts claims",
                    "Retrieves top evidence cases",
                    "Ranks paragraph-level risk",
                    "Explains why a paragraph needs review",
                ]),
            }
        )
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="overview-card">', unsafe_allow_html=True)
    st.markdown("### Evaluation Summary")
    manual_df = load_results("results/evaluation_results.csv")
    synthetic_df = load_results("results/generated_evaluation_results.csv")

    if manual_df is None and synthetic_df is None:
        st.info("Run python evaluation.py to generate evaluation summary metrics.")
    else:
        if manual_df is not None:
            st.markdown("**Manual evaluation**")
            cols = st.columns(4)
            metrics = [
                ("Claim detection accuracy", f"{manual_df['claim_correct'].mean():.2f}"),
                ("Evidence level agreement", f"{manual_df['evidence_correct'].mean():.2f}"),
                ("Risk label accuracy", f"{manual_df['risk_correct'].mean():.2f}"),
                ("Baseline accuracy", f"{manual_df['baseline_correct'].mean():.2f}"),
            ]
            for col, (label, value) in zip(cols, metrics):
                col.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if synthetic_df is not None:
            st.markdown("**Synthetic robustness evaluation**")
            cols = st.columns(4)
            metrics = [
                ("Claim detection accuracy", f"{synthetic_df['claim_correct'].mean():.2f}"),
                ("Evidence level agreement", f"{synthetic_df['evidence_correct'].mean():.2f}"),
                ("Risk label accuracy", f"{synthetic_df['risk_correct'].mean():.2f}"),
                ("Baseline accuracy", f"{synthetic_df['baseline_correct'].mean():.2f}"),
            ]
            for col, (label, value) in zip(cols, metrics):
                col.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.caption("The manual set is small but carefully labeled. The synthetic robustness set expands coverage across more M&A disclosure patterns.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="overview-card">', unsafe_allow_html=True)
    st.markdown("### Human Role and Limitations")
    st.write("The tool is a first-pass screener. It does not replace professional judgment, audit procedures, or investment analysis. Analysts should manually review high-risk paragraphs and verify evidence in the original filing.")
    st.markdown("</div>", unsafe_allow_html=True)


st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Screener", "Project Overview"], index=0)

if page == "Screener":
    render_screener_page()
else:
    render_project_overview_page()
