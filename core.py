import os
import re
from typing import Any
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# -----------------------------
# 1. Basic utilities
# -----------------------------

OPTIMISTIC_KEYWORDS = [
    "accelerate growth",
    "synergies",
    "synergy",
    "expected benefits",
    "strategic combination",
    "complementary capabilities",
    "growth opportunities",
    "revenue opportunities",
    "enhance shareholder value",
    "shareholder value",
    "strengthen market position",
    "strengthen competitive position",
    "unlock opportunities",
    "unlock value",
    "create value",
    "value creation",
    "improve operational efficiency",
    "operational improvements",
    "integration benefits",
    "transformational",
    "expand customer base",
    "expand into new markets",
    "improve EBITDA",
    "enhance margins",
    "cost savings",
    "cross-selling",
    "scale advantages",
    "accretive",
    "long-term growth",
    "platform for growth",
    "long-term value",
    "market position",
    "growth"
]

WEAK_STRATEGIC_PATTERNS = [
    "enhance capabilities",
    "enhance the company's capabilities",
    "strengthen platform",
    "expand presence",
    "improve positioning",
    "support long-term growth",
    "enhance data analytics capabilities",
]

OPTIMISTIC_CONTEXT_WORDS = [
    "benefit",
    "benefits",
    "opportunity",
    "opportunities",
    "expand",
    "margin",
    "margins",
    "competitive position",
    "market expansion",
    "integration",
    "accretive",
    "scale",
    "cross-sell",
    "cross selling",
    "customer base",
    "new markets",
    "platform",
    "segment"
]

CONCRETE_SUPPORT_PATTERNS = [
    r"revenue",
    r"ebitda",
    r"margin",
    r"cost savings",
    r"annual savings",
    r"customer base",
    r"distribution channels",
    r"regions?",
    r"patents?",
    r"technology",
    r"manufacturing facilities",
    r"supply chain",
    r"integration plan",
    r"facility consolidation",
    r"pro forma",
    r"segment",
    r"within\s+12\s+months",
    r"within\s+18\s+months",
    r"within\s+24\s+months"
]

GENERIC_PROMOTIONAL_PATTERNS = [
    "accelerate growth",
    "create value",
    "value creation",
    "unlock value",
    "unlock opportunities",
    "enhance shareholder value",
    "shareholder value",
    "transformational",
    "long-term growth",
    "long-term value",
    "platform for growth",
]

DESCRIPTIVE_PATTERNS = [
    "accounting treatment",
    "goodwill",
    "intangible assets",
    "purchase price",
    "paid in cash",
    "completed the acquisition",
]

PROCEDURAL_EXCLUSION_PATTERNS = [
    "form 25",
    "form 15",
    "delisting",
    "nyse",
    "exchange act",
    "sec filing",
    "rule 12d2-2",
    "option conversion",
    "rsu conversion",
    "withholding tax",
    "withholding taxes",
    "merger consideration",
    "cash election",
]

EXECUTION_SUPPORT_PATTERNS = [
    "cost savings",
    "annual savings",
    "supply chain",
    "integration plan",
    "facility consolidation",
    "manufacturing facilities",
    "distribution channels",
    "within 12 months",
    "within 18 months",
    "within 24 months",
    "ebitda",
    "margin",
    "operational efficiencies",
]

QUANTITATIVE_PATTERNS = [
    r"\$\s?\d+(\.\d+)?",
    r"\d+%",
    r"\d+\s?million",
    r"\d+\s?billion",
    r"\d+\s?thousand",
    r"\d+\s?months",
    r"\d+\s?years",
    r"\d+\s?(customers|stores|regions|markets|locations|facilities)",
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(customers|stores|regions|markets|channels|locations|facilities)\b",
    r"within\s+(12|18|24)\s+months",
    r"within\s+\d+",
    r"annual savings",
    r"annual cost savings",
    r"pro forma\s+(revenue|ebitda|margin)",
    r"(revenue|ebitda|margin)\s+(of|to|by|from|within|approximately|around)",
    r"(revenue|ebitda|margin)\s+\$?\d+",
    r"cost savings",
    r"pro forma"
]


def load_evidence_library(path="data/evidence_library.csv"):
    return pd.read_csv(path)


def load_test_cases(path="data/test_cases.csv"):
    return pd.read_csv(path)


def contains_quantitative_support(text):
    text_lower = str(text).lower()
    negative_quant_phrases = [
        "no revenue target",
        "no revenue targets",
        "no market assumptions",
        "does not provide revenue targets",
        "has not yet finalized",
        "without measurable support",
        "without quantified",
        "no measurable support"
    ]

    for phrase in negative_quant_phrases:
        if phrase in text_lower:
            return False

    for pattern in QUANTITATIVE_PATTERNS:
        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            return True
    return False


def has_concrete_business_support(text):
    text_lower = _clean_text(text).lower()

    negative_concrete_phrases = [
        "has not yet finalized an integration plan",
        "has not finalized an integration plan",
        "without an integration plan",
        "without quantified support",
        "without measurable support",
        "does not provide revenue targets",
        "no revenue target",
        "no revenue targets",
        "multiple regions",
    ]

    for phrase in negative_concrete_phrases:
        if phrase in text_lower:
            return False

    for pattern in CONCRETE_SUPPORT_PATTERNS:
        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            return True

    return False


def is_purely_descriptive(paragraph):
    text_lower = _clean_text(paragraph).lower()
    return any(pattern in text_lower for pattern in DESCRIPTIVE_PATTERNS)


def is_procedural_exclusion(paragraph):
    text_lower = _clean_text(paragraph).lower()
    return any(pattern in text_lower for pattern in PROCEDURAL_EXCLUSION_PATTERNS)


def has_weak_strategic_optimism(text):
    text_lower = _clean_text(text).lower()
    if any(pattern in text_lower for pattern in WEAK_STRATEGIC_PATTERNS):
        return True
    return bool(
        re.search(r"enhance .*capabilities", text_lower)
        or re.search(r"strengthen .*platform", text_lower)
        or re.search(r"improve .*positioning", text_lower)
        or re.search(r"expand .*presence", text_lower)
    )


def has_execution_support(text):
    text_lower = _clean_text(text).lower()
    return any(pattern in text_lower for pattern in EXECUTION_SUPPORT_PATTERNS)


def clean_disclosure_text(text):
    raw_text = _clean_text(text)
    if raw_text.strip() == "":
        return ""

    normalized = raw_text[:200000].replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u00a0", " ")
    normalized = re.sub(r"[ \t]+", " ", normalized)

    cleaned_lines = []
    for line in normalized.split("\n"):
        compact_line = re.sub(r"\s+", " ", line).strip()

        if compact_line == "":
            cleaned_lines.append("")
            continue

        if re.fullmatch(r"(page\s+)?\d{1,4}(\s+of\s+\d{1,4})?", compact_line.lower()):
            continue

        if re.fullmatch(r"(table of contents|united states|securities and exchange commission|form 8-k)", compact_line.lower()):
            continue

        if re.fullmatch(r"[A-Z0-9 \-]{1,18}", compact_line) and len(compact_line.split()) <= 3:
            continue

        if re.fullmatch(r"[A-Za-z]{1,3}", compact_line):
            continue

        cleaned_lines.append(compact_line)

    cleaned_text = "\n".join(cleaned_lines)
    cleaned_text = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned_text)

    paragraphs = []
    current_lines = []
    for line in cleaned_text.split("\n"):
        if line == "":
            if current_lines:
                paragraphs.append(" ".join(current_lines).strip())
                current_lines = []
            continue

        if current_lines and len(line.split()) <= 4 and not line.endswith((".", ":", ";")):
            current_lines.append(line)
            continue

        current_lines.append(line)

    if current_lines:
        paragraphs.append(" ".join(current_lines).strip())

    return "\n\n".join(paragraphs).strip()


def clean_claim(sentence):
    claim_text = _clean_text(sentence).strip()
    if claim_text == "":
        return ""

    claim_text = re.sub(r"^(the company|management|we)\s+(believes|believe|expects|expect|anticipates|anticipate)\s+(that\s+)?", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"^(the transaction|the acquisition|the deal)\s+is\s+expected\s+to\s+", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"^(the acquired business)\s+is\s+expected\s+to\s+", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"^the acquired business contributed .*?\s+and\s+is\s+expected\s+to\s+", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"^achieving\s+", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bthe company'?s presence in the ([a-zA-Z0-9&/\- ]+?) market\b", "market presence", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bthe company'?s presence\b", "market presence", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bacross (its|the) existing customer base\b", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bthe company'?s data analytics capabilities\b", "data analytics capabilities", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bthe company'?s\b", "", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bexisting customer base\b", "customer base", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\bapproximately achieving\b", "achieving approximately", claim_text, flags=re.IGNORECASE)
    claim_text = re.sub(r"\s+,", ",", claim_text)
    claim_text = re.sub(r",\s*,", ", ", claim_text)
    claim_text = re.sub(r"\s{2,}", " ", claim_text)
    claim_text = re.sub(r"\s+", " ", claim_text).strip(" .;:")

    if claim_text == "":
        return ""

    lower_claim = claim_text.lower()
    if not any(keyword in lower_claim for keyword in [
        "growth", "synerg", "cost savings", "market", "customer", "operational",
        "ebitda", "revenue", "margin", "technology", "cross-selling",
        "shareholder value", "accretive", "capabilities", "platform", "positioning"
    ]):
        return ""

    if claim_text.lower().startswith("management expects"):
        return claim_text[0].upper() + claim_text[1:]

    return f"Management expects {claim_text}"


# -----------------------------
# 2. Baseline model
# -----------------------------

def keyword_baseline(paragraph):
    """
    Simple baseline:
    Detect whether a paragraph sounds optimistic based only on keywords.
    This baseline does NOT use retrieval, external evidence, or risk scoring.
    """
    text = _clean_text(paragraph).lower()
    matched_keywords = []

    for kw in OPTIMISTIC_KEYWORDS:
        if kw.lower() in text:
            matched_keywords.append(kw)

    has_claim = len(matched_keywords) > 0

    if has_claim:
        baseline_label = "optimistic"
    else:
        baseline_label = "not optimistic"

    return {
        "baseline_label": baseline_label,
        "matched_keywords": matched_keywords
    }


# -----------------------------
# 3. Claim extraction
# -----------------------------

def extract_claim_rule_based(paragraph):
    """
    Beginner-friendly rule-based claim extraction.
    This works even without OpenAI API.
    Later you can replace this with an LLM call.
    """
    paragraph = _clean_text(paragraph).strip()

    if paragraph == "":
        return {
            "has_optimistic_claim": "no",
            "claim": "",
            "retrieval_claim": ""
        }

    if is_procedural_exclusion(paragraph):
        return {
            "has_optimistic_claim": "no",
            "claim": "",
            "retrieval_claim": ""
        }

    sentences = re.split(r"(?<=[.!?])\s+", paragraph)

    candidate_sentences = []
    paragraph_lower = paragraph.lower()
    matched_keywords = [kw for kw in OPTIMISTIC_KEYWORDS if kw.lower() in paragraph_lower]
    has_context_match = any(word in paragraph_lower for word in OPTIMISTIC_CONTEXT_WORDS)
    has_concrete_support = has_concrete_business_support(paragraph)
    has_weak_strategic_signal = has_weak_strategic_optimism(paragraph)
    has_positive_signal = bool(matched_keywords) or (
        has_context_match and any(
            cue in paragraph_lower
            for cue in ["expect", "expected", "believe", "will", "anticipate", "opportunity", "benefit", "expand"]
        )
    )
    has_positive_signal = has_positive_signal or (
        has_concrete_support and any(
            cue in paragraph_lower
            for cue in ["expected", "expects", "will", "expand", "improve", "generate", "add", "integrated"]
        )
    )
    has_positive_signal = has_positive_signal or has_weak_strategic_signal

    for sentence in sentences:
        sentence_lower = sentence.lower()
        for kw in OPTIMISTIC_KEYWORDS:
            if kw.lower() in sentence_lower:
                candidate_sentences.append(sentence)
                break
        else:
            if any(word in sentence_lower for word in OPTIMISTIC_CONTEXT_WORDS) and any(
                cue in sentence_lower
                for cue in ["expect", "expected", "believe", "will", "anticipate", "opportunity", "benefit", "expand"]
            ):
                candidate_sentences.append(sentence)
            elif has_concrete_business_support(sentence) and any(
                cue in sentence_lower
                for cue in ["expected", "expects", "will", "expand", "improve", "generate", "add", "integrated"]
            ):
                candidate_sentences.append(sentence)
            elif has_weak_strategic_optimism(sentence) and any(
                cue in sentence_lower
                for cue in ["expected", "expects", "will", "anticipate", "support", "enhance", "strengthen"]
            ):
                candidate_sentences.append(sentence)

    if len(candidate_sentences) == 0 and has_positive_signal:
        cleaned_claim = clean_claim(paragraph)
        return {
            "has_optimistic_claim": "yes",
            "claim": cleaned_claim if cleaned_claim else paragraph,
            "retrieval_claim": paragraph
        }

    if len(candidate_sentences) == 0:
        return {
            "has_optimistic_claim": "no",
            "claim": "",
            "retrieval_claim": ""
        }

    cleaned_sentences = []
    for sentence in candidate_sentences:
        cleaned_sentence = clean_claim(sentence)
        if cleaned_sentence:
            cleaned_sentences.append(cleaned_sentence)

    if cleaned_sentences:
        unique_cleaned_sentences = list(dict.fromkeys(cleaned_sentences))
        claim = " ".join(unique_cleaned_sentences)
    else:
        claim = clean_claim(candidate_sentences[0]) if candidate_sentences else ""

    return {
        "has_optimistic_claim": "yes",
        "claim": claim,
        "retrieval_claim": " ".join(candidate_sentences)
    }


# -----------------------------
# 4. Embedding retrieval
# -----------------------------

def get_openai_client():
    """
    Create OpenAI client if API key exists.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if OpenAI is None:
        return None

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def get_embedding_openai(text, model="text-embedding-3-small"):
    """
    Get embedding from OpenAI.
    """
    client = get_openai_client()

    if client is None:
        return None

    response = client.embeddings.create(
        model=model,
        input=text
    )

    return response.data[0].embedding


def _clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def retrieve_evidence(claim, evidence_df, top_k=3):
    """
    Retrieval step.

    If OpenAI API key is available:
        use OpenAI embeddings.
    If not:
        use TF-IDF fallback.
    """
    claim = _clean_text(claim)

    if claim.strip() == "":
        return pd.DataFrame()

    client = get_openai_client()

    # Option A: OpenAI embedding
    if client is not None:
        claim_embedding = get_embedding_openai(claim)

        if claim_embedding is not None:
            valid_rows = []
            evidence_embeddings = []

            for idx, text in evidence_df["evidence_text"].items():
                emb = get_embedding_openai(_clean_text(text))
                if emb is None:
                    continue
                valid_rows.append(idx)
                evidence_embeddings.append(emb)

            if evidence_embeddings:
                similarities = cosine_similarity(
                    np.array(claim_embedding).reshape(1, -1),
                    np.array(evidence_embeddings)
                )[0]

                ranked_df = evidence_df.loc[valid_rows].copy()
                ranked_df["similarity"] = similarities

                return ranked_df.sort_values("similarity", ascending=False).head(top_k)

    # Option B: fallback TF-IDF
    from sklearn.feature_extraction.text import TfidfVectorizer

    evidence_texts = evidence_df["evidence_text"].fillna("").astype(str).tolist()
    texts = [claim] + evidence_texts

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(texts)

    claim_vector = tfidf_matrix[0]
    evidence_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(claim_vector, evidence_vectors)[0]

    evidence_df = evidence_df.copy()
    evidence_df["similarity"] = similarities

    return evidence_df.sort_values("similarity", ascending=False).head(top_k)


# -----------------------------
# 5. Evidence relationship
# -----------------------------

def classify_evidence_relationship(retrieved_df):
    """
    Simple rule-based relationship classification.
    This makes the project stable and easy to evaluate.
    """
    if retrieved_df.empty:
        return "none"

    directions = retrieved_df["expected_direction"].fillna("").astype(str).tolist()

    if "contradict" in directions:
        return "contradict"

    support_count = directions.count("support")
    weak_count = directions.count("weak")

    if support_count >= 2:
        return "support"

    if weak_count >= 2:
        return "weak"

    return "weakly related"


# -----------------------------
# 6. Evidence level
# -----------------------------

def infer_evidence_level(paragraph, claim, relationship):
    """
    Estimate evidence level using:
    - quantitative support in paragraph
    - retrieved evidence relationship
    """
    has_quant = contains_quantitative_support(paragraph)
    has_concrete_support = has_concrete_business_support(paragraph)
    has_execution_evidence = has_execution_support(paragraph)
    has_weak_strategic_signal = has_weak_strategic_optimism(paragraph)
    paragraph_lower = _clean_text(paragraph).lower()
    has_generic_promo = any(pattern in paragraph_lower for pattern in GENERIC_PROMOTIONAL_PATTERNS)

    if claim.strip() == "":
        return "none"

    if is_purely_descriptive(paragraph) or is_procedural_exclusion(paragraph):
        return "none"

    if relationship == "contradict":
        return "weak"

    if has_weak_strategic_signal and not has_execution_evidence:
        return "weak"

    if has_quant and has_concrete_support:
        return "strong"

    if has_quant and relationship == "support":
        return "strong"

    if has_quant and relationship == "weakly related":
        return "strong"

    if has_concrete_support and not has_quant:
        return "strong"

    if relationship == "support" and not has_generic_promo:
        return "strong" if has_concrete_support else "weak"

    if relationship == "weak" and has_concrete_support:
        return "strong"

    if relationship == "none":
        return "none" if not has_concrete_support and not has_quant else "weak"

    if has_generic_promo and not has_quant and not has_concrete_support:
        return "weak"

    if has_quant:
        return "strong" if has_concrete_support else "weak"

    return "weak"


# -----------------------------
# 7. Risk scoring
# -----------------------------

def calculate_risk_score(paragraph, claim, evidence_level, relationship):
    """
    Rule-based scoring:
    Higher score = higher review risk.
    """
    has_claim = claim.strip() != ""
    has_quant = contains_quantitative_support(paragraph)
    has_concrete_support = has_concrete_business_support(paragraph)
    has_execution_evidence = has_execution_support(paragraph)
    has_weak_strategic_signal = has_weak_strategic_optimism(paragraph)
    score = 1
    reasons = []

    if not has_claim:
        return {
            "risk_score": 1,
            "risk_label": "low",
            "risk_reasons": [
                "No optimistic claim was detected, so the paragraph is low risk."
            ]
        }

    reasons.append("The paragraph contains an optimistic claim.")

    if relationship == "contradict":
        return {
            "risk_score": 5,
            "risk_label": "high",
            "risk_reasons": reasons + [
                "Retrieved evidence may contradict the claim."
            ]
        }

    if not has_quant:
        reasons.append("The paragraph lacks quantitative support.")
    else:
        reasons.append("The paragraph includes quantitative support.")

    if has_weak_strategic_signal and not has_execution_evidence:
        score = 3 if has_quant or has_concrete_support else 2
        reasons.append("The paragraph makes a mild strategic enhancement claim with limited measurable support.")
    elif evidence_level == "strong" and has_quant:
        score = 1
        reasons.append("The paragraph includes strong evidence support.")
    elif evidence_level == "strong" and not has_quant:
        score = 3
        reasons.append("The paragraph has concrete business support but limited quantification.")
    elif evidence_level == "weak" and has_concrete_support:
        score = 3
        reasons.append("The paragraph has some concrete business support, but the evidence remains weak.")
    else:
        score = 5
        reasons.append("The paragraph relies on weak support without clear quantitative grounding.")

    if relationship == "support":
        reasons.append("Retrieved evidence supports the claim.")
    elif relationship == "weakly related":
        reasons.append("Retrieved evidence is only weakly related.")
    elif relationship == "weak":
        reasons.append("Retrieved evidence suggests weak support.")
    else:
        reasons.append("No clear supporting evidence was identified.")

    if score >= 5:
        risk_label = "high"
    elif score >= 3:
        risk_label = "medium"
    else:
        risk_label = "low"

    return {
        "risk_score": score,
        "risk_label": risk_label,
        "risk_reasons": reasons
    }


# -----------------------------
# 8. Explanation generation
# -----------------------------

def generate_explanation(paragraph, claim, retrieved_df, relationship, evidence_level, risk_result):
    """
    Generate explanation.
    Uses a stable template by default.
    If OpenAI key exists, you can later replace this with LLM.
    """
    if claim.strip() == "":
        return (
            "Screening conclusion:\n"
            "This paragraph appears low risk because no clear optimistic commitment was detected.\n\n"
            "Why flagged:\n"
            "- The paragraph reads as descriptive or accounting-focused rather than promotional.\n\n"
            "Evidence considered:\n"
            "- No optimistic claim was extracted for retrieval-based review.\n\n"
            "Suggested analyst follow-up:\n"
            "Confirm whether related sections elsewhere in the filing contain forward-looking deal claims."
        )

    evidence_snippets = []
    for _, row in retrieved_df.head(2).iterrows():
        evidence_snippets.append(f"- {_clean_text(row.get('evidence_text'))}")

    if not evidence_snippets:
        evidence_snippets.append("- No closely related external evidence was retrieved.")

    paragraph_lower = _clean_text(paragraph).lower()
    focus_areas = []
    for term, label in [
        ("revenue", "revenue growth"),
        ("cost savings", "cost savings"),
        ("market", "market expansion"),
        ("customer", "customer expansion"),
        ("cross-selling", "cross-selling"),
        ("technology", "technology capabilities"),
        ("ebitda", "EBITDA improvement"),
        ("margin", "margin improvement"),
    ]:
        if term in paragraph_lower and label not in focus_areas:
            focus_areas.append(label)

    if not focus_areas:
        focus_areas.append("optimistic acquisition benefits")

    follow_up = (
        "Review whether management provides measurable assumptions, integration plans, or post-merger performance indicators elsewhere in the filing."
    )
    if relationship == "contradict":
        follow_up = (
            "Review whether management addresses integration risks, contradictory assumptions, or offsetting costs elsewhere in the filing."
        )
    elif evidence_level == "strong" and risk_result["risk_label"] != "high":
        follow_up = (
            "Confirm that the cited metrics, timelines, and operational assumptions are supported consistently across the filing."
        )

    why_flagged = [
        f"- The paragraph includes optimistic language about {', '.join(focus_areas)}.",
    ]
    if evidence_level == "strong":
        why_flagged.append("- It includes concrete support that reduces screening risk but still merits validation.")
    elif relationship == "contradict":
        why_flagged.append("- Retrieved evidence suggests the claim may understate execution or integration risk.")
    else:
        why_flagged.append("- It provides limited measurable support relative to the strength of the commitment.")

    conclusion_map = {
        "high": "This paragraph is high risk because it makes an optimistic commitment with limited or conflicting support.",
        "medium": "This paragraph is medium risk because it includes an optimistic claim with some support but still leaves validation gaps.",
        "low": "This paragraph is low risk because the claim is supported by more concrete evidence and measurable context.",
    }

    return (
        "Screening conclusion:\n"
        f"{conclusion_map.get(risk_result['risk_label'], 'This paragraph requires review.')}\n\n"
        "Why flagged:\n"
        f"{chr(10).join(why_flagged)}\n\n"
        "Evidence considered:\n"
        f"{chr(10).join(evidence_snippets)}\n\n"
        "Suggested analyst follow-up:\n"
        f"{follow_up}"
    ).strip()


# -----------------------------
# 9. Full pipeline
# -----------------------------

def analyze_paragraph(paragraph, evidence_path="data/evidence_library.csv"):
    evidence_df = load_evidence_library(evidence_path)

    baseline = keyword_baseline(paragraph)

    claim_result = extract_claim_rule_based(paragraph)
    claim = claim_result["claim"]
    retrieval_claim = claim_result["retrieval_claim"]

    retrieved_df = retrieve_evidence(retrieval_claim, evidence_df, top_k=3)

    relationship = classify_evidence_relationship(retrieved_df)

    evidence_level = infer_evidence_level(
        paragraph=paragraph,
        claim=claim,
        relationship=relationship
    )

    risk_result = calculate_risk_score(
        paragraph=paragraph,
        claim=claim,
        evidence_level=evidence_level,
        relationship=relationship
    )

    explanation = generate_explanation(
        paragraph=paragraph,
        claim=claim,
        retrieved_df=retrieved_df,
        relationship=relationship,
        evidence_level=evidence_level,
        risk_result=risk_result
    )

    return {
        "paragraph": paragraph,
        "baseline": baseline,
        "has_optimistic_claim": claim_result["has_optimistic_claim"],
        "claim": claim,
        "retrieved_evidence": retrieved_df,
        "relationship": relationship,
        "evidence_level": evidence_level,
        "risk_score": risk_result["risk_score"],
        "risk_label": risk_result["risk_label"],
        "risk_reasons": risk_result["risk_reasons"],
        "explanation": explanation
    }


def split_disclosure_into_paragraphs(text):
    cleaned_text = clean_disclosure_text(text)

    if cleaned_text == "":
        return []

    raw_paragraphs = re.split(r"\n\s*\n+", cleaned_text)
    paragraphs = []

    for paragraph in raw_paragraphs:
        normalized = paragraph.strip()
        if normalized == "":
            continue
        paragraphs.append({
            "paragraph_id": f"P{len(paragraphs) + 1:03d}",
            "paragraph": normalized
        })

    return paragraphs


def analyze_disclosure(text, evidence_path="data/evidence_library.csv"):
    paragraph_rows = split_disclosure_into_paragraphs(text)
    analysis_rows = []

    for row in paragraph_rows:
        result = analyze_paragraph(row["paragraph"], evidence_path=evidence_path)
        retrieved_df = result["retrieved_evidence"].reset_index(drop=True)
        top_evidence = [
            _clean_text(retrieved_df.iloc[i]["evidence_text"]) if i < len(retrieved_df) else ""
            for i in range(3)
        ]

        analysis_rows.append({
            "paragraph_id": row["paragraph_id"],
            "paragraph": row["paragraph"],
            "has_optimistic_claim": result["has_optimistic_claim"],
            "claim": result["claim"],
            "evidence_level": result["evidence_level"],
            "relationship": result["relationship"],
            "risk_score": result["risk_score"],
            "risk_label": result["risk_label"],
            "baseline_label": result["baseline"]["baseline_label"],
            "top_evidence_1": top_evidence[0],
            "top_evidence_2": top_evidence[1],
            "top_evidence_3": top_evidence[2],
            "explanation": result["explanation"],
            "retrieved_evidence": result["retrieved_evidence"],
            "baseline_matched_keywords": ", ".join(result["baseline"]["matched_keywords"])
        })

    return pd.DataFrame(analysis_rows)
