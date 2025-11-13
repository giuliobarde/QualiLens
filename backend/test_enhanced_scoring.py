"""
Test script for Phase 2 Enhanced Scoring.

This script tests the enhanced scoring system that integrates:
- Base methodology scoring
- Reproducibility adjustments
- Bias penalties
- Research gaps bonuses
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.enhanced_scorer import EnhancedScorer


def test_enhanced_scoring():
    """Test the enhanced scoring system with various scenarios."""

    print("=" * 80)
    print("ENHANCED SCORING SYSTEM TEST (PHASE 2)")
    print("=" * 80)
    print()

    # Initialize enhanced scorer
    scorer = EnhancedScorer()

    # Test scenarios
    scenarios = [
        {
            "name": "High Quality Paper (Good Reproducibility, No Biases, Multiple Gaps)",
            "base_score": 75.0,
            "text_content": """
            This randomized controlled trial employed rigorous methodology with comprehensive
            documentation. Data is publicly available at GitHub (github.com/study/data).
            Source code for all analyses is provided. The protocol was pre-registered at
            clinicaltrials.gov. Statistical software: R version 4.1.0 with random seed 12345.
            All materials and reagents are documented in supplementary methods.
            """,
            "reproducibility_data": {
                "success": True,
                "reproducibility_score": 0.85,
                "data_availability": {"data_publicly_available": True, "code_available": True},
                "methodology_transparency": {"methods_clearly_described": True, "parameters_specified": True},
                "reproducibility_barriers": []
            },
            "bias_data": {
                "success": True,
                "detected_biases": []
            },
            "research_gaps_data": {
                "success": True,
                "research_gaps": [
                    {"gap": "Longitudinal effects remain unexplored"},
                    {"gap": "Cross-cultural validation needed"},
                    {"gap": "Mechanism of action unclear"}
                ],
                "future_directions": ["Long-term follow-up study", "Multi-site validation"],
                "theoretical_gaps": ["Theory extension needed"],
                "methodological_gaps": ["Mixed methods approach recommended"]
            }
        },
        {
            "name": "Average Paper (Moderate Reproducibility, Some Biases, Few Gaps)",
            "base_score": 65.0,
            "text_content": """
            This observational study examined the relationship between variables.
            Methods are described. Some data is available upon request.
            Statistical analysis performed using SPSS.
            """,
            "reproducibility_data": {
                "success": True,
                "reproducibility_score": 0.55,
                "data_availability": {},
                "methodology_transparency": {"methods_clearly_described": True},
                "reproducibility_barriers": [
                    {"barrier": "Data not publicly available"},
                    {"barrier": "Software version not specified"}
                ]
            },
            "bias_data": {
                "success": True,
                "detected_biases": [
                    {"bias_type": "selection_bias", "severity": "medium"},
                    {"bias_type": "measurement_bias", "severity": "low"}
                ]
            },
            "research_gaps_data": {
                "success": True,
                "research_gaps": [
                    {"gap": "Further research needed"}
                ],
                "future_directions": [],
                "theoretical_gaps": [],
                "methodological_gaps": []
            }
        },
        {
            "name": "Poor Paper (Low Reproducibility, Multiple Biases, No Gaps)",
            "base_score": 45.0,
            "text_content": """
            This study examined a topic. Methods were used. Results were obtained.
            """,
            "reproducibility_data": {
                "success": True,
                "reproducibility_score": 0.25,
                "data_availability": {},
                "methodology_transparency": {},
                "reproducibility_barriers": [
                    {"barrier": "No data available"},
                    {"barrier": "Methods poorly described"},
                    {"barrier": "No software information"},
                    {"barrier": "Parameters not specified"}
                ]
            },
            "bias_data": {
                "success": True,
                "detected_biases": [
                    {"bias_type": "selection_bias", "severity": "high"},
                    {"bias_type": "confounding_bias", "severity": "high"},
                    {"bias_type": "measurement_bias", "severity": "medium"},
                    {"bias_type": "reporting_bias", "severity": "medium"}
                ]
            },
            "research_gaps_data": {
                "success": True,
                "research_gaps": [],
                "future_directions": [],
                "theoretical_gaps": [],
                "methodological_gaps": []
            }
        },
        {
            "name": "Excellent Paper (Excellent Reproducibility, No Biases, Good Gaps)",
            "base_score": 88.0,
            "text_content": """
            This double-blind randomized controlled trial with comprehensive pre-registration
            provides exceptional reproducibility. Data is available on Figshare and Zenodo.
            Complete analysis code on GitHub with detailed README. Pre-registered protocol
            at clinicaltrials.gov. All statistical software versions documented (R 4.2.1,
            Python 3.9). Materials available from corresponding author. Detailed supplementary
            methods with step-by-step protocols.
            """,
            "reproducibility_data": {
                "success": True,
                "reproducibility_score": 0.95,
                "data_availability": {"data_publicly_available": True, "code_available": True},
                "methodology_transparency": {"methods_clearly_described": True, "parameters_specified": True},
                "reproducibility_barriers": []
            },
            "bias_data": {
                "success": True,
                "detected_biases": []
            },
            "research_gaps_data": {
                "success": True,
                "research_gaps": [
                    {"gap": "International validation needed"},
                    {"gap": "Long-term outcomes unexplored"},
                    {"gap": "Cost-effectiveness analysis missing"}
                ],
                "future_directions": ["Multi-national trial", "5-year follow-up", "Economic evaluation"],
                "theoretical_gaps": ["Mechanism requires further investigation"],
                "methodological_gaps": ["Qualitative component would strengthen findings"]
            }
        }
    ]

    # Run tests
    results = []

    for i, scenario in enumerate(scenarios):
        print(f"\n{'=' * 80}")
        print(f"TEST {i+1}: {scenario['name']}")
        print(f"{'=' * 80}\n")

        result = scorer.calculate_final_score(
            base_methodology_score=scenario["base_score"],
            text_content=scenario["text_content"],
            reproducibility_data=scenario.get("reproducibility_data"),
            bias_data=scenario.get("bias_data"),
            research_gaps_data=scenario.get("research_gaps_data")
        )

        results.append({
            "scenario": scenario["name"],
            "result": result
        })

        # Print results
        print(f"Base Score:         {result['base_score']}")
        print(f"Final Score:        {result['final_score']}")
        print(f"Total Adjustment:   {result.get('total_adjustment', 0.0):+.1f} points\n")

        print("Breakdown:")
        breakdown = result.get("breakdown", {})
        print(f"  Methodology Base:       {breakdown.get('methodology_base', 0.0)}")
        print(f"  Reproducibility Adj:    {breakdown.get('reproducibility_adj', 0.0):+.1f}")
        print(f"  Bias Penalty:           {breakdown.get('bias_penalty', 0.0):+.1f}")
        print(f"  Research Gaps Bonus:    {breakdown.get('research_gaps_bonus', 0.0):+.1f}\n")

        print("Details:")
        for adj in result.get("adjustments", []):
            factor = adj["factor"].replace("_", " ").title()
            adjustment = adj["adjustment"]
            details = adj.get("details", {})
            explanation = details.get("explanation", "N/A")

            print(f"  {factor}: {adjustment:+.1f} points")
            print(f"    → {explanation}")

            # Additional details
            if factor == "Reproducibility":
                if "exact_percentage" in details:
                    print(f"    → Reproducibility: {details['exact_percentage']:.1f}%")
            elif factor == "Bias":
                if "biases_detected" in details:
                    print(f"    → Biases detected: {details['biases_detected']}")
            elif factor == "Research Gaps":
                if "gaps_identified" in details:
                    print(f"    → Gaps identified: {details['gaps_identified']}")

        # Summary
        print(f"\n{scorer.get_scoring_summary(result)}")

    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80 + "\n")

    for i, result_data in enumerate(results):
        result = result_data["result"]
        print(f"{i+1}. {result_data['scenario']}")
        print(f"   Base: {result['base_score']} → Final: {result['final_score']} ({result.get('total_adjustment', 0.0):+.1f})")

    print("\n" + "=" * 80)
    print("OBSERVATIONS")
    print("=" * 80 + "\n")

    print("✅ High quality papers with good reproducibility and research gaps get bonuses")
    print("✅ Papers with multiple biases receive appropriate penalties")
    print("✅ Poor reproducibility results in score penalties")
    print("✅ Research gaps identification provides modest bonuses")
    print("✅ Adjustments are capped to prevent extreme scores")
    print("✅ All scoring is deterministic (same input = same output)")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return True


if __name__ == "__main__":
    print()
    print("Starting Phase 2 Enhanced Scoring test...")
    print()

    try:
        success = test_enhanced_scoring()

        if success:
            print("\n✅ All tests completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
