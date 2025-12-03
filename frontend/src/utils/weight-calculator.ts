/**
 * Utility functions for calculating and adjusting rubric weights
 */

export interface ComponentScores {
  methodology: number;
  bias: number;
  reproducibility: number;
  research_gaps: number;
}

export interface RubricWeights {
  methodology: number;
  bias: number;
  reproducibility: number;
  research_gaps: number;
}

/**
 * Calculate weights that would produce the desired overall score
 * given the individual component scores.
 * 
 * This solves: desired_score = sum(component_score * weight)
 * with constraint: sum(weights) = 1
 * 
 * Uses a proportional adjustment approach:
 * 1. Calculate current weighted score
 * 2. Calculate difference needed
 * 3. Adjust weights proportionally to components that can contribute
 * 
 * @param componentScores Individual section scores (0-100)
 * @param desiredOverallScore Target overall score (0-100)
 * @param currentWeights Current weights (optional, defaults to standard)
 * @returns New weights that would produce the desired score
 */
export function calculateWeightsForScore(
  componentScores: ComponentScores,
  desiredOverallScore: number,
  currentWeights?: RubricWeights
): RubricWeights {
  const defaultWeights: RubricWeights = {
    methodology: 0.60,
    bias: 0.20,
    reproducibility: 0.10,
    research_gaps: 0.10,
  };

  const weights = currentWeights || defaultWeights;

  // Calculate current weighted score
  const currentScore =
    componentScores.methodology * weights.methodology +
    componentScores.bias * weights.bias +
    componentScores.reproducibility * weights.reproducibility +
    componentScores.research_gaps * weights.research_gaps;

  const scoreDifference = desiredOverallScore - currentScore;

  // If difference is very small, return current weights
  if (Math.abs(scoreDifference) < 0.1) {
    return weights;
  }

  // Calculate how much each component can contribute to the change
  // Components with higher scores can contribute more to increasing the overall
  // Components with lower scores can contribute more to decreasing the overall
  const contributions = {
    methodology: componentScores.methodology - currentScore,
    bias: componentScores.bias - currentScore,
    reproducibility: componentScores.reproducibility - currentScore,
    research_gaps: componentScores.research_gaps - currentScore,
  };

  // Calculate adjustment factors
  // Positive contributions help increase score, negative help decrease
  const totalContribution = 
    Math.abs(contributions.methodology) * weights.methodology +
    Math.abs(contributions.bias) * weights.bias +
    Math.abs(contributions.reproducibility) * weights.reproducibility +
    Math.abs(contributions.research_gaps) * weights.research_gaps;

  if (totalContribution === 0) {
    // All components have the same score, can't adjust meaningfully
    return weights;
  }

  // Calculate weight adjustments
  // We want to shift weight toward components that can help achieve the desired score
  const adjustmentFactor = scoreDifference / (totalContribution * 10); // Scale factor

  const newWeights: RubricWeights = {
    methodology: weights.methodology + (contributions.methodology * weights.methodology * adjustmentFactor),
    bias: weights.bias + (contributions.bias * weights.bias * adjustmentFactor),
    reproducibility: weights.reproducibility + (contributions.reproducibility * weights.reproducibility * adjustmentFactor),
    research_gaps: weights.research_gaps + (contributions.research_gaps * weights.research_gaps * adjustmentFactor),
  };

  // Ensure all weights are non-negative
  newWeights.methodology = Math.max(0, newWeights.methodology);
  newWeights.bias = Math.max(0, newWeights.bias);
  newWeights.reproducibility = Math.max(0, newWeights.reproducibility);
  newWeights.research_gaps = Math.max(0, newWeights.research_gaps);

  // Normalize to sum to 1.0
  const sum = newWeights.methodology + newWeights.bias + newWeights.reproducibility + newWeights.research_gaps;
  if (sum > 0) {
    return {
      methodology: newWeights.methodology / sum,
      bias: newWeights.bias / sum,
      reproducibility: newWeights.reproducibility / sum,
      research_gaps: newWeights.research_gaps / sum,
    };
  }

  // Fallback to default if normalization fails
  return defaultWeights;
}

/**
 * Calculate overall score from component scores and weights
 */
export function calculateOverallScore(
  componentScores: ComponentScores,
  weights: RubricWeights
): number {
  return (
    componentScores.methodology * weights.methodology +
    componentScores.bias * weights.bias +
    componentScores.reproducibility * weights.reproducibility +
    componentScores.research_gaps * weights.research_gaps
  );
}

/**
 * Extract component scores from analysis result data
 * Backend now always provides component_scores, so this is the primary source
 */
export function extractComponentScores(data: any): ComponentScores | null {
  // Primary: Get from component_scores (backend always provides this now)
  if (data?.component_scores) {
    return {
      methodology: data.component_scores.methodology || 0,
      bias: data.component_scores.bias || 0,
      reproducibility: data.component_scores.reproducibility || 0,
      research_gaps: data.component_scores.research_gaps || 0,
    };
  }

  // Fallback: Try to get scores from quality_breakdown (legacy support)
  if (data?.quality_breakdown) {
    const breakdown = data.quality_breakdown;
    return {
      methodology: breakdown.methodology?.score || 0,
      bias: breakdown.bias?.score || 0,
      reproducibility: breakdown.reproducibility?.score || 0,
      research_gaps: breakdown.research_gaps?.score || 0,
    };
  }

  // Fallback: try to calculate from individual metrics
  let methodology = 0;
  let bias = 0;
  let reproducibility = 0;
  let research_gaps = 0;

  // Methodology
  if (data?.methodology_quality_rating) {
    methodology = data.methodology_quality_rating.toLowerCase().includes('high') ? 90 :
                  data.methodology_quality_rating.toLowerCase().includes('medium') ? 70 : 50;
  }

  // Bias (inverted - fewer biases = higher score)
  if (data?.detected_biases && Array.isArray(data.detected_biases)) {
    bias = Math.max(0, 100 - (data.detected_biases.length * 20));
  }

  // Reproducibility
  if (data?.reproducibility_score !== undefined) {
    // Normalize to 0-100 range (backend may return 0-1 or 0-100)
    reproducibility = data.reproducibility_score <= 1.0 
      ? data.reproducibility_score * 100 
      : data.reproducibility_score;
  }

  // Research Gaps (based on count)
  if (data?.research_gaps && Array.isArray(data.research_gaps)) {
    const gapsCount = data.research_gaps.length;
    if (gapsCount === 0) {
      research_gaps = 0;
    } else if (gapsCount <= 2) {
      research_gaps = 40;
    } else if (gapsCount <= 5) {
      research_gaps = 70;
    } else if (gapsCount <= 10) {
      research_gaps = 90;
    } else {
      research_gaps = 100;
    }
  }

  // Only return if we have at least some data
  if (methodology > 0 || bias > 0 || reproducibility > 0 || research_gaps > 0) {
    return { methodology, bias, reproducibility, research_gaps };
  }

  return null;
}

