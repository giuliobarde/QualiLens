'use client';

import React, { useState, useEffect } from 'react';

export interface RubricWeights {
  methodology: number;
  bias: number;
  reproducibility: number;
  research_gaps: number;
}

interface RubricConfigProps {
  initialWeights?: RubricWeights;
  onWeightsChange?: (weights: RubricWeights) => void;
  className?: string;
  alwaysExpanded?: boolean;
}

const DEFAULT_WEIGHTS: RubricWeights = {
  methodology: 0.60,
  bias: 0.20,
  reproducibility: 0.10,
  research_gaps: 0.10,
};

export default function RubricConfig({ 
  initialWeights, 
  onWeightsChange,
  className = '',
  alwaysExpanded = false
}: RubricConfigProps) {
  const [weights, setWeights] = useState<RubricWeights>(
    initialWeights || { ...DEFAULT_WEIGHTS }
  );
  const [isExpanded, setIsExpanded] = useState(alwaysExpanded);

  useEffect(() => {
    if (initialWeights) {
      setWeights(initialWeights);
    }
  }, [initialWeights]);

  useEffect(() => {
    if (alwaysExpanded) {
      setIsExpanded(true);
    }
  }, [alwaysExpanded]);

  const updateWeight = (key: keyof RubricWeights, value: number) => {
    const newWeights = { ...weights, [key]: value };
    
    // Normalize weights to sum to 1.0
    const sum = Object.values(newWeights).reduce((a, b) => a + b, 0);
    if (sum > 0) {
      const normalized: RubricWeights = {
        methodology: newWeights.methodology / sum,
        bias: newWeights.bias / sum,
        reproducibility: newWeights.reproducibility / sum,
        research_gaps: newWeights.research_gaps / sum,
      };
      setWeights(normalized);
      onWeightsChange?.(normalized);
    }
  };

  const resetToDefaults = () => {
    // Check if weights are already at defaults (within small tolerance for floating point)
    const isAlreadyDefault = 
      Math.abs(weights.methodology - DEFAULT_WEIGHTS.methodology) < 0.001 &&
      Math.abs(weights.bias - DEFAULT_WEIGHTS.bias) < 0.001 &&
      Math.abs(weights.reproducibility - DEFAULT_WEIGHTS.reproducibility) < 0.001 &&
      Math.abs(weights.research_gaps - DEFAULT_WEIGHTS.research_gaps) < 0.001;
    
    if (!isAlreadyDefault) {
      setWeights({ ...DEFAULT_WEIGHTS });
      onWeightsChange?.(DEFAULT_WEIGHTS);
    }
    // If already at defaults, don't trigger a change (prevents unnecessary recalculation)
  };

  const total = Object.values(weights).reduce((a, b) => a + b, 0);
  const isNormalized = Math.abs(total - 1.0) < 0.001;

  return (
    <div className={`bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-200/50 shadow-md ${className}`}>
      {!alwaysExpanded && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50/50 transition-colors rounded-t-2xl"
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </div>
            <div className="text-left">
              <h3 className="text-lg font-semibold text-gray-800">Evaluation Rubric</h3>
              <p className="text-sm text-gray-600">Customize scoring weights</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {!isNormalized && (
              <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                Adjusting...
              </span>
            )}
            <svg 
              className={`w-5 h-5 text-gray-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </button>
      )}

      {(isExpanded || alwaysExpanded) && (
        <div className={`px-6 pb-6 ${alwaysExpanded ? 'pt-6' : 'pt-2'} space-y-4 ${!alwaysExpanded ? 'border-t border-gray-200' : ''}`}>
          {/* Methodology Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Methodology
              </label>
              <span className="text-sm font-bold text-blue-600">
                {(weights.methodology * 100).toFixed(1)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={weights.methodology}
              onChange={(e) => updateWeight('methodology', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Bias Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Bias Assessment
              </label>
              <span className="text-sm font-bold text-red-600">
                {(weights.bias * 100).toFixed(1)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={weights.bias}
              onChange={(e) => updateWeight('bias', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-red-600"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Reproducibility Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Reproducibility
              </label>
              <span className="text-sm font-bold text-green-600">
                {(weights.reproducibility * 100).toFixed(1)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={weights.reproducibility}
              onChange={(e) => updateWeight('reproducibility', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-green-600"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Research Gaps Weight */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Research Gaps
              </label>
              <span className="text-sm font-bold text-purple-600">
                {(weights.research_gaps * 100).toFixed(1)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={weights.research_gaps}
              onChange={(e) => updateWeight('research_gaps', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Total and Reset */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Total:</span>
              <span className={`text-sm font-bold ${isNormalized ? 'text-green-600' : 'text-yellow-600'}`}>
                {(total * 100).toFixed(1)}%
              </span>
            </div>
            <button
              onClick={resetToDefaults}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Reset to Defaults
            </button>
          </div>

        </div>
      )}
    </div>
  );
}

