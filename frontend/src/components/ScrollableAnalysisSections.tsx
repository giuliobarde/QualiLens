'use client';

import React, { useState } from 'react';
import ErrorBoundary from './ErrorBoundary';
import SafeRenderer from './SafeRenderer';

interface ScrollableAnalysisSectionsProps {
  data: any;
  className?: string;
}

export default function ScrollableAnalysisSections({ data, className = '' }: ScrollableAnalysisSectionsProps) {
  const [activeSection, setActiveSection] = useState('summary');

  const sections = [
    { id: 'summary', label: 'Summary', icon: '📝', color: 'blue' },
    { id: 'methodology', label: 'Methodology', icon: '🔬', color: 'green' },
    { id: 'bias', label: 'Bias Analysis', icon: '⚠️', color: 'red' },
    { id: 'statistics', label: 'Statistics', icon: '📈', color: 'purple' },
    { id: 'reproducibility', label: 'Reproducibility', icon: '🔄', color: 'indigo' },
    { id: 'gaps', label: 'Research Gaps', icon: '🔍', color: 'yellow' },
    { id: 'citations', label: 'Citations', icon: '📚', color: 'pink' },
  ];

  const getColorClasses = (color: string, isActive: boolean) => {
    const colorMap = {
      blue: isActive ? 'bg-blue-100 text-blue-800 border-blue-200' : 'text-blue-600 hover:bg-blue-50',
      green: isActive ? 'bg-green-100 text-green-800 border-green-200' : 'text-green-600 hover:bg-green-50',
      red: isActive ? 'bg-red-100 text-red-800 border-red-200' : 'text-red-600 hover:bg-red-50',
      purple: isActive ? 'bg-purple-100 text-purple-800 border-purple-200' : 'text-purple-600 hover:bg-purple-50',
      indigo: isActive ? 'bg-indigo-100 text-indigo-800 border-indigo-200' : 'text-indigo-600 hover:bg-indigo-50',
      yellow: isActive ? 'bg-yellow-100 text-yellow-800 border-yellow-200' : 'text-yellow-600 hover:bg-yellow-50',
      pink: isActive ? 'bg-pink-100 text-pink-800 border-pink-200' : 'text-pink-600 hover:bg-pink-50',
    };
    return colorMap[color as keyof typeof colorMap] || 'text-gray-600 hover:bg-gray-50';
  };

  const renderSummary = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.executive_summary && (
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
            <h4 className="font-semibold text-blue-800 mb-2">Executive Summary</h4>
            <SafeRenderer data={data.executive_summary} className="text-sm text-blue-700" />
          </div>
        )}
        
        {data?.key_points && Array.isArray(data.key_points) && data.key_points.length > 0 && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Key Points</h4>
            <ul className="space-y-1">
              {data.key_points.slice(0, 3).map((point: any, index: number) => (
                <li key={index} className="text-sm text-gray-600 flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  <SafeRenderer data={point} />
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data?.summary && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Detailed Summary</h4>
            <SafeRenderer data={data.summary} className="text-sm text-gray-600 line-clamp-4" />
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderMethodology = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.study_design && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Study Design</h4>
            <SafeRenderer data={data.study_design} className="text-sm text-gray-600" />
          </div>
        )}
        
        {data?.methodological_strengths && Array.isArray(data.methodological_strengths) && data.methodological_strengths.length > 0 && (
          <div>
            <h4 className="font-semibold text-green-800 mb-2">Strengths</h4>
            <ul className="space-y-1">
              {data.methodological_strengths.slice(0, 3).map((strength: any, index: number) => (
                <li key={index} className="text-sm text-green-700 flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <SafeRenderer data={strength} />
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data?.methodological_weaknesses && Array.isArray(data.methodological_weaknesses) && data.methodological_weaknesses.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">Weaknesses</h4>
            <ul className="space-y-1">
              {data.methodological_weaknesses.slice(0, 3).map((weakness: any, index: number) => (
                <li key={index} className="text-sm text-red-700 flex items-start">
                  <span className="text-red-500 mr-2">⚠</span>
                  <SafeRenderer data={weakness} />
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data?.methodology_quality_rating && (
          <div className="bg-gray-50 p-3 rounded">
            <h4 className="font-semibold text-gray-800 mb-1">Quality Rating</h4>
            <span className={`px-2 py-1 text-xs rounded ${
              String(data.methodology_quality_rating).toLowerCase().includes('high') ? 'bg-green-100 text-green-800' :
              String(data.methodology_quality_rating).toLowerCase().includes('medium') ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              <SafeRenderer data={data.methodology_quality_rating} />
            </span>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderBiasAnalysis = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.bias_summary && (
          <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-400">
            <h4 className="font-semibold text-yellow-800 mb-2">Bias Assessment</h4>
            <SafeRenderer data={data.bias_summary} className="text-sm text-yellow-700" />
          </div>
        )}
        
        {data?.detected_biases && Array.isArray(data.detected_biases) && data.detected_biases.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">Detected Biases ({data.detected_biases.length})</h4>
            <div className="space-y-2">
              {data.detected_biases.slice(0, 3).map((bias: any, index: number) => (
                <div key={index} className="bg-red-50 p-3 rounded border border-red-200">
                  <SafeRenderer data={bias} className="text-sm text-red-700" />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {data?.limitations && Array.isArray(data.limitations) && data.limitations.length > 0 && (
          <div>
            <h4 className="font-semibold text-orange-800 mb-2">Limitations</h4>
            <ul className="space-y-1">
              {data.limitations.slice(0, 3).map((limitation: any, index: number) => (
                <li key={index} className="text-sm text-orange-700 flex items-start">
                  <span className="text-orange-500 mr-2">⚠</span>
                  <SafeRenderer data={limitation} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderStatistics = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.statistical_tests_used && Array.isArray(data.statistical_tests_used) && data.statistical_tests_used.length > 0 && (
          <div>
            <h4 className="font-semibold text-purple-800 mb-2">Statistical Tests</h4>
            <div className="space-y-2">
              {data.statistical_tests_used.slice(0, 3).map((test: any, index: number) => (
                <div key={index} className="bg-purple-50 p-3 rounded">
                  <SafeRenderer data={test} className="text-sm text-purple-700" />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {data?.statistical_concerns && Array.isArray(data.statistical_concerns) && data.statistical_concerns.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">Statistical Concerns ({data.statistical_concerns.length})</h4>
            <div className="space-y-2">
              {data.statistical_concerns.slice(0, 2).map((concern: any, index: number) => (
                <div key={index} className="bg-red-50 p-3 rounded border border-red-200">
                  <SafeRenderer data={concern} className="text-sm text-red-700" />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {data?.statistical_recommendations && Array.isArray(data.statistical_recommendations) && data.statistical_recommendations.length > 0 && (
          <div>
            <h4 className="font-semibold text-green-800 mb-2">Recommendations</h4>
            <ul className="space-y-1">
              {data.statistical_recommendations.slice(0, 3).map((rec: any, index: number) => (
                <li key={index} className="text-sm text-green-700 flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <SafeRenderer data={rec} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderReproducibility = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.reproducibility_score !== undefined && (
          <div className="bg-indigo-50 p-4 rounded-lg">
            <h4 className="font-semibold text-indigo-800 mb-2">Reproducibility Score</h4>
            <div className="flex items-center space-x-3">
              <div className="text-2xl font-bold text-indigo-600">
                {Math.round(data.reproducibility_score * 100)}%
              </div>
              <div className="flex-1">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      data.reproducibility_score >= 0.8 ? 'bg-green-500' :
                      data.reproducibility_score >= 0.6 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${data.reproducibility_score * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {data?.data_availability && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Data Availability</h4>
            <SafeRenderer data={data.data_availability} className="text-sm text-gray-600" />
          </div>
        )}
        
        {data?.code_availability && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Code Availability</h4>
            <SafeRenderer data={data.code_availability} className="text-sm text-gray-600" />
          </div>
        )}
        
        {data?.reproducibility_barriers && Array.isArray(data.reproducibility_barriers) && data.reproducibility_barriers.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">Barriers ({data.reproducibility_barriers.length})</h4>
            <ul className="space-y-1">
              {data.reproducibility_barriers.slice(0, 3).map((barrier: any, index: number) => (
                <li key={index} className="text-sm text-red-700 flex items-start">
                  <span className="text-red-500 mr-2">⚠</span>
                  <SafeRenderer data={barrier} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderGaps = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        {data?.research_gaps && Array.isArray(data.research_gaps) && data.research_gaps.length > 0 && (
          <div>
            <h4 className="font-semibold text-yellow-800 mb-2">Research Gaps ({data.research_gaps.length})</h4>
            <div className="space-y-2">
              {data.research_gaps.slice(0, 3).map((gap: any, index: number) => (
                <div key={index} className="bg-yellow-50 p-3 rounded border border-yellow-200">
                  <SafeRenderer data={gap} className="text-sm text-yellow-700" />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {data?.future_directions && Array.isArray(data.future_directions) && data.future_directions.length > 0 && (
          <div>
            <h4 className="font-semibold text-green-800 mb-2">Future Directions</h4>
            <ul className="space-y-1">
              {data.future_directions.slice(0, 3).map((direction: any, index: number) => (
                <li key={index} className="text-sm text-green-700 flex items-start">
                  <span className="text-green-500 mr-2">→</span>
                  <SafeRenderer data={direction} />
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {data?.unaddressed_questions && Array.isArray(data.unaddressed_questions) && data.unaddressed_questions.length > 0 && (
          <div>
            <h4 className="font-semibold text-blue-800 mb-2">Unaddressed Questions</h4>
            <ul className="space-y-1">
              {data.unaddressed_questions.slice(0, 3).map((question: any, index: number) => (
                <li key={index} className="text-sm text-blue-700 flex items-start">
                  <span className="text-blue-500 mr-2">?</span>
                  <SafeRenderer data={question} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderCitations = () => (
    <ErrorBoundary>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-blue-50 p-3 rounded text-center">
            <div className="text-lg font-bold text-blue-600">{data?.total_citations || 0}</div>
            <div className="text-xs text-blue-600">Total Citations</div>
          </div>
          <div className="bg-green-50 p-3 rounded text-center">
            <div className="text-lg font-bold text-green-600">
              {data?.citation_quality ? 'High' : 'Unknown'}
            </div>
            <div className="text-xs text-green-600">Quality</div>
          </div>
        </div>
        
        {data?.citation_gaps && Array.isArray(data.citation_gaps) && data.citation_gaps.length > 0 && (
          <div>
            <h4 className="font-semibold text-red-800 mb-2">Citation Gaps ({data.citation_gaps.length})</h4>
            <div className="space-y-2">
              {data.citation_gaps.slice(0, 3).map((gap: any, index: number) => (
                <div key={index} className="bg-red-50 p-3 rounded border border-red-200">
                  <SafeRenderer data={gap} className="text-sm text-red-700" />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {data?.bibliometric_indicators && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Bibliometric Indicators</h4>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(data.bibliometric_indicators).slice(0, 4).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-2 rounded text-center">
                  <div className="text-sm font-semibold text-gray-800">
                    <SafeRenderer data={value} />
                  </div>
                  <div className="text-xs text-gray-600 capitalize">{key.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'summary':
        return renderSummary();
      case 'methodology':
        return renderMethodology();
      case 'bias':
        return renderBiasAnalysis();
      case 'statistics':
        return renderStatistics();
      case 'reproducibility':
        return renderReproducibility();
      case 'gaps':
        return renderGaps();
      case 'citations':
        return renderCitations();
      default:
        return renderSummary();
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Enhanced Section Navigation */}
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200 p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
          <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Analysis Sections
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`p-3 rounded-xl text-xs font-semibold transition-all border-2 transform hover:scale-105 ${
                activeSection === section.id 
                  ? getColorClasses(section.color, true) + ' shadow-md scale-105'
                  : getColorClasses(section.color, false) + ' border-transparent hover:border-gray-300'
              }`}
            >
              <span className="mr-1.5 text-base">{section.icon}</span>
              {section.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Enhanced Section Content */}
      <div className="flex-1 overflow-y-auto p-6 analysis-scroll">
        <div className="animate-fade-in">
          {renderSectionContent()}
        </div>
      </div>
    </div>
  );
}