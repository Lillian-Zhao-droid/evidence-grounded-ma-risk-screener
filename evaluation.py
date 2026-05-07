import os
from pathlib import Path

import pandas as pd

from core import analyze_paragraph, load_test_cases


def normalize_label(x):
    return str(x).strip().lower()


def evaluate_dataset(input_path, output_path):
    test_df = pd.read_csv(input_path)
    results = []

    for _, row in test_df.iterrows():
        case_id = row["case_id"]
        paragraph = row["paragraph"]

        expected_claim = normalize_label(row["has_optimistic_claim"])
        expected_evidence = normalize_label(row["expected_evidence_level"])
        expected_risk = normalize_label(row["expected_risk"])
        dataset_type = normalize_label(row["dataset_type"]) if "dataset_type" in row else "manual"

        output = analyze_paragraph(paragraph)

        predicted_claim = normalize_label(output["has_optimistic_claim"])
        predicted_evidence = normalize_label(output["evidence_level"])
        predicted_risk = normalize_label(output["risk_label"])
        predicted_baseline = normalize_label(output["baseline"]["baseline_label"])

        expected_baseline = "optimistic" if expected_claim == "yes" else "not optimistic"

        results.append({
            "case_id": case_id,
            "dataset_type": dataset_type,
            "paragraph": paragraph,
            "expected_claim": expected_claim,
            "predicted_claim": predicted_claim,
            "claim_correct": int(predicted_claim == expected_claim),
            "expected_baseline": expected_baseline,
            "predicted_baseline": predicted_baseline,
            "baseline_correct": int(predicted_baseline == expected_baseline),
            "expected_evidence": expected_evidence,
            "predicted_evidence": predicted_evidence,
            "evidence_correct": int(predicted_evidence == expected_evidence),
            "expected_risk": expected_risk,
            "predicted_risk": predicted_risk,
            "risk_correct": int(predicted_risk == expected_risk),
            "proposed_system_risk_correct": int(predicted_risk == expected_risk),
            "explanation": output["explanation"],
        })

    results_df = pd.DataFrame(results)
    os.makedirs("results", exist_ok=True)
    results_df.to_csv(output_path, index=False)
    return results_df


def summarize_results(results_df):
    return {
        "claim_accuracy": results_df["claim_correct"].mean(),
        "evidence_accuracy": results_df["evidence_correct"].mean(),
        "risk_accuracy": results_df["risk_correct"].mean(),
        "baseline_accuracy": results_df["baseline_correct"].mean(),
        "proposed_system_risk_accuracy": results_df["proposed_system_risk_correct"].mean(),
    }


def print_summary(title, summary, output_path):
    print(title)
    print("-" * len(title))
    print(f"Claim detection accuracy: {summary['claim_accuracy']:.2f}")
    print(f"Evidence level agreement: {summary['evidence_accuracy']:.2f}")
    print(f"Risk label accuracy: {summary['risk_accuracy']:.2f}")
    print(f"Baseline optimistic detection accuracy: {summary['baseline_accuracy']:.2f}")
    print(f"Proposed system risk accuracy: {summary['proposed_system_risk_accuracy']:.2f}")
    print(f"Saved detailed results to {output_path}")
    print()


def run_evaluation():
    manual_input = "data/test_cases.csv"
    manual_output = "results/evaluation_results.csv"
    manual_results = evaluate_dataset(manual_input, manual_output)
    manual_summary = summarize_results(manual_results)
    print_summary("Manual evaluation set", manual_summary, manual_output)

    generated_input = Path("data/generated_test_cases.csv")
    if generated_input.exists():
        generated_output = "results/generated_evaluation_results.csv"
        generated_results = evaluate_dataset(str(generated_input), generated_output)
        generated_summary = summarize_results(generated_results)
        print_summary("Synthetic robustness set", generated_summary, generated_output)
    else:
        print("Synthetic robustness set")
        print("------------------------")
        print("No data/generated_test_cases.csv found.")
        print("Run python generate_synthetic_tests.py to create the synthetic robustness dataset.")


if __name__ == "__main__":
    run_evaluation()
