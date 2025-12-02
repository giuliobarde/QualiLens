'use client';

import React, { useEffect, useState, useRef } from 'react';

interface CircularScoreDisplayProps {
  data: any;
  className?: string;
  isExpanded?: boolean;
}

interface ScoreBreakdown {
  methodology: number;
  reproducibility: number;
  bias: number;
  statistics: number;
  overall: number;
  source: string;
}

export default function CircularScoreDisplay({ data, className = '', isExpanded = false }: CircularScoreDisplayProps) {
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdown | null>(null);
  const [animatedScore, setAnimatedScore] = useState(0);
  const hasAnimatedRef = useRef(false);
  const lastAnimatedScoreRef = useRef<number | null>(null);

  // Comprehensive score calculation
  const calculateComprehensiveScore = (): ScoreBreakdown => {
    // Method 1: Direct overall_quality_score from backend
    if (data?.overall_quality_score !== undefined && data?.overall_quality_score !== null) {
      const directScore = Number(data.overall_quality_score);
      
      // Check if this is a suspiciously low score (likely from quality assessor override)
      if (directScore < 50 && data?.quantitative_scores?.scores?.overall_score > directScore) {
        const methodologyScore = data.quantitative_scores.scores.overall_score;
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
      const breakdown = data.quality_breakdown;
      const methodology = breakdown.methodology?.score || 0;
      const reproducibility = breakdown.reproducibility?.score || 0;
      const bias = breakdown.bias?.score || 0;
      const statistics = breakdown.statistics?.score || 0;
      
      const overall = (methodology + reproducibility + bias + statistics) / 4;
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
      const scores = data.quantitative_scores.scores;
      const overall = scores.overall_score || 0;
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
    let totalScore = 0;
    let count = 0;
    const scores: any = {};
    
    if (data?.methodology_quality_rating) {
      const methodologyScore = data.methodology_quality_rating.toLowerCase().includes('high') ? 90 :
                              data.methodology_quality_rating.toLowerCase().includes('medium') ? 70 : 50;
      scores.methodology = methodologyScore;
      totalScore += methodologyScore;
      count++;
    }
    
    if (data?.reproducibility_score !== undefined) {
      const reproScore = data.reproducibility_score * 100;
      scores.reproducibility = reproScore;
      totalScore += reproScore;
      count++;
    }
    
    if (data?.detected_biases && Array.isArray(data.detected_biases)) {
      const biasScore = Math.max(0, 100 - (data.detected_biases.length * 20));
      scores.bias = biasScore;
      totalScore += biasScore;
      count++;
    }
    
    if (data?.statistical_concerns && Array.isArray(data.statistical_concerns)) {
      const statsScore = Math.max(0, 100 - (data.statistical_concerns.length * 15));
      scores.statistics = statsScore;
      totalScore += statsScore;
      count++;
    }
    
    const overall = count > 0 ? totalScore / count : 50;
    
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
      
      // Check if this is new data (different score) or just a re-render (same score)
      const isNewData = lastAnimatedScoreRef.current === null || 
                        lastAnimatedScoreRef.current !== breakdown.overall;
      
      if (isNewData) {
        // This is new data - reset animation flag and animate
        hasAnimatedRef.current = false;
        lastAnimatedScoreRef.current = breakdown.overall;
        
        const targetScore = breakdown.overall;
        const duration = 1500;
        const steps = 60;
        const increment = targetScore / steps;
        let current = 0;
        
        const timer = setInterval(() => {
          current += increment;
          if (current >= targetScore) {
            setAnimatedScore(targetScore);
            clearInterval(timer);
            hasAnimatedRef.current = true;
          } else {
            setAnimatedScore(current);
          }
        }, duration / steps);
        
        return () => clearInterval(timer);
      } else {
        // Same data, just a re-render (like when isExpanded changes) - set score directly without animation
        setAnimatedScore(breakdown.overall);
      }
    }
  }, [data]);

  const score = scoreBreakdown?.overall || 0;
  const normalizedScore = Math.max(0, Math.min(100, animatedScore));
  
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

  // Calculate circumference for circular progress
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (normalizedScore / 100) * circumference;

  if (isExpanded) {
    // Horizontal spread layout for expanded view
    return (
      <div className={`${className}`}>
        <h3 className="text-xl font-bold text-gray-800 mb-6 text-center">Overall Quality Score</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
          {/* Main Score - Center */}
          <div className="lg:col-span-2 flex flex-col items-center">
            <div className="relative w-40 h-40 mx-auto mb-4">
              <svg className="transform -rotate-90 w-40 h-40">
                <circle
                  cx="80"
                  cy="80"
                  r={radius * 0.8}
                  stroke="#E5E7EB"
                  strokeWidth="10"
                  fill="none"
                />
                <circle
                  cx="80"
                  cy="80"
                  r={radius * 0.8}
                  stroke={getScoreColor(normalizedScore)}
                  strokeWidth="10"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={circumference * 0.8}
                  strokeDashoffset={offset * 0.8}
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-4xl font-bold" style={{ color: getScoreColor(normalizedScore) }}>
                  {Math.round(normalizedScore)}
                </div>
                <div className="text-xs text-gray-500 mt-1">out of 100</div>
              </div>
            </div>
            <div className={`text-lg font-bold mb-2`} style={{ color: getScoreColor(normalizedScore) }}>
              {getScoreLabel(normalizedScore)}
            </div>
            <div className="text-sm text-gray-600 text-center max-w-xs">
              {getScoreDescription(normalizedScore)}
            </div>
          </div>

          {/* Score Breakdown - Right Side */}
          {scoreBreakdown && scoreBreakdown.source !== 'direct_backend_score' ? (
            <div className="lg:col-span-3">
              <div className="text-sm font-semibold text-gray-700 mb-4">Score Breakdown</div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl border border-blue-200 text-center">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Methodology</div>
                  <div className="text-3xl font-bold" style={{ color: getScoreColor(scoreBreakdown.methodology) }}>
                    {Math.round(scoreBreakdown.methodology)}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl border border-green-200 text-center">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Reproducibility</div>
                  <div className="text-3xl font-bold" style={{ color: getScoreColor(scoreBreakdown.reproducibility) }}>
                    {Math.round(scoreBreakdown.reproducibility)}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border border-red-200 text-center">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Bias</div>
                  <div className="text-3xl font-bold" style={{ color: getScoreColor(scoreBreakdown.bias) }}>
                    {Math.round(scoreBreakdown.bias)}
                  </div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl border border-purple-200 text-center">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Statistics</div>
                  <div className="text-3xl font-bold" style={{ color: getScoreColor(scoreBreakdown.statistics) }}>
                    {Math.round(scoreBreakdown.statistics)}
                  </div>
                </div>
              </div>
              
              {/* Additional metrics - Below breakdown */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                {data?.tools_used && (
                  <div className="bg-blue-50 p-3 rounded-xl border border-blue-200 text-center">
                    <div className="font-bold text-blue-800 text-2xl">{data.tools_used.length}</div>
                    <div className="text-blue-600 text-sm">Tools Used</div>
                  </div>
                )}
                
                {data?.reproducibility_score !== undefined && (
                  <div className="bg-green-50 p-3 rounded-xl border border-green-200 text-center">
                    <div className="font-bold text-green-800 text-2xl">
                      {Math.round(data.reproducibility_score * 100)}%
                    </div>
                    <div className="text-green-600 text-sm">Reproducible</div>
                  </div>
                )}
                
                {data?.detected_biases && (
                  <div className="bg-red-50 p-3 rounded-xl border border-red-200 text-center">
                    <div className="font-bold text-red-800 text-2xl">{data.detected_biases.length}</div>
                    <div className="text-red-600 text-sm">Biases Found</div>
                  </div>
                )}
                
                {data?.research_gaps && (
                  <div className="bg-yellow-50 p-3 rounded-xl border border-yellow-200 text-center">
                    <div className="font-bold text-yellow-800 text-2xl">{data.research_gaps.length}</div>
                    <div className="text-yellow-600 text-sm">Research Gaps</div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="lg:col-span-3">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {data?.tools_used && (
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-200 text-center">
                    <div className="font-bold text-blue-800 text-3xl">{data.tools_used.length}</div>
                    <div className="text-blue-600 text-sm mt-1">Tools Used</div>
                  </div>
                )}
                
                {data?.reproducibility_score !== undefined && (
                  <div className="bg-green-50 p-4 rounded-xl border border-green-200 text-center">
                    <div className="font-bold text-green-800 text-3xl">
                      {Math.round(data.reproducibility_score * 100)}%
                    </div>
                    <div className="text-green-600 text-sm mt-1">Reproducible</div>
                  </div>
                )}
                
                {data?.detected_biases && (
                  <div className="bg-red-50 p-4 rounded-xl border border-red-200 text-center">
                    <div className="font-bold text-red-800 text-3xl">{data.detected_biases.length}</div>
                    <div className="text-red-600 text-sm mt-1">Biases Found</div>
                  </div>
                )}
                
                {data?.research_gaps && (
                  <div className="bg-yellow-50 p-4 rounded-xl border border-yellow-200 text-center">
                    <div className="font-bold text-yellow-800 text-3xl">{data.research_gaps.length}</div>
                    <div className="text-yellow-600 text-sm mt-1">Research Gaps</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Default vertical layout
  return (
    <div className={`text-center ${className}`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-6">Overall Quality Score</h3>
      
      {/* Circular Progress */}
      <div className="relative w-48 h-48 mx-auto mb-6">
        <svg className="transform -rotate-90 w-48 h-48">
          {/* Background circle */}
          <circle
            cx="96"
            cy="96"
            r={radius}
            stroke="#E5E7EB"
            strokeWidth="12"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="96"
            cy="96"
            r={radius}
            stroke={getScoreColor(normalizedScore)}
            strokeWidth="12"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Score text in center */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-5xl font-bold" style={{ color: getScoreColor(normalizedScore) }}>
            {Math.round(normalizedScore)}
          </div>
          <div className="text-xs text-gray-500 mt-1">out of 100</div>
        </div>
      </div>
      
      {/* Score details */}
      <div className="space-y-3 mb-6">
        <div className={`text-xl font-bold`} style={{ color: getScoreColor(normalizedScore) }}>
          {getScoreLabel(normalizedScore)}
        </div>
        <div className="text-sm text-gray-600 max-w-xs mx-auto">
          {getScoreDescription(normalizedScore)}
        </div>
      </div>
      
      {/* Score Breakdown */}
      {scoreBreakdown && scoreBreakdown.source !== 'direct_backend_score' && (
        <div className="mt-6 p-4 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border border-gray-200">
          <div className="text-sm font-semibold text-gray-700 mb-3">Score Breakdown</div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-white p-2 rounded-lg">
              <div className="text-gray-600 mb-1">Methodology</div>
              <div className="text-lg font-bold" style={{ color: getScoreColor(scoreBreakdown.methodology) }}>
                {Math.round(scoreBreakdown.methodology)}
              </div>
            </div>
            <div className="bg-white p-2 rounded-lg">
              <div className="text-gray-600 mb-1">Reproducibility</div>
              <div className="text-lg font-bold" style={{ color: getScoreColor(scoreBreakdown.reproducibility) }}>
                {Math.round(scoreBreakdown.reproducibility)}
              </div>
            </div>
            <div className="bg-white p-2 rounded-lg">
              <div className="text-gray-600 mb-1">Bias</div>
              <div className="text-lg font-bold" style={{ color: getScoreColor(scoreBreakdown.bias) }}>
                {Math.round(scoreBreakdown.bias)}
              </div>
            </div>
            <div className="bg-white p-2 rounded-lg">
              <div className="text-gray-600 mb-1">Statistics</div>
              <div className="text-lg font-bold" style={{ color: getScoreColor(scoreBreakdown.statistics) }}>
                {Math.round(scoreBreakdown.statistics)}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Additional metrics */}
      <div className="mt-6 grid grid-cols-2 gap-3 text-xs">
        {data?.tools_used && (
          <div className="bg-blue-50 p-3 rounded-xl border border-blue-200">
            <div className="font-bold text-blue-800 text-lg">{data.tools_used.length}</div>
            <div className="text-blue-600">Tools Used</div>
          </div>
        )}
        
        {data?.reproducibility_score !== undefined && (
          <div className="bg-green-50 p-3 rounded-xl border border-green-200">
            <div className="font-bold text-green-800 text-lg">
              {Math.round(data.reproducibility_score * 100)}%
            </div>
            <div className="text-green-600">Reproducible</div>
          </div>
        )}
        
        {data?.detected_biases && (
          <div className="bg-red-50 p-3 rounded-xl border border-red-200">
            <div className="font-bold text-red-800 text-lg">{data.detected_biases.length}</div>
            <div className="text-red-600">Biases Found</div>
          </div>
        )}
        
        {data?.research_gaps && (
          <div className="bg-yellow-50 p-3 rounded-xl border border-yellow-200">
            <div className="font-bold text-yellow-800 text-lg">{data.research_gaps.length}</div>
            <div className="text-yellow-600">Research Gaps</div>
          </div>
        )}
      </div>
    </div>
  );
}
