'use client';

import React, { useEffect, useState } from 'react';

interface QualityScoreDisplayProps {
  data: any;
  className?: string;
}

interface ScoreBreakdown {
  methodology: number;
  reproducibility: number;
  bias: number;
  statistics: number;
  overall: number;
  source: string;
}

export default function QualityScoreDisplay({ data, className = '' }: QualityScoreDisplayProps) {
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdown | null>(null);
  const [debugInfo, setDebugInfo] = useState<string>('');

  // Comprehensive score calculation with debugging
  const calculateComprehensiveScore = (): ScoreBreakdown => {
    console.log('🔍 QUALITY SCORE CALCULATION DEBUG:');
    console.log('Raw data received:', data);
    
    let debugLog = 'Score Calculation Debug:\n';
    debugLog += `Data keys: ${Object.keys(data || {})}\n`;
    
    // Method 1: Direct overall_quality_score from backend
    if (data?.overall_quality_score !== undefined && data?.overall_quality_score !== null) {
      const directScore = Number(data.overall_quality_score);
      debugLog += `✅ Found direct overall_quality_score: ${directScore}\n`;
      console.log('✅ Using direct overall_quality_score:', directScore);
      
      // Check if this is a suspiciously low score (likely from quality assessor override)
      if (directScore < 50 && data?.quantitative_scores?.scores?.overall_score > directScore) {
        const methodologyScore = data.quantitative_scores.scores.overall_score;
        debugLog += `⚠️ Low score detected (${directScore}), using methodology score: ${methodologyScore}\n`;
        console.log('⚠️ Using methodology analyzer score instead of quality assessor:', methodologyScore);
        return {
          methodology: methodologyScore,
          reproducibility: methodologyScore,
          bias: methodologyScore,
          statistics: methodologyScore,
          overall: methodologyScore,
          source: 'methodology_override'
        };
      }
      
      return {
        methodology: directScore,
        reproducibility: directScore,
        bias: directScore,
        statistics: directScore,
        overall: directScore,
        source: 'direct_backend_score'
      };
    }
    
    // Method 2: Check quality_breakdown from quality assessor
    if (data?.quality_breakdown) {
      debugLog += `Found quality_breakdown: ${JSON.stringify(data.quality_breakdown)}\n`;
      const breakdown = data.quality_breakdown;
      const methodology = breakdown.methodology?.score || 0;
      const reproducibility = breakdown.reproducibility?.score || 0;
      const bias = breakdown.bias?.score || 0;
      const statistics = breakdown.statistics?.score || 0;
      
      const overall = (methodology + reproducibility + bias + statistics) / 4;
      debugLog += `Calculated from quality_breakdown: ${overall}\n`;
      console.log('✅ Using quality_breakdown scores:', { methodology, reproducibility, bias, statistics, overall });
      return {
        methodology,
        reproducibility,
        bias,
        statistics,
        overall,
        source: 'quality_breakdown'
      };
    }
    
    // Method 3: Check quantitative_scores from methodology analyzer
    if (data?.quantitative_scores?.scores) {
      debugLog += `Found quantitative_scores: ${JSON.stringify(data.quantitative_scores.scores)}\n`;
      const scores = data.quantitative_scores.scores;
      const overall = scores.overall_score || 0;
      debugLog += `Using quantitative_scores overall: ${overall}\n`;
      console.log('✅ Using quantitative_scores:', overall);
      return {
        methodology: scores.study_design || 0,
        reproducibility: scores.data_collection || 0,
        bias: scores.validity_measures || 0,
        statistics: scores.analysis_methods || 0,
        overall,
        source: 'quantitative_scores'
      };
    }
    
    // Method 4: Calculate from individual metrics
    debugLog += 'Calculating from individual metrics...\n';
    let totalScore = 0;
    let count = 0;
    const scores: any = {};
    
    // Methodology quality from rating
    if (data?.methodology_quality_rating) {
      const methodologyScore = data.methodology_quality_rating.toLowerCase().includes('high') ? 90 :
                              data.methodology_quality_rating.toLowerCase().includes('medium') ? 70 : 50;
      scores.methodology = methodologyScore;
      totalScore += methodologyScore;
      count++;
      debugLog += `Methodology rating: ${data.methodology_quality_rating} -> ${methodologyScore}\n`;
    }
    
    // Reproducibility score
    if (data?.reproducibility_score !== undefined) {
      const reproScore = data.reproducibility_score * 100;
      scores.reproducibility = reproScore;
      totalScore += reproScore;
      count++;
      debugLog += `Reproducibility score: ${data.reproducibility_score} -> ${reproScore}\n`;
    }
    
    // Bias assessment (inverse - fewer biases = higher score)
    if (data?.detected_biases && Array.isArray(data.detected_biases)) {
      const biasScore = Math.max(0, 100 - (data.detected_biases.length * 20));
      scores.bias = biasScore;
      totalScore += biasScore;
      count++;
      debugLog += `Bias assessment: ${data.detected_biases.length} biases -> ${biasScore}\n`;
    }
    
    // Statistical concerns (inverse)
    if (data?.statistical_concerns && Array.isArray(data.statistical_concerns)) {
      const statsScore = Math.max(0, 100 - (data.statistical_concerns.length * 15));
      scores.statistics = statsScore;
      totalScore += statsScore;
      count++;
      debugLog += `Statistical concerns: ${data.statistical_concerns.length} concerns -> ${statsScore}\n`;
    }
    
    const overall = count > 0 ? totalScore / count : 50; // Default to 50 instead of 75
    debugLog += `Final calculation: ${totalScore} / ${count} = ${overall}\n`;
    debugLog += `Source: individual_metrics\n`;
    
    console.log('✅ Calculated from individual metrics:', { scores, overall, count });
    
    return {
      methodology: scores.methodology || overall,
      reproducibility: scores.reproducibility || overall,
      bias: scores.bias || overall,
      statistics: scores.statistics || overall,
      overall,
      source: 'individual_metrics'
    };
  };

  // Calculate score when data changes
  useEffect(() => {
    if (data) {
      const breakdown = calculateComprehensiveScore();
      setScoreBreakdown(breakdown);
      setDebugInfo(breakdown.source);
      console.log('🎯 Final score breakdown:', breakdown);
    }
  }, [data]);

  const score = scoreBreakdown?.overall || 0;
  const normalizedScore = Math.max(0, Math.min(100, score));
  
  // Calculate color based on score
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10B981'; // Green
    if (score >= 60) return '#F59E0B'; // Yellow
    if (score >= 40) return '#F97316'; // Orange
    return '#EF4444'; // Red
  };

  const getScoreLabel = (score: number) => {
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 55) return 'Fair';
    if (score >= 40) return 'Poor';
    return 'Very Poor';
  };

  const getScoreDescription = (score: number) => {
    if (score >= 85) return 'High quality research with strong methodology and minimal concerns';
    if (score >= 70) return 'Good quality research with some areas for improvement';
    if (score >= 55) return 'Fair quality research with notable limitations';
    if (score >= 40) return 'Poor quality research with significant concerns';
    return 'Very poor quality research with major methodological issues';
  };

  // Calculate the target color for the score
  const getTargetColor = (score: number) => {
    if (score >= 80) return '#10B981'; // Green
    if (score >= 60) return '#F59E0B'; // Yellow
    if (score >= 40) return '#F97316'; // Orange
    return '#EF4444'; // Red
  };

  // Create a dynamic gradient that starts red and transitions to the appropriate color
  const getScoreGradient = (score: number) => {
    const targetColor = getTargetColor(score);
    return `linear-gradient(to right, #EF4444 0%, ${targetColor} 100%)`;
  };

  // Debug display component
  const DebugInfo = () => {
    if (process.env.NODE_ENV === 'development') {
      return (
        <div className="mt-4 p-2 bg-gray-100 rounded text-xs">
          <div className="font-semibold">Debug Info:</div>
          <div>Score Source: {debugInfo}</div>
          <div>Raw Score: {score}</div>
          <div>Normalized: {normalizedScore}</div>
          {scoreBreakdown && (
            <div>
              Breakdown: M:{scoreBreakdown.methodology.toFixed(1)} 
              R:{scoreBreakdown.reproducibility.toFixed(1)} 
              B:{scoreBreakdown.bias.toFixed(1)} 
              S:{scoreBreakdown.statistics.toFixed(1)}
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`text-center ${className}`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Overall Quality Score</h3>
      
      {/* Score Source Indicator */}
      {debugInfo && (
        <div className="mb-2 text-xs text-gray-500">
          Source: {debugInfo.replace('_', ' ').toUpperCase()}
        </div>
      )}
      
      {/* Horizontal Progress Bar */}
      <div className="relative w-full max-w-md mx-auto">
        {/* Background bar */}
        <div className="w-full h-8 bg-gray-200 rounded-full overflow-hidden">
          {/* Progress bar with gradient */}
          <div 
            className="h-full transition-all duration-1000 ease-out rounded-full"
            style={{
              width: `${normalizedScore}%`,
              background: getScoreGradient(normalizedScore)
            }}
          />
        </div>
        
        {/* Score display */}
        <div className="mt-4">
          <div className="text-3xl font-bold text-gray-800">
            {Math.round(normalizedScore)}
          </div>
        </div>
      </div>
      
      {/* Score details */}
      <div className="mt-4 space-y-2">
        <div className={`text-lg font-semibold ${getScoreColor(normalizedScore) ? 'text-gray-800' : 'text-gray-600'}`}>
          {getScoreLabel(normalizedScore)}
        </div>
        <div className="text-sm text-gray-600 max-w-xs mx-auto">
          {getScoreDescription(normalizedScore)}
        </div>
      </div>
      
      {/* Score Breakdown (if available) */}
      {scoreBreakdown && scoreBreakdown.source !== 'direct_backend_score' && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <div className="text-sm font-semibold text-gray-700 mb-2">Score Breakdown</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span>Methodology:</span>
              <span className="font-semibold">{Math.round(scoreBreakdown.methodology)}</span>
            </div>
            <div className="flex justify-between">
              <span>Reproducibility:</span>
              <span className="font-semibold">{Math.round(scoreBreakdown.reproducibility)}</span>
            </div>
            <div className="flex justify-between">
              <span>Bias:</span>
              <span className="font-semibold">{Math.round(scoreBreakdown.bias)}</span>
            </div>
            <div className="flex justify-between">
              <span>Statistics:</span>
              <span className="font-semibold">{Math.round(scoreBreakdown.statistics)}</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Additional metrics */}
      <div className="mt-6 grid grid-cols-2 gap-4 text-xs">
        {data?.tools_used && (
          <div className="bg-blue-50 p-2 rounded">
            <div className="font-semibold text-blue-800">{data.tools_used.length}</div>
            <div className="text-blue-600">Tools Used</div>
          </div>
        )}
        
        {data?.reproducibility_score !== undefined && (
          <div className="bg-green-50 p-2 rounded">
            <div className="font-semibold text-green-800">
              {Math.round(data.reproducibility_score * 100)}%
            </div>
            <div className="text-green-600">Reproducible</div>
          </div>
        )}
        
        {data?.detected_biases && (
          <div className="bg-red-50 p-2 rounded">
            <div className="font-semibold text-red-800">{data.detected_biases.length}</div>
            <div className="text-red-600">Biases Found</div>
          </div>
        )}
        
        {data?.research_gaps && (
          <div className="bg-yellow-50 p-2 rounded">
            <div className="font-semibold text-yellow-800">{data.research_gaps.length}</div>
            <div className="text-yellow-600">Research Gaps</div>
          </div>
        )}
      </div>
      
      {/* Debug Info (Development only) */}
      <DebugInfo />
    </div>
  );
}
