"""
Test script for verifying scoring consistency.

This script tests that the same paper content always produces the same score,
validating the Phase 1 improvements to the scoring system.
"""

import sys
import os
import hashlib

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.tools.methodology_analyzer import MethodologyAnalyzerTool


def test_scoring_consistency():
    """Test that the same paper content always produces the same score."""

    print("=" * 80)
    print("SCORING CONSISTENCY TEST")
    print("=" * 80)
    print()

    # Sample paper content for testing
    test_paper_content = """
    This is a randomized controlled trial investigating the effectiveness of a new
    intervention. The study design employed a double-blind, placebo-controlled approach
    with 200 participants randomly assigned to treatment and control groups.

    Sample characteristics: The study included 200 adult participants (age 25-65,
    mean age 42.3 ± 8.7 years) recruited from three medical centers. Inclusion criteria
    included diagnosis confirmed by standardized assessment. Exclusion criteria included
    comorbid conditions and prior treatment.

    Data collection methods: Data was collected using validated instruments including
    standardized questionnaires and clinical assessments. All assessors were trained
    and calibrated. Quality control measures included regular supervision and data
    verification.

    Analysis methods: Statistical analysis employed t-tests, ANOVA, and regression
    analysis. All assumptions were checked and confirmed. Effect sizes (Cohen's d)
    and 95% confidence intervals were calculated for all primary outcomes.

    Validity measures: Internal validity was ensured through randomization and blinding.
    External validity was addressed through diverse sampling. Reliability was confirmed
    with Cronbach's alpha > 0.85 for all scales.

    Ethical considerations: The study was approved by institutional review board.
    All participants provided written informed consent. Data was de-identified and
    stored securely in compliance with data protection regulations.
    """

    # Calculate content hash
    content_hash = hashlib.sha256(test_paper_content.encode('utf-8')).hexdigest()
    print(f"Test Paper Content Hash: {content_hash[:32]}...")
    print()

    # Initialize the methodology analyzer tool
    print("Initializing MethodologyAnalyzerTool...")
    analyzer = MethodologyAnalyzerTool()
    print("✅ Tool initialized")
    print()

    # Run analysis multiple times
    num_runs = 3
    print(f"Running analysis {num_runs} times to test consistency...")
    print()

    scores = []
    hashes = []
    cached_status = []

    for i in range(num_runs):
        print(f"--- Run {i+1} ---")

        try:
            result = analyzer.execute(
                text_content=test_paper_content,
                analysis_depth="comprehensive"
            )

            if result.get("success"):
                score = result.get("overall_quality_score", 0)
                scores.append(score)

                # Check for scoring metadata
                metadata = result.get("scoring_metadata", {})
                if "content_hash" in result:
                    hashes.append(result["content_hash"])
                    cached = result.get("cached", False)
                    cached_status.append(cached)

                    print(f"  Score: {score}")
                    print(f"  Cached: {cached}")
                    print(f"  Content Hash: {result['content_hash'][:32]}...")
                else:
                    print(f"  Score: {score}")
                    print(f"  ⚠️  No content hash in result")

                # Show quantitative scores breakdown
                quant_scores = result.get("quantitative_scores", {}).get("scores", {})
                if quant_scores:
                    print(f"  Breakdown:")
                    print(f"    - Study Design: {quant_scores.get('study_design', 'N/A')}")
                    print(f"    - Sample: {quant_scores.get('sample_characteristics', 'N/A')}")
                    print(f"    - Data Collection: {quant_scores.get('data_collection', 'N/A')}")
                    print(f"    - Analysis Methods: {quant_scores.get('analysis_methods', 'N/A')}")
            else:
                print(f"  ❌ Analysis failed: {result.get('error', 'Unknown error')}")
                scores.append(None)

        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
            scores.append(None)

        print()

    # Verify consistency
    print("=" * 80)
    print("CONSISTENCY VERIFICATION")
    print("=" * 80)
    print()

    # Check if all scores are identical
    valid_scores = [s for s in scores if s is not None]

    if len(valid_scores) == num_runs:
        unique_scores = set(valid_scores)

        if len(unique_scores) == 1:
            print(f"✅ PASS: All scores are identical!")
            print(f"   Score: {valid_scores[0]}")
        else:
            print(f"❌ FAIL: Scores are inconsistent!")
            print(f"   Scores: {scores}")
            print(f"   Variance: {max(valid_scores) - min(valid_scores)} points")
    else:
        print(f"⚠️  WARNING: Some runs failed")
        print(f"   Successful runs: {len(valid_scores)}/{num_runs}")
        if len(valid_scores) > 1:
            unique_scores = set(valid_scores)
            if len(unique_scores) == 1:
                print(f"   ✅ Successful runs had consistent scores: {valid_scores[0]}")
            else:
                print(f"   ❌ Successful runs had inconsistent scores: {valid_scores}")

    print()

    # Check content hash consistency
    if len(hashes) > 0:
        unique_hashes = set(hashes)
        if len(unique_hashes) == 1:
            print(f"✅ Content hash is consistent across runs")
            print(f"   Hash: {hashes[0][:32]}...")
        else:
            print(f"❌ Content hash is inconsistent!")
            print(f"   Unique hashes: {len(unique_hashes)}")

    print()

    # Check caching behavior
    if len(cached_status) > 0:
        print(f"Caching behavior:")
        for i, cached in enumerate(cached_status):
            status = "CACHED" if cached else "FRESH"
            print(f"  Run {i+1}: {status}")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    # Return test result
    if len(valid_scores) >= 2 and len(set(valid_scores)) == 1:
        return True
    else:
        return False


if __name__ == "__main__":
    print()
    print("Starting scoring consistency test...")
    print()

    try:
        success = test_scoring_consistency()

        if success:
            print("\n✅ Overall test result: PASSED")
            sys.exit(0)
        else:
            print("\n❌ Overall test result: FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
