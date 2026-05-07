import os
import pandas as pd


def build_rows():
    rows = []
    case_number = 1

    generic_synergy_claims = [
        "Management expects the transaction to unlock value and create meaningful synergies across the combined business.",
        "The strategic combination is expected to strengthen positioning and support long-term growth opportunities.",
        "The acquisition should enhance shareholder value through broad strategic benefits and scale advantages.",
        "Executives believe the deal will create a platform for growth, although no supporting metrics were disclosed.",
        "The company expects significant benefits from the combination but did not provide measurable assumptions.",
    ]

    cost_savings_claims = [
        "The transaction is expected to deliver $35 million of annual cost savings within 18 months through procurement integration.",
        "Management expects approximately $60 million in savings within 24 months from supply chain consolidation.",
        "The deal is projected to generate $20 million in annual savings within 12 months through facility consolidation.",
        "The company expects $45 million of cost synergies over 24 months supported by shared services integration.",
        "Executives forecast annual savings of $28 million within 18 months from combining distribution networks.",
    ]

    market_expansion_claims = [
        ("The acquisition is expected to expand the company into new healthcare regions in the Midwest and Southeast.", "strong", "medium"),
        ("Management believes the transaction opens growth opportunities in adjacent markets, although no regional plan was provided.", "weak", "high"),
        ("The combination adds distribution channels in three western regions and broadens the customer base.", "strong", "medium"),
        ("The deal should support market expansion over time, but management did not identify specific customer groups.", "weak", "high"),
        ("The target adds a presence in two European regions and extends the buyer's sales network.", "strong", "medium"),
    ]

    operational_efficiency_claims = [
        ("Management plans to consolidate two manufacturing facilities and integrate procurement teams to improve operational efficiency.", "strong", "medium"),
        ("The company expects operational improvements from the acquisition but has not finalized the integration plan.", "weak", "high"),
        ("Executives anticipate efficiency gains from aligning warehouse operations and combining support functions.", "strong", "medium"),
        ("The filing states that the acquisition should improve operations, although no implementation steps were described.", "weak", "high"),
        ("The buyer expects better operating margins by merging logistics processes over the next 18 months.", "strong", "low"),
    ]

    revenue_contribution_claims = [
        "The acquired business contributed $140 million of revenue last year and is expected to expand the enterprise software segment.",
        "Management said the target adds $85 million in annual revenue and supports expansion in the diagnostics segment.",
        "The company expects the target's $110 million revenue base to strengthen its industrial automation segment.",
        "The target contributed $95 million in revenue and gives the acquirer a larger customer base in specialty retail.",
        "Executives highlighted $70 million of revenue contribution from the acquired platform and expected cross-selling opportunities.",
    ]

    technology_claims = [
        ("The acquisition adds patented imaging technology that will be integrated into the company's analytics platform.", "strong", "medium"),
        ("Management expects the patented automation tools to improve product capabilities, but no financial targets were disclosed.", "strong", "medium"),
        ("The target brings proprietary software and a portfolio of patents that support the buyer's existing platform.", "strong", "medium"),
        ("Executives described the acquired technology as transformational without identifying measurable commercial impact.", "weak", "high"),
        ("The company said the transaction adds technology capabilities that may support future innovation across product lines.", "weak", "medium"),
    ]

    accounting_only_paragraphs = [
        "The filing describes preliminary purchase accounting adjustments related to goodwill and intangible assets.",
        "Management disclosed the accounting treatment for acquired inventory, goodwill, and deferred tax balances.",
        "The company reported the allocation of purchase price to identifiable intangible assets and goodwill.",
        "The note explains fair value estimates used in the preliminary acquisition accounting entries.",
        "The disclosure summarizes the recognition of goodwill and customer relationship intangibles from the transaction.",
    ]

    purchase_price_paragraphs = [
        "The aggregate purchase price was $420 million, subject to working capital and net debt adjustments.",
        "The company paid $275 million in cash at closing for the acquired business.",
        "The acquisition price included $190 million upfront and a contingent payment tied to post-close milestones.",
        "The transaction consideration was approximately $510 million, funded through cash on hand and borrowings.",
        "The buyer agreed to a purchase price of $330 million for the target's equity interests.",
    ]

    integration_risk_paragraphs = [
        ("Management expects the combination to create benefits, but integration costs may be material in the first year.", "weak", "high"),
        ("The company believes the deal will support growth, although executives noted execution risk and restructuring charges.", "weak", "high"),
        ("The filing states that synergy realization depends on successful integration and may be offset by transition costs.", "weak", "high"),
        ("Management expects operational benefits but warned that systems integration could delay planned improvements.", "weak", "high"),
        ("Executives said the transaction could create value, while acknowledging integration risks and duplicated costs.", "weak", "high"),
    ]

    accretive_claims = [
        ("The transaction is expected to be accretive, although management did not provide timing assumptions.", "weak", "high"),
        ("Executives expect the acquisition to be accretive to earnings within 24 months.", "strong", "low"),
        ("The buyer said the deal should be modestly accretive over time, but no pro forma metrics were disclosed.", "weak", "medium"),
        ("Management expects the transaction to be accretive and cited pro forma margin expansion within 18 months.", "strong", "low"),
        ("The company described the acquisition as accretive without explaining the expected realization period.", "weak", "high"),
    ]

    shareholder_value_claims = [
        "The acquisition is expected to enhance shareholder value and create strategic benefits for the combined company.",
        "Management believes the transaction will drive long-term value creation for shareholders, although it provided no measurable targets.",
        "Executives said the combination should improve shareholder value through better positioning in core markets.",
        "The buyer expects the deal to create value for shareholders over time but did not quantify expected benefits.",
        "The company described the acquisition as a compelling value creation opportunity for shareholders.",
    ]

    vague_strategic_claims = [
        "Management described the transaction as a highly complementary strategic combination for future growth.",
        "Executives said the deal fits the company's strategy and offers compelling long-term opportunities.",
        "The filing states that the combination strengthens the business strategically, without describing specific operating benefits.",
        "The company said the acquisition broadens its strategic platform and should support future opportunity creation.",
        "Management expects strategic benefits from the combination, but the disclosure remains high level.",
    ]

    def add_row(paragraph, has_claim, evidence_level, risk, dataset_type):
        nonlocal case_number
        rows.append({
            "case_id": f"G{case_number:03d}",
            "paragraph": paragraph,
            "has_optimistic_claim": has_claim,
            "expected_evidence_level": evidence_level,
            "expected_risk": risk,
            "dataset_type": dataset_type,
        })
        case_number += 1

    for paragraph in generic_synergy_claims:
        add_row(paragraph, "yes", "weak", "high", "generic_synergy")

    for paragraph in cost_savings_claims:
        add_row(paragraph, "yes", "strong", "low", "cost_savings")

    for paragraph, evidence_level, risk in market_expansion_claims:
        add_row(paragraph, "yes", evidence_level, risk, "market_expansion")

    for paragraph, evidence_level, risk in operational_efficiency_claims:
        add_row(paragraph, "yes", evidence_level, risk, "operational_efficiency")

    for paragraph in revenue_contribution_claims:
        add_row(paragraph, "yes", "strong", "low", "revenue_contribution")

    for paragraph, evidence_level, risk in technology_claims:
        add_row(paragraph, "yes", evidence_level, risk, "technology_patent")

    for paragraph in accounting_only_paragraphs:
        add_row(paragraph, "no", "none", "low", "accounting_only")

    for paragraph in purchase_price_paragraphs:
        add_row(paragraph, "no", "none", "low", "purchase_price_only")

    for paragraph, evidence_level, risk in integration_risk_paragraphs:
        add_row(paragraph, "yes", evidence_level, risk, "integration_risk")

    for paragraph, evidence_level, risk in accretive_claims:
        add_row(paragraph, "yes", evidence_level, risk, "accretive")

    for paragraph in shareholder_value_claims:
        add_row(paragraph, "yes", "weak", "high", "shareholder_value")

    for paragraph in vague_strategic_claims:
        add_row(paragraph, "yes", "weak", "high", "vague_strategic")

    return rows


def main():
    rows = build_rows()
    df = pd.DataFrame(rows)
    os.makedirs("data", exist_ok=True)
    output_path = "data/generated_test_cases.csv"
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic test cases")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
