# Evidence-Grounded M&A Disclosure Risk Screener

## Overview

This project is a Streamlit-based GenAI workflow tool for screening M&A disclosure text at the paragraph level. It is designed as a first-pass review aid for disclosure analysis: the user can paste or upload M&A disclosure text, and the system will identify optimistic claims, retrieve related evidence cases, assign risk scores, rank paragraphs by review priority, and generate analyst-facing explanations.

The project is intentionally narrow in scope. It does not attempt full sentiment analysis or general SEC filing summarization. Instead, it focuses on a specific business problem: optimistic M&A disclosure language that may sound persuasive but may lack concrete support.

## 1. Context, User, and Problem

### Business Context

M&A disclosures often include forward-looking language about:

- synergies
- revenue growth
- market expansion
- operational efficiency
- margin improvement
- shareholder value

These claims may be reasonable, but they may also be promotional, generic, or insufficiently supported by measurable evidence. In practice, reviewers often need to read long filings and decide which paragraphs deserve deeper scrutiny.

### Target User

This tool is designed for:

- financial analysts
- auditors
- disclosure reviewers
- accounting researchers

### Problem

Users need a first-pass screening tool that can help them quickly find paragraphs containing optimistic M&A claims and distinguish between:

- claims with stronger concrete support
- claims with weaker or more generic support
- purely procedural or accounting language that should not be flagged

The goal is not to automate final judgment. The goal is to reduce review burden by surfacing paragraphs that may need manual follow-up.

## 2. Solution and Design

### What the App Does

The Streamlit app accepts:

- pasted M&A disclosure text
- uploaded `.txt` files
- uploaded `.html` SEC-style filings

It then:

1. cleans the input text
2. splits the disclosure into paragraphs
3. detects optimistic claims
4. retrieves related evidence cases from the evidence library
5. classifies the evidence relationship
6. assigns a rule-based risk label and risk score
7. ranks paragraphs by review priority
8. generates an analyst-facing explanation

### Supported Inputs

- pasted disclosure text
- `.txt` files
- `.html` files

### Current Input Limitations

- full PDF support is not currently implemented
- the prototype works best on M&A-related sections rather than entire long filings

### Workflow

The workflow is:

1. Disclosure input
2. Text cleaning
3. Paragraph splitting
4. Optimistic claim extraction
5. External evidence retrieval from `data/evidence_library.csv`
6. Evidence relationship classification
7. Rule-based risk scoring
8. Explanation generation
9. Paragraph-level ranked output

### Why This Is Not Just ChatGPT

A prompt-only chatbot can comment on pasted text, but this tool uses a structured workflow. It adds:

- paragraph-level screening
- a keyword-only baseline for comparison
- external evidence retrieval
- evidence relationship classification
- rule-based risk scoring
- ranked paragraph output
- analyst-facing explanations

Most importantly, the retrieval step grounds the output in an evidence library rather than relying only on the pasted paragraph.

### Baseline vs Proposed System

| Component | Baseline Keyword Model | Proposed Evidence-Grounded Workflow |
|---|---|---|
| Claim detection | Detects optimistic keywords only | Extracts optimistic claims |
| Evidence use | No external evidence | Retrieves top related evidence cases |
| Paragraph ranking | No | Yes |
| Risk scoring | No | Yes |
| Explanation | No grounded explanation | Generates analyst-facing explanation |

## 3. Evaluation and Results

The project uses two evaluation sets.

### Manual Evaluation Set

- File: `data/test_cases.csv`
- Purpose: carefully labeled benchmark examples
- Role: checks paragraph-level behavior on hand-reviewed cases

### Synthetic Robustness Set

- File: `data/generated_test_cases.csv`
- Purpose: larger generated set covering broader M&A disclosure patterns
- Role: checks whether the workflow behaves consistently across more edge cases and realistic variants

### Current Results

#### Manual Evaluation Set

| Metric | Result |
|---|---:|
| Claim detection accuracy | 0.95 |
| Evidence level agreement | 0.90 |
| Risk label accuracy | 0.80 |
| Baseline optimistic detection accuracy | 0.60 |
| Proposed system risk accuracy | 0.80 |

#### Synthetic Robustness Set

| Metric | Result |
|---|---:|
| Claim detection accuracy | 0.88 |
| Evidence level agreement | 0.78 |
| Risk label accuracy | 0.83 |
| Baseline optimistic detection accuracy | 0.58 |
| Proposed system risk accuracy | 0.83 |

### Interpretation

These results suggest that the proposed workflow outperforms the keyword-only baseline because it does more than detect optimistic words. It adds:

- claim extraction
- retrieval-grounded evidence review
- evidence relationship classification
- structured risk scoring

The evaluation is still prototype-scale, so these numbers should be interpreted as evidence of useful workflow behavior rather than production readiness.

### Human Role

This tool is a first-pass screener. It does not replace:

- analyst judgment
- audit procedures
- investment analysis

Users should manually review flagged high-risk paragraphs and verify claims in the original filing.

## 4. Artifact Snapshot

This section can be updated with screenshots before final submission.

### Screenshot Placeholders

- Screenshot 1: Main screener interface
- Screenshot 2: Ranked paragraph risk table
- Screenshot 3: Paragraph detail with retrieved evidence

### Sample Input

```text
On April 15, 2024, Company A completed the acquisition of Company B for a total purchase price of $480 million, subject to customary working capital adjustments.

Management expects the acquisition to accelerate revenue growth, expand the company’s presence in the healthcare analytics market, and create cross-selling opportunities across its existing customer base.

The company anticipates achieving approximately $35 million in annual cost savings within 24 months through supply chain integration and operational efficiencies.

The acquired business contributed $120 million in revenue in the prior fiscal year and is expected to enhance the company’s data analytics capabilities.

The transaction will be accounted for as a business combination under applicable accounting standards, and goodwill is expected to be recognized.
```

### Sample Output Summary

- Paragraphs analyzed: 5
- Optimistic paragraphs detected
- High-risk paragraphs flagged if claims lack concrete support
- Retrieved evidence shown for each flagged paragraph
- CSV results can be downloaded

## 5. Setup and Usage Instructions

### Clone the Repository

```bash
git clone <your-repo-url>
cd evidence-grounded-ma-risk-tool
```

### Create and Activate a Virtual Environment

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Generate Synthetic Test Cases

```bash
python generate_synthetic_tests.py
```

### Run Evaluation

```bash
python evaluation.py
```

### Run the App

```bash
streamlit run app.py
```

## Repository Structure

| Path | Purpose |
|---|---|
| `app.py` | Streamlit app interface |
| `core.py` | Core screening logic, text cleaning, claim extraction, retrieval, risk scoring, explanation |
| `evaluation.py` | Runs evaluation on manual and synthetic sets |
| `generate_synthetic_tests.py` | Generates synthetic robustness evaluation data |
| `requirements.txt` | Project dependencies |
| `data/evidence_library.csv` | Evidence library used for retrieval |
| `data/test_cases.csv` | Manual evaluation set |
| `data/generated_test_cases.csv` | Synthetic robustness evaluation set |
| `results/evaluation_results.csv` | Manual evaluation results |
| `results/generated_evaluation_results.csv` | Synthetic robustness evaluation results |

## Limitations

- The evidence library is small.
- The evidence cases are synthetic rather than drawn from a large real labeled corpus.
- This is a prototype, not a production disclosure review platform.
- It is not audit advice or investment advice.
- The tool works best on M&A-related disclosure sections rather than entire long filings.
- PDF support is limited and remains future work.

## Future Improvements

- Build a larger SEC 8-K evidence library
- Improve HTML and PDF parsing
- Add LLM-based claim extraction
- Expand expert-labeled evaluation data
- Incorporate post-merger outcome data for stronger evidence grounding

## Final Note

This project is best understood as a workflow artifact rather than just a chatbot wrapper. Its value comes from structuring the task into paragraph screening, retrieval, risk scoring, and explanation so that users can review optimistic M&A claims more systematically.
