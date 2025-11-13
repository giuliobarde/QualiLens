# Chain-of-Thought Improvements for Bias & Research Gap Detection

## Overview

Implemented **two-step chain-of-thought reasoning** for bias detection and research gap identification to improve accuracy and reduce false positives/negatives.

**Date**: 2025-11-13
**Version**: 5
**Status**: ✅ Implemented

---

## Architecture Decision: Tools vs. Agents

### Decision: Stick with Tools ✅

**Rationale**:
- Tools are specialists with clear, focused responsibilities
- Single agent (paper_analysis_agent) orchestrates the workflow
- Simpler to maintain with less coordination complexity
- Proven pattern for this use case

### When to Use Multiple Agents

Multiple agents make sense when you need:
- **Parallel independent workflows** (e.g., separate agents for papers vs. user queries)
- **Different contexts/goals** (e.g., analysis agent vs. QA agent)
- **Complex multi-turn conversations** between agents

For **verification within a single analysis pipeline**, tools are better - they're essentially "specialized functions" the agent can call.

---

## Two-Step Process Design

### Philosophy

1. **Step 1 (Brainstorming)**: Cast a wide net
   - Temperature = 0.3 (some creativity)
   - Identify ALL potential items (biases/gaps)
   - Include edge cases and subtle issues
   - Don't worry about false positives

2. **Step 2 (Verification)**: Rigorous filtering
   - Temperature = 0.0 (deterministic)
   - Verify each potential item with chain-of-thought reasoning
   - Reject false positives with clear reasoning
   - Only confirm genuine issues

### Benefits

✅ **Higher Recall**: Brainstorming phase catches subtle issues
✅ **Higher Precision**: Verification phase filters false positives
✅ **Explainable**: Each decision has chain-of-thought reasoning
✅ **Consistent**: Verification step is deterministic (temperature=0)
✅ **Transparent**: Shows both confirmed and rejected items

---

## Bias Detection (Two-Step)

### Step 1: Brainstorm Potential Biases

**Purpose**: Identify ALL potential biases without filtering
**Temperature**: 0.3 (creative)
**Max Tokens**: 2000

**Prompt Strategy**:
```
- Be thorough and creative
- Include anything that MIGHT be a bias
- Provide reasoning for each potential bias
- Include edge cases and subtle biases
- Don't worry about false positives
```

**Output**:
```json
{
  "potential_biases": [
    {
      "bias_type": "selection_bias",
      "initial_assessment": "Why this might be a bias",
      "evidence_snippet": "Specific quote from paper",
      "potential_severity": "low | medium | high",
      "reasoning": "Chain-of-thought"
    }
  ]
}
```

---

### Step 2: Verify & Analyze Biases

**Purpose**: Rigorously verify each potential bias
**Temperature**: 0.0 (deterministic)
**Max Tokens**: 2500

**Chain-of-Thought Framework**:
1. **ANALYZE**: What does the evidence actually show?
2. **EVALUATE**: Is this a genuine bias or limitation?
3. **ASSESS**: If it's a bias, how severe is it?
4. **CONCLUDE**: Should this be included in the final list?

**Prompt Strategy**:
```
- Carefully examine evidence
- Determine TRUE bias vs. false positive
- Assess severity and impact
- Provide clear justification
- Be conservative when in doubt
```

**Output**:
```json
{
  "detected_biases": [
    {
      "bias_type": "selection_bias",
      "description": "Clear description of confirmed bias",
      "evidence": "Specific evidence from paper",
      "severity": "low | medium | high",
      "impact": "How this affects study validity",
      "verification_reasoning": "Chain-of-thought for confirmation"
    }
  ],
  "rejected_biases": [
    {
      "bias_type": "measurement_bias",
      "rejection_reasoning": "Why this is NOT a genuine bias"
    }
  ]
}
```

---

## Research Gap Identification (Two-Step)

### Step 1: Brainstorm Potential Gaps

**Purpose**: Identify ALL potential research gaps
**Temperature**: 0.3 (creative)
**Max Tokens**: 2000

**Prompt Strategy**:
```
- Be thorough and creative
- Include anything that MIGHT be missing
- Consider all gap types: methodological, theoretical, empirical, practical
- Think about what's unexplored or inadequately addressed
- Don't worry about false positives
```

**Gap Categories**:
1. **Methodological**: Missing methods, inadequate controls, sample limitations
2. **Theoretical**: Unexplored frameworks, missing constructs
3. **Empirical**: Untested hypotheses, unexplored populations
4. **Practical**: Real-world applications not explored
5. **Conceptual**: Undefined terms, ambiguous concepts

**Output**:
```json
{
  "potential_gaps": [
    {
      "gap_type": "methodological | theoretical | empirical | practical",
      "initial_assessment": "What might be missing",
      "evidence": "Why this might be a gap",
      "potential_significance": "Why this could be important",
      "reasoning": "Chain-of-thought"
    }
  ],
  "potential_future_directions": [
    {
      "direction": "Potential research direction",
      "rationale": "Why this might be worth pursuing",
      "reasoning": "Chain-of-thought"
    }
  ]
}
```

---

### Step 2: Verify & Evaluate Gaps

**Purpose**: Rigorously verify each potential gap
**Temperature**: 0.0 (deterministic)
**Max Tokens**: 2500

**Chain-of-Thought Framework**:
1. **ANALYZE**: Is this actually missing from the paper?
2. **EVALUATE**: If missing, is it a significant gap or minor limitation?
3. **ASSESS**: What's the potential impact of addressing this gap?
4. **PRIORITIZE**: How important is this gap relative to others?
5. **CONCLUDE**: Should this be included as a confirmed research gap?

**Prompt Strategy**:
```
- Examine whether truly missing or already addressed
- Determine REAL gap vs. false positive
- Assess significance and impact
- Provide clear justification
- Number of gaps should vary by paper completeness
```

**Verification Standards**:
- Comprehensive papers: 0-2 major gaps
- Average papers: 3-5 gaps
- Papers with limitations: 6+ gaps
- Based on ACTUAL analysis, not arbitrary numbers

**Output**:
```json
{
  "research_gaps": [
    {
      "gap_type": "methodological",
      "description": "Clear description of confirmed gap",
      "significance": "Why this gap is important",
      "evidence": "Evidence showing this is missing",
      "verification_reasoning": "Chain-of-thought for confirmation"
    }
  ],
  "rejected_gaps": [
    {
      "gap_type": "theoretical",
      "rejection_reasoning": "Why this is NOT a real gap"
    }
  ]
}
```

---

## Expected Outcomes

### Improved Accuracy

**Bias Detection**:
- ✅ Fewer false positives (verification step filters)
- ✅ Fewer false negatives (brainstorming catches subtle issues)
- ✅ Better severity assessment (two-phase analysis)
- ✅ Clearer explanations (chain-of-thought reasoning)

**Research Gap Identification**:
- ✅ More nuanced gap detection
- ✅ Better distinction between gaps and limitations
- ✅ Variable gap counts based on paper quality (not fixed)
- ✅ Higher quality future directions

---

## Performance Considerations

### API Calls

**Before**: 1 call per analysis
**After**: 2 calls per analysis (brainstorm + verify)

**Impact**:
- Bias detection: 1 → 2 calls
- Research gaps: 1 → 2 calls
- **Total additional calls**: +2 per paper analysis

### Latency

**Estimated Impact**:
- Bias detection: +2-3 seconds
- Research gap identification: +2-3 seconds
- **Total additional latency**: +4-6 seconds per full analysis

**Mitigation**:
- Tools run in parallel (no sequential dependency)
- Caching still applies (same paper = cached results)
- Trade-off is worth it for improved accuracy

---

## Temperature Strategy

| Step | Tool | Temperature | Rationale |
|------|------|-------------|-----------|
| Step 1 | Bias Brainstorm | 0.3 | Creative exploration |
| Step 2 | Bias Verify | 0.0 | Deterministic filtering |
| Step 1 | Gap Brainstorm | 0.3 | Creative exploration |
| Step 2 | Gap Verify | 0.0 | Deterministic filtering |

**Why This Works**:
- Step 1 needs creativity to catch edge cases
- Step 2 needs determinism for consistency
- Combined: Best of both worlds

---

## Consistency Guarantee

### What's Deterministic?

✅ **Step 2 (Verification)**: Always temperature=0.0
- Same potential items → same verification decisions
- Consistent severity assessments
- Reproducible final lists

### What's Not Deterministic?

⚠️ **Step 1 (Brainstorming)**: Temperature=0.3
- May generate slightly different potential items
- This is INTENTIONAL - we want thorough exploration
- Step 2 ensures consistent final results

### Net Result

✅ **Final outputs are consistent enough**:
- Verification step (temp=0) filters consistently
- Same genuine biases/gaps will be confirmed
- Slight variation in brainstorming doesn't affect final quality
- More important: improved accuracy vs. perfect determinism in brainstorming

**If absolute determinism is needed**: Set Step 1 temperature to 0.0 (trade-off: may miss subtle issues)

---

## Examples

### Bias Detection Example

**Step 1 Output**:
```json
{
  "potential_biases": [
    {
      "bias_type": "selection_bias",
      "initial_assessment": "Sample recruited only from university students",
      "evidence_snippet": "Participants were recruited from undergraduate psychology courses",
      "potential_severity": "high",
      "reasoning": "University students are not representative of general population"
    },
    {
      "bias_type": "measurement_bias",
      "initial_assessment": "Self-reported data may be subject to social desirability",
      "evidence_snippet": "All measures were self-reported surveys",
      "potential_severity": "medium",
      "reasoning": "Self-report can introduce response bias"
    }
  ]
}
```

**Step 2 Output**:
```json
{
  "detected_biases": [
    {
      "bias_type": "selection_bias",
      "description": "Sample limited to university students, limiting generalizability",
      "evidence": "Participants recruited exclusively from undergraduate psychology courses",
      "severity": "high",
      "impact": "Results may not generalize beyond educated young adults",
      "verification_reasoning": "ANALYZE: Paper explicitly states sample is from one university. EVALUATE: This is genuine selection bias as population is highly specific. ASSESS: High severity due to significant limitation in generalizability. CONCLUDE: Confirmed as high-severity selection bias."
    }
  ],
  "rejected_biases": [
    {
      "bias_type": "measurement_bias",
      "rejection_reasoning": "ANALYZE: While data is self-reported, paper validates measures against objective criteria. EVALUATE: Self-report alone is not a bias if measures are validated. ASSESS: This is a methodological choice, not a bias. CONCLUDE: Rejected - this is a limitation, not a bias."
    }
  ]
}
```

---

## Integration

### Files Modified

1. **[bias_detection.py](backend/agents/tools/bias_detection.py)**
   - Added two-step process
   - Step 1: Lines 123-186
   - Step 2: Lines 187-281

2. **[research_gap_identifier.py](backend/agents/tools/research_gap_identifier.py)**
   - Added two-step process
   - Step 1: Lines 118-189
   - Step 2: Lines 191-324

3. **[score_cache.py](backend/agents/score_cache.py)**
   - Bumped CACHE_VERSION to 5

### No Changes Needed

- ✅ Agent orchestration (paper_analysis_agent) remains unchanged
- ✅ Tool interfaces remain the same
- ✅ Response structure unchanged (except new `rejected_*` fields)
- ✅ Scoring formula unchanged

---

## Testing Recommendations

### Test for Accuracy

```python
# Test: Analyze paper with known biases
paper_with_biases = """..."""  # Paper with obvious selection bias

result = analyze_paper(paper_with_biases)
biases = result["bias_analysis"]["detected_biases"]

# Check: Selection bias should be detected
assert any(b["bias_type"] == "selection_bias" for b in biases)

# Check: Rejected biases should have clear reasoning
rejected = result["bias_analysis"].get("rejected_biases", [])
for r in rejected:
    assert "rejection_reasoning" in r
    assert len(r["rejection_reasoning"]) > 50  # Substantive reasoning
```

### Test for Consistency

```python
# Test: Verify Step 2 is deterministic
# (Step 1 may vary, but Step 2 should be consistent for same inputs)

# Note: This requires testing with same brainstormed items
# In practice, end-to-end consistency is "consistent enough"
# due to deterministic verification step
```

---

## Future Improvements

### Potential Enhancements

1. **Add Step 3 (Prioritization)**
   - Rank confirmed biases/gaps by importance
   - Focus on most critical issues first

2. **Self-Reflection Loop**
   - Step 3: Review own verification decisions
   - Catch verification errors

3. **Confidence Scores**
   - Add confidence level to each confirmed item
   - Help users understand certainty

4. **Few-Shot Examples**
   - Provide examples of genuine vs. false biases
   - Improve verification accuracy

---

## Summary

### What Changed

- ✅ **Bias detection**: Now uses 2-step chain-of-thought (brainstorm + verify)
- ✅ **Research gap identification**: Now uses 2-step chain-of-thought (brainstorm + verify)
- ✅ **Cache version**: Bumped to 5
- ✅ **Architecture**: Kept tools-based approach (not multiple agents)

### Why It's Better

- ✅ **Higher accuracy**: Better recall + precision
- ✅ **More explainable**: Chain-of-thought reasoning provided
- ✅ **Transparent**: Shows rejected items with reasoning
- ✅ **Appropriate consistency**: Verification step is deterministic

### Trade-offs

- ⚠️ **More API calls**: +2 per paper (bias + gaps)
- ⚠️ **Slightly longer**: +4-6 seconds per analysis
- ⚠️ **Step 1 variability**: Brainstorming uses temp=0.3 (intentional)

**Net Result**: Improved quality is worth the trade-offs ✅

---

**Status**: ✅ Implemented and ready for testing
**Version**: 5
**Cache Version**: 5
**Production Ready**: Yes (test first!)
