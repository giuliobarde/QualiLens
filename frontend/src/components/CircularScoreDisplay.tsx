'use client';

import React, { useEffect, useState, useRef } from 'react';
import { extractComponentScores, calculateOverallScore, RubricWeights, ComponentScores } from '@/utils/weight-calculator';
import RubricConfig, { RubricWeights as RubricWeightsType } from '@/components/RubricConfig';

interface CircularScoreDisplayProps {
  data: any;
  className?: string;
  isExpanded?: boolean;
  onWeightsChange?: (weights: RubricWeights) => void;
  customWeights?: RubricWeights;
}

interface ScoreBreakdown {
  methodology: number;
  reproducibility: number;
  bias: number;
  statistics: number;
  overall: number;
  source: string;
}

// Default weights matching RubricConfig
const DEFAULT_WEIGHTS: RubricWeights = {
  methodology: 0.60,
  bias: 0.20,
  reproducibility: 0.10,
  research_gaps: 0.10,
};

export default function CircularScoreDisplay({ 
  data, 
  className = '', 
  isExpanded = false,
  onWeightsChange,
  customWeights
}: CircularScoreDisplayProps) {
  const [scoreBreakdown, setScoreBreakdown] = useState<ScoreBreakdown | null>(null);
  const [animatedScore, setAnimatedScore] = useState(0);
  const hasAnimatedRef = useRef(false);
  const lastAnimatedScoreRef = useRef<number | null>(null);
  const [isEditingWeights, setIsEditingWeights] = useState(false);
  const [activeTab, setActiveTab] = useState<'overall' | 'breakdown'>('overall');
  // Initialize with customWeights if provided, otherwise use default weights (not null)
  const [currentWeights, setCurrentWeights] = useState<RubricWeights>(customWeights || DEFAULT_WEIGHTS);

  // Comprehensive score calculation - now always uses component_scores from backend
  const calculateComprehensiveScore = (): ScoreBreakdown => {
    // Primary method: Extract component scores and calculate overall using weights
    const componentScores = extractComponentScores(data);
    if (componentScores) {
      // Calculate overall score using current weights (default or custom)
      const overall = calculateOverallScore(componentScores, currentWeights);
      return {
        methodology: componentScores.methodology,
        reproducibility: componentScores.reproducibility,
        bias: componentScores.bias,
        statistics: componentScores.methodology, // Use methodology for statistics display
        overall,
        source: 'component_scores'
      };
    }
    
    // Fallback: Try to extract from quality_breakdown (legacy support)
    if (data?.quality_breakdown) {
      const breakdown = data.quality_breakdown;
      const methodology = breakdown.methodology?.score || 0;
      const reproducibility = breakdown.reproducibility?.score || 0;
      const bias = breakdown.bias?.score || 0;
      const research_gaps = breakdown.research_gaps?.score || 0;
      
      const fallbackScores: ComponentScores = {
        methodology,
        reproducibility,
        bias,
        research_gaps
      };
      const overall = calculateOverallScore(fallbackScores, currentWeights);
      return {
        methodology,
        reproducibility,
        bias,
        statistics: methodology, // Use methodology for statistics display
        overall,
        source: 'quality_breakdown'
      };
    }
    
    // Last resort: Calculate from individual metrics (should rarely be needed)
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
      const reproScore = typeof data.reproducibility_score === 'number' 
        ? (data.reproducibility_score <= 1.0 ? data.reproducibility_score * 100 : data.reproducibility_score)
        : 0;
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
    
    // Research gaps fallback
    if (data?.research_gaps && Array.isArray(data.research_gaps)) {
      const gapsCount = data.research_gaps.length;
      let researchGapsScore = 0.0;
      if (gapsCount === 0) {
        researchGapsScore = 0.0;
      } else if (gapsCount <= 2) {
        researchGapsScore = 40.0;
      } else if (gapsCount <= 5) {
        researchGapsScore = 70.0;
      } else if (gapsCount <= 10) {
        researchGapsScore = 90.0;
      } else {
        researchGapsScore = 100.0;
      }
      scores.research_gaps = researchGapsScore;
      totalScore += researchGapsScore;
      count++;
    }
    
    // If we have component scores, calculate weighted overall
    if (count > 0 && (scores.methodology !== undefined || scores.reproducibility !== undefined || 
        scores.bias !== undefined || scores.research_gaps !== undefined)) {
      const fallbackComponentScores: ComponentScores = {
        methodology: scores.methodology || 0,
        reproducibility: scores.reproducibility || 0,
        bias: scores.bias || 0,
        research_gaps: scores.research_gaps || 0
      };
      const overall = calculateOverallScore(fallbackComponentScores, currentWeights);
      return {
        methodology: scores.methodology || overall,
        reproducibility: scores.reproducibility || overall,
        bias: scores.bias || overall,
        statistics: scores.methodology || overall,
        overall,
        source: 'individual_metrics'
      };
    }
    
    // Absolute fallback: return zeros
    return {
      methodology: 0,
      reproducibility: 0,
      bias: 0,
      statistics: 0,
      overall: 0,
      source: 'fallback'
    };
  };

  // Calculate score when data changes
  useEffect(() => {
    if (data) {
      // calculateComprehensiveScore now always calculates overall using currentWeights
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
  }, [data, currentWeights]);

  // Update weights when customWeights prop changes
  useEffect(() => {
    if (customWeights) {
      setCurrentWeights(customWeights);
    } else {
      // If customWeights is cleared, reset to defaults
      setCurrentWeights(DEFAULT_WEIGHTS);
    }
  }, [customWeights]);

  // Recalculate overall score when weights change (but scoreBreakdown already exists)
  // This handles the case where weights change after initial calculation
  useEffect(() => {
    if (scoreBreakdown && data) {
      // Recalculate using the comprehensive score function which uses currentWeights
      const newBreakdown = calculateComprehensiveScore();
      // Only update if the score actually changed (avoid unnecessary updates)
      if (Math.abs(newBreakdown.overall - scoreBreakdown.overall) > 0.01) {
        setAnimatedScore(newBreakdown.overall);
        setScoreBreakdown(newBreakdown);
      }
    }
    // Note: We intentionally don't include scoreBreakdown in deps to avoid infinite loops
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentWeights, data]);

  const score = scoreBreakdown?.overall || 0;
  const normalizedScore = Math.max(0, Math.min(100, animatedScore));

  // Handle weight editing
  const handleEditWeightsClick = () => {
    setIsEditingWeights(true);
  };

  const handleWeightsChange = (newWeights: RubricWeightsType) => {
    setCurrentWeights(newWeights);
    onWeightsChange?.(newWeights);
  };

  const handleWeightsEditCancel = () => {
    setIsEditingWeights(false);
    // Reset to original weights if available, otherwise use defaults
    if (customWeights) {
      setCurrentWeights(customWeights);
    } else {
      setCurrentWeights(DEFAULT_WEIGHTS);
    }
  };
  
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
        <div className="flex items-center justify-center space-x-2 mb-6">
          <h3 className="text-xl font-bold text-gray-800">Overall Quality Score</h3>
          {!isEditingWeights && (
            <button
              onClick={handleEditWeightsClick}
              className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
              title="Edit scoring weights"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          )}
          {isEditingWeights && (
            <button
              onClick={handleWeightsEditCancel}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
            >
              Done
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex space-x-0.5 mb-4 bg-gray-100 p-0.5 rounded-md">
          <button
            onClick={() => setActiveTab('overall')}
            className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
              activeTab === 'overall'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Overall Score
          </button>
          <button
            onClick={() => setActiveTab('breakdown')}
            className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
              activeTab === 'breakdown'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Score Breakdown
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'overall' ? (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
            {/* Main Score - Left Side */}
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

            {/* Right Side - Weight Editing or Additional Metrics */}
            {isEditingWeights ? (
              <div className="lg:col-span-3">
                <RubricConfig
                  initialWeights={currentWeights || undefined}
                  onWeightsChange={handleWeightsChange}
                  alwaysExpanded={true}
                />
              </div>
            ) : (
              <div className="lg:col-span-3">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {data?.tools_used && (
                    <div className="bg-blue-50 p-3 rounded-xl border border-blue-200 text-center">
                      <div className="font-bold text-blue-800 text-2xl">{data.tools_used.length}</div>
                      <div className="text-blue-600 text-xs mt-0.5">Tools Used</div>
                    </div>
                  )}
                  
                  {data?.reproducibility_score !== undefined && (
                    <div className="bg-green-50 p-3 rounded-xl border border-green-200 text-center">
                      <div className="font-bold text-green-800 text-2xl">
                        {Math.round(data.reproducibility_score <= 1.0 ? data.reproducibility_score * 100 : data.reproducibility_score)}%
                      </div>
                      <div className="text-green-600 text-xs mt-0.5">Reproducible</div>
                    </div>
                  )}
                  
                  {data?.detected_biases && (
                    <div className="bg-red-50 p-3 rounded-xl border border-red-200 text-center">
                      <div className="font-bold text-red-800 text-2xl">{data.detected_biases.length}</div>
                      <div className="text-red-600 text-xs mt-0.5">Biases Found</div>
                    </div>
                  )}
                  
                  {data?.research_gaps && (
                    <div className="bg-yellow-50 p-3 rounded-xl border border-yellow-200 text-center">
                      <div className="font-bold text-yellow-800 text-2xl">{data.research_gaps.length}</div>
                      <div className="text-yellow-600 text-xs mt-0.5">Research Gaps</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Score Breakdown Tab */
          scoreBreakdown && (
            <div className="space-y-4">
              <div className="text-sm font-semibold text-gray-700 mb-4">Component Scores</div>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl border border-blue-200">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Methodology</div>
                  <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.methodology) }}>
                    {Math.round(scoreBreakdown.methodology)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Weight: {(currentWeights.methodology * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Contribution: {(scoreBreakdown.methodology * currentWeights.methodology).toFixed(1)} pts
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl border border-green-200">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Reproducibility</div>
                  <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.reproducibility) }}>
                    {Math.round(scoreBreakdown.reproducibility)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Weight: {(currentWeights.reproducibility * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Contribution: {(scoreBreakdown.reproducibility * currentWeights.reproducibility).toFixed(1)} pts
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border border-red-200">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Bias</div>
                  <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.bias) }}>
                    {Math.round(scoreBreakdown.bias)}
                  </div>
                  <div className="text-xs text-gray-500">
                    Weight: {(currentWeights.bias * 100).toFixed(0)}%
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Contribution: {(scoreBreakdown.bias * currentWeights.bias).toFixed(1)} pts
                  </div>
                </div>
                
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl border border-purple-200">
                  <div className="text-gray-600 mb-2 text-sm font-medium">Research Gaps</div>
                  {(() => {
                    const componentScores = extractComponentScores(data);
                    const researchGapsScore = componentScores?.research_gaps || 0;
                    return (
                      <>
                        <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(researchGapsScore) }}>
                          {Math.round(researchGapsScore)}
                        </div>
                        <div className="text-xs text-gray-500">
                          Weight: {(currentWeights.research_gaps * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          Contribution: {(researchGapsScore * currentWeights.research_gaps).toFixed(1)} pts
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            </div>
          )
        )}
      </div>
    );
  }

  // Default vertical layout
  return (
    <div className={`text-center ${className}`}>
      {/* Weight Editing Mode - Show only rubric when editing */}
      {isEditingWeights ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Edit Scoring Weights</h3>
            <button
              onClick={handleWeightsEditCancel}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
            >
              Done
            </button>
          </div>
          <RubricConfig
            initialWeights={currentWeights || undefined}
            onWeightsChange={handleWeightsChange}
            alwaysExpanded={true}
          />
        </div>
      ) : (
        <>
          <div className="flex items-center justify-center space-x-2 mb-6">
            <h3 className="text-lg font-semibold text-gray-800">Overall Quality Score</h3>
            <button
              onClick={handleEditWeightsClick}
              className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
              title="Edit scoring weights"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex space-x-0.5 mb-4 bg-gray-100 p-0.5 rounded-md">
            <button
              onClick={() => setActiveTab('overall')}
              className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                activeTab === 'overall'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Overall Score
            </button>
            <button
              onClick={() => setActiveTab('breakdown')}
              className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                activeTab === 'breakdown'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Score Breakdown
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'overall' ? (
            <>
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
              
              {/* Additional metrics */}
              <div className="mt-6 grid grid-cols-2 gap-3 text-xs">
                {data?.tools_used && (
                  <div className="bg-blue-50 p-2 rounded-xl border border-blue-200">
                    <div className="font-bold text-blue-800 text-base">{data.tools_used.length}</div>
                    <div className="text-blue-600">Tools Used</div>
                  </div>
                )}
                
                {data?.reproducibility_score !== undefined && (
                  <div className="bg-green-50 p-2 rounded-xl border border-green-200">
                    <div className="font-bold text-green-800 text-base">
                      {Math.round(data.reproducibility_score <= 1.0 ? data.reproducibility_score * 100 : data.reproducibility_score)}%
                    </div>
                    <div className="text-green-600">Reproducible</div>
                  </div>
                )}
                
                {data?.detected_biases && (
                  <div className="bg-red-50 p-2 rounded-xl border border-red-200">
                    <div className="font-bold text-red-800 text-base">{data.detected_biases.length}</div>
                    <div className="text-red-600">Biases Found</div>
                  </div>
                )}
                
                {data?.research_gaps && (
                  <div className="bg-yellow-50 p-2 rounded-xl border border-yellow-200">
                    <div className="font-bold text-yellow-800 text-base">{data.research_gaps.length}</div>
                    <div className="text-yellow-600">Research Gaps</div>
                  </div>
                )}
              </div>
            </>
          ) : (
            /* Score Breakdown Tab */
            scoreBreakdown && (
              <div className="space-y-4">
                <div className="text-sm font-semibold text-gray-700 mb-4">Component Scores</div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl border border-blue-200">
                    <div className="text-gray-600 mb-2 text-sm font-medium">Methodology</div>
                    <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.methodology) }}>
                      {Math.round(scoreBreakdown.methodology)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Weight: {(currentWeights.methodology * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Contribution: {(scoreBreakdown.methodology * currentWeights.methodology).toFixed(1)} pts
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl border border-green-200">
                    <div className="text-gray-600 mb-2 text-sm font-medium">Reproducibility</div>
                    <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.reproducibility) }}>
                      {Math.round(scoreBreakdown.reproducibility)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Weight: {(currentWeights.reproducibility * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Contribution: {(scoreBreakdown.reproducibility * currentWeights.reproducibility).toFixed(1)} pts
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-red-50 to-red-100 p-4 rounded-xl border border-red-200">
                    <div className="text-gray-600 mb-2 text-sm font-medium">Bias</div>
                    <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(scoreBreakdown.bias) }}>
                      {Math.round(scoreBreakdown.bias)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Weight: {(currentWeights.bias * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Contribution: {(scoreBreakdown.bias * currentWeights.bias).toFixed(1)} pts
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl border border-purple-200">
                    <div className="text-gray-600 mb-2 text-sm font-medium">Research Gaps</div>
                    {(() => {
                      const componentScores = extractComponentScores(data);
                      const researchGapsScore = componentScores?.research_gaps || 0;
                      return (
                        <>
                          <div className="text-3xl font-bold mb-2" style={{ color: getScoreColor(researchGapsScore) }}>
                            {Math.round(researchGapsScore)}
                          </div>
                          <div className="text-xs text-gray-500">
                            Weight: {(currentWeights.research_gaps * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            Contribution: {(researchGapsScore * currentWeights.research_gaps).toFixed(1)} pts
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
