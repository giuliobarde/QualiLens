'use client';

import React from 'react';

interface QualityScoreDisplayProps {
  data: any;
  className?: string;
}

export default function QualityScoreDisplay({ data, className = '' }: QualityScoreDisplayProps) {
  // Calculate overall quality score
  const getOverallScore = () => {
    if (data?.overall_quality_score !== undefined) {
      return data.overall_quality_score;
    }
    
    // Calculate from various metrics if available
    let totalScore = 0;
    let count = 0;
    
    // Methodology quality
    if (data?.methodology_quality_rating) {
      const methodologyScore = data.methodology_quality_rating.toLowerCase().includes('high') ? 90 :
                              data.methodology_quality_rating.toLowerCase().includes('medium') ? 70 : 50;
      totalScore += methodologyScore;
      count++;
    }
    
    // Reproducibility score
    if (data?.reproducibility_score !== undefined) {
      totalScore += data.reproducibility_score * 100;
      count++;
    }
    
    // Bias assessment (inverse - fewer biases = higher score)
    if (data?.detected_biases && Array.isArray(data.detected_biases)) {
      const biasScore = Math.max(0, 100 - (data.detected_biases.length * 20));
      totalScore += biasScore;
      count++;
    }
    
    // Statistical concerns (inverse)
    if (data?.statistical_concerns && Array.isArray(data.statistical_concerns)) {
      const statsScore = Math.max(0, 100 - (data.statistical_concerns.length * 15));
      totalScore += statsScore;
      count++;
    }
    
    return count > 0 ? totalScore / count : 75; // Default to 75 if no data
  };

  const score = getOverallScore();
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

  return (
    <div className={`text-center ${className}`}>
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Overall Quality Score</h3>
      
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
    </div>
  );
}
