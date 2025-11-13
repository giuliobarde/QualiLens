# Weighted Component Scoring System (Phase 2 Revised)

## Overview

The QualiLens scoring system uses a **weighted component model** where four independent factors each contribute a specific percentage to the final score.

```
Final Score = (Methodology × 0.6) + (Bias × 0.2) + (Reproducibility × 0.1) + (Research Gaps × 0.1)
```

---

## Component Breakdown

### 1. Methodology (60% weight)

**What it measures**: Quality of research methodology and study design

**Scoring range**: 0-100 points

**Factors evaluated**:
- Study design quality
- Sample characteristics
- Data collection methods
- Analysis methods
- Validity measures
- Ethical considerations

**Example**:
```
Methodology score: 75/100
Contribution to final: 75 × 0.6 = 45 points
```

---

### 2. Bias (20% weight)

**What it measures**: Presence and severity of research biases (inverted scale)

**Scoring range**: 0-100 points
- 100 = no biases (perfect)
- 0 = many severe biases

**How it's calculated**:
```python
Start with 100 points
For each bias detected:
  - High severity: subtract 20 points
  - Medium severity: subtract 10 points
  - Low severity: subtract 5 points

  If critical bias type (selection, confounding, publication):
    - Additional 10 point penalty

Minimum: 0 points
```

**Examples**:
| Biases Detected | Calculation | Bias Score | Contribution (×0.2) |
|----------------|-------------|------------|---------------------|
| None | 100 - 0 | 100/100 | 20.0 pts |
| 1 medium | 100 - 10 | 90/100 | 18.0 pts |
| 1 high selection | 100 - 20 - 10 | 70/100 | 14.0 pts |
| 3 medium | 100 - 30 | 70/100 | 14.0 pts |
| 2 high + 2 medium (critical) | 100 - 80 | 20/100 | 4.0 pts |

---

### 3. Reproducibility (10% weight)

**What it measures**: How reproducible the research is based on available information

**Scoring range**: 0-100 points

**How it's calculated**: Keyword-based deterministic analysis

**Indicators** (cumulative points):
- Data availability (+20): "data available", "public repository", "github", "osf.io", "zenodo"
- Code availability (+20): "code available", "source code", "github.com", "analysis script"
- Methods detail (+20): "detailed method", "step-by-step", "protocol", "procedure"
- Materials availability (+15): "material available", "reagent", "equipment", "software version"
- Statistical details (+15): "statistical software", "r version", "python", "random seed"
- Pre-registration (+10): "pre-registered", "clinicaltrials.gov", "registered protocol"

**Example**:
```
Paper mentions: GitHub repo, detailed methods, R version
Reproducibility score: 20 + 20 + 15 = 55/100
Contribution to final: 55 × 0.1 = 5.5 points
```

---

### 4. Research Gaps (10% weight)

**What it measures**: Identification of research gaps and future directions

**Scoring range**: 0-100 points

**How it's calculated**: Tiered scoring based on gap count

**Base scoring**:
| Gaps Identified | Base Score |
|----------------|------------|
| 0 gaps | 0 points |
| 1-2 gaps | 40 points |
| 3-5 gaps | 70 points |
| 6-10 gaps | 90 points |
| 10+ gaps | 100 points |

**Bonuses** (capped at 100 total):
- Future directions provided: +10 points
- Theoretical gaps identified: +5 points
- Methodological gaps identified: +5 points

**Example**:
```
3 research gaps identified + future directions
Research gaps score: 70 + 10 = 80/100
Contribution to final: 80 × 0.1 = 8 points
```

---

## Complete Examples

### Example 1: Excellent Paper

```
Component Scores:
  Methodology:      90 / 100
  Bias:            100 / 100  (no biases)
  Reproducibility:  90 / 100  (code + data available)
  Research Gaps:   100 / 100  (10+ gaps identified)

Weighted Contributions:
  Methodology (60%):     90 × 0.6 = 54.0 pts
  Bias (20%):           100 × 0.2 = 20.0 pts
  Reproducibility (10%): 90 × 0.1 =  9.0 pts
  Research Gaps (10%):  100 × 0.1 = 10.0 pts
                                 ─────────
Final Score:                      93.0 / 100
```

### Example 2: Good Paper

```
Component Scores:
  Methodology:      80 / 100
  Bias:             90 / 100  (1 low bias)
  Reproducibility:  70 / 100  (some documentation)
  Research Gaps:    70 / 100  (3-5 gaps)

Weighted Contributions:
  Methodology (60%):     80 × 0.6 = 48.0 pts
  Bias (20%):            90 × 0.2 = 18.0 pts
  Reproducibility (10%): 70 × 0.1 =  7.0 pts
  Research Gaps (10%):   70 × 0.1 =  7.0 pts
                                 ─────────
Final Score:                      80.0 / 100
```

### Example 3: Average Paper

```
Component Scores:
  Methodology:      65 / 100
  Bias:             50 / 100  (multiple medium biases)
  Reproducibility:  50 / 100  (moderate info)
  Research Gaps:    40 / 100  (1-2 gaps)

Weighted Contributions:
  Methodology (60%):     65 × 0.6 = 39.0 pts
  Bias (20%):            50 × 0.2 = 10.0 pts
  Reproducibility (10%): 50 × 0.1 =  5.0 pts
  Research Gaps (10%):   40 × 0.1 =  4.0 pts
                                 ─────────
Final Score:                      58.0 / 100
```

### Example 4: Poor Paper

```
Component Scores:
  Methodology:      40 / 100
  Bias:             10 / 100  (multiple severe biases)
  Reproducibility:  20 / 100  (poor documentation)
  Research Gaps:     0 / 100  (no gaps identified)

Weighted Contributions:
  Methodology (60%):     40 × 0.6 = 24.0 pts
  Bias (20%):            10 × 0.2 =  2.0 pts
  Reproducibility (10%): 20 × 0.1 =  2.0 pts
  Research Gaps (10%):    0 × 0.1 =  0.0 pts
                                 ─────────
Final Score:                      28.0 / 100
```

---

## User-Provided Examples

The user provided two examples to illustrate the desired scoring:

### User Example 1
**Input**: Methodology=100, 5 biases, not reproducible, 10 research gaps

**Expected by user**: ~60 points (60+0+0+0, apparently ignoring gaps)

**Actual calculation**:
```
Methodology:     100 × 0.6 = 60.0 pts
Bias (5 biases):   0 × 0.2 =  0.0 pts  (many biases = 0 score)
Reproducibility:   0 × 0.1 =  0.0 pts
Research Gaps:   100 × 0.1 = 10.0 pts  (10+ gaps = 100 score)
                           ─────────
Final:                      70.0 / 100
```

**Note**: 10 research gaps should contribute 10 points (10% of 100).

### User Example 2
**Input**: Methodology=75, no biases, very reproducible, no gaps

**Expected by user**: 85 points (45+20+10+0)

**Actual calculation**:
```
Methodology:      75 × 0.6 = 45.0 pts
Bias (none):     100 × 0.2 = 20.0 pts
Reproducibility: 100 × 0.1 = 10.0 pts
Research Gaps:     0 × 0.1 =  0.0 pts
                           ─────────
Final:                      75.0 / 100
```

**Note**: User's stated math (45+20+10+0) equals 75, not 85. Possible typo in expected value.

---

## Key Properties

### Deterministic
✅ **Same input = same output (always)**
- All components use deterministic calculations
- No randomness in scoring
- Consistent across multiple runs

### Transparent
✅ **Every point is explainable**
- Each component score visible (0-100)
- Weighted contribution visible
- Full breakdown provided in response

### Balanced
✅ **Methodology dominant but not exclusive**
- Methodology: 60% (primary factor)
- Other factors: 40% combined (significant impact)
- Perfect methodology alone = 60/100 final
- Poor methodology cannot reach high scores

### Bounded
✅ **Scores stay within valid range**
- Each component: 0-100
- Final score: 0-100 (clamped if needed)
- No negative scores

---

## Response Structure

When analyzing a paper, the system returns:

```json
{
  "overall_quality_score": 78.5,
  "base_methodology_score": 75.0,

  "component_scores": {
    "methodology": 75.0,
    "bias": 80.0,
    "reproducibility": 85.0,
    "research_gaps": 70.0
  },

  "weighted_contributions": {
    "methodology": 45.0,
    "bias": 16.0,
    "reproducibility": 8.5,
    "research_gaps": 7.0
  },

  "scoring_weights": {
    "methodology": 0.6,
    "bias": 0.2,
    "reproducibility": 0.1,
    "research_gaps": 0.1
  }
}
```

---

## Implementation Files

### Core Implementation
- **[enhanced_scorer.py](backend/agents/enhanced_scorer.py)** - Weighted scoring logic
- **[paper_analysis_agent.py](backend/agents/agents/paper_analysis_agent.py)** - Integration
- **[score_cache.py](backend/agents/score_cache.py)** - Caching (Version 3)

### Testing
- **[test_weighted_scoring_simple.py](backend/test_weighted_scoring_simple.py)** - Simple calculation tests

### Documentation
- **[SCORING_SYSTEM_COMPLETE.md](SCORING_SYSTEM_COMPLETE.md)** - Complete system overview
- **[PHASE1_IMPROVEMENTS.md](PHASE1_IMPROVEMENTS.md)** - Consistency improvements
- **[PHASE2_ENHANCEMENTS.md](PHASE2_ENHANCEMENTS.md)** - Enhanced scoring details

---

## Version History

- **Version 1**: Basic methodology scoring only
- **Version 2**: Added adjustments for reproducibility, bias, research gaps
- **Version 3**: **Current** - Weighted component system (60/20/10/10)

**Cache Version**: 3 (invalidates all previous caches)

---

## Quick Reference

### Weights
- Methodology: **60%**
- Bias: **20%**
- Reproducibility: **10%**
- Research Gaps: **10%**
- **Total: 100%**

### Scoring Formula
```
Final = (M × 0.6) + (B × 0.2) + (R × 0.1) + (G × 0.1)
```

### Component Ranges
- All components: **0-100 points**
- Final score: **0-100 points**

### Typical Scores
- Excellent paper: **85-95**
- Good paper: **70-84**
- Average paper: **50-69**
- Poor paper: **0-49**

---

**Status**: ✅ Implemented and tested
**Date**: 2025-11-13
**Production Ready**: Yes
