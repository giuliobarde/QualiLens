'use client';

import React, { useState } from 'react';

interface AnalysisResult {
  success: boolean;
  analysis_level: string;
  tools_used: string[];
  query: string;
  text_length: number;
  analysis_timestamp: string;
  
  // Phase 1 Results
  executive_summary?: string;
  key_points?: string[];
  summary?: string;
  detected_biases?: any[];
  bias_summary?: string;
  limitations?: string[];
  confounding_factors?: string[];
  study_design?: string;
  sample_characteristics?: any;
  methodological_strengths?: string[];
  methodological_weaknesses?: string[];
  methodology_quality_rating?: string;
  
  // Phase 2 Results
  statistical_tests_used?: any[];
  test_appropriateness?: any;
  statistical_concerns?: any[];
  statistical_recommendations?: string[];
  reproducibility_score?: number;
  reproducibility_barriers?: any[];
  data_availability?: any;
  code_availability?: any;
  research_gaps?: any[];
  future_directions?: any[];
  unaddressed_questions?: any[];
  methodological_gaps?: any[];
  theoretical_gaps?: any[];
  total_citations?: number;
  citation_quality?: any;
  reference_analysis?: any;
  citation_gaps?: any[];
  bibliometric_indicators?: any;
  
  // Overall Assessment
  overall_assessment?: {
    analysis_completeness: string;
    key_strengths: string[];
    key_concerns: string[];
    overall_quality: string;
  };
  
  // Quality Assessment Results
  overall_quality_score?: number;
  quality_breakdown?: any;
  quality_strengths?: string[];
  quality_weaknesses?: string[];
  quality_recommendations?: string[];
  quality_confidence_level?: string;
  scoring_criteria_used?: string[];
}

interface EnhancedResearchDataDisplayProps {
  data: AnalysisResult;
  className?: string;
}

export default function EnhancedResearchDataDisplay({ data, className = '' }: EnhancedResearchDataDisplayProps) {
  const [activeTab, setActiveTab] = useState('overview');

  // Debug logging
  console.log('🔍 EnhancedResearchDataDisplay received data:', data);
  console.log('🔍 Data keys:', data ? Object.keys(data) : 'No data');
  console.log('🔍 Data success:', data?.success);
  console.log('🔍 Data tools_used:', data?.tools_used);
  console.log('🔍 Data analysis_level:', data?.analysis_level);

  const formatList = (items: string[] | undefined) => {
    if (!items || items.length === 0) return 'N/A';
    return items.map((item, index) => (
      <li key={index} className="text-sm text-gray-600">{item}</li>
    ));
  };

  const getQualityColor = (quality: string) => {
    const qualityLower = quality?.toLowerCase() || '';
    if (qualityLower.includes('high')) return 'bg-green-100 text-green-800';
    if (qualityLower.includes('medium')) return 'bg-yellow-100 text-yellow-800';
    if (qualityLower.includes('low')) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getCompletenessColor = (completeness: string) => {
    if (completeness === 'comprehensive') return 'bg-green-100 text-green-800';
    if (completeness === 'standard') return 'bg-blue-100 text-blue-800';
    if (completeness === 'basic') return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'summary', label: 'Summary', icon: '📝' },
    { id: 'methodology', label: 'Methodology', icon: '🔬' },
    { id: 'bias', label: 'Bias Analysis', icon: '⚠️' },
    { id: 'statistics', label: 'Statistics', icon: '📈' },
    { id: 'reproducibility', label: 'Reproducibility', icon: '🔄' },
    { id: 'gaps', label: 'Research Gaps', icon: '🔍' },
    { id: 'citations', label: 'Citations', icon: '📚' },
    { id: 'quality', label: 'Quality Score', icon: '⭐' },
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Analysis Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border border-blue-200">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Analysis Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{data.tools_used?.length || 0}</div>
            <div className="text-sm text-gray-600">Tools Used</div>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{data.text_length?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">Characters Analyzed</div>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <div className={`text-2xl font-bold ${getCompletenessColor(data.overall_assessment?.analysis_completeness || '')}`}>
              {data.overall_assessment?.analysis_completeness || 'Unknown'}
            </div>
            <div className="text-sm text-gray-600">Analysis Level</div>
          </div>
        </div>
      </div>

      {/* Overall Assessment */}
      {data.overall_assessment && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Overall Assessment</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-lg font-medium text-gray-700 mb-3">Quality Assessment</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Overall Quality:</span>
                  <span className={`px-3 py-1 text-sm rounded ${getQualityColor(data.overall_assessment.overall_quality)}`}>
                    {data.overall_assessment.overall_quality}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Analysis Completeness:</span>
                  <span className={`px-3 py-1 text-sm rounded ${getCompletenessColor(data.overall_assessment.analysis_completeness)}`}>
                    {data.overall_assessment.analysis_completeness}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-lg font-medium text-gray-700 mb-3">Key Insights</h4>
              <div className="space-y-2">
                {data.overall_assessment.key_strengths && data.overall_assessment.key_strengths.length > 0 && (
                  <div>
                    <span className="text-sm font-medium text-green-700">Strengths:</span>
                    <ul className="text-sm text-gray-600 mt-1">
                      {data.overall_assessment.key_strengths.slice(0, 3).map((strength, index) => (
                        <li key={index}>• {strength}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {data.overall_assessment.key_concerns && data.overall_assessment.key_concerns.length > 0 && (
                  <div>
                    <span className="text-sm font-medium text-red-700">Concerns:</span>
                    <ul className="text-sm text-gray-600 mt-1">
                      {data.overall_assessment.key_concerns.slice(0, 3).map((concern, index) => (
                        <li key={index}>• {concern}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tools Used */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Analysis Tools Used</h3>
        <div className="flex flex-wrap gap-2">
          {data.tools_used?.map((tool, index) => (
            <span key={index} className="bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full">
              {tool.replace('_tool', '').replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>
    </div>
  );

  const renderSummary = () => (
    <div className="space-y-6">
      {/* Executive Summary */}
      {data.executive_summary && (
        <div className="bg-blue-50 p-6 rounded-lg border-l-4 border-blue-400">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Executive Summary</h3>
          <p className="text-gray-700">{data.executive_summary}</p>
        </div>
      )}

      {/* Key Points */}
      {data.key_points && data.key_points.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Key Points</h3>
          <ul className="space-y-2">
            {data.key_points.map((point, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">•</span>
                <span className="text-gray-700">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Full Summary */}
      {data.summary && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Detailed Summary</h3>
          <p className="text-gray-700 leading-relaxed">{data.summary}</p>
        </div>
      )}
    </div>
  );

  const renderMethodology = () => {
    // Helper function to safely render any value
    const safeRender = (value: any): string => {
      if (value === null || value === undefined) return 'N/A';
      if (typeof value === 'string') return value;
      if (typeof value === 'number' || typeof value === 'boolean') return String(value);
      if (Array.isArray(value)) return value.map(item => safeRender(item)).join(', ');
      if (typeof value === 'object') return JSON.stringify(value, null, 2);
      return String(value);
    };

    // Helper function to render list items safely
    const renderListItems = (items: any[], icon: string, color: string) => {
      if (!items || !Array.isArray(items) || items.length === 0) return null;
      
      return items.map((item, index) => (
        <li key={index} className="flex items-start space-x-2">
          <span className={`${color} mt-1`}>{icon}</span>
          <span className="text-gray-700">{safeRender(item)}</span>
        </li>
      ));
    };

    // Helper function to render object entries safely
    const renderObjectEntries = (obj: any) => {
      if (!obj || typeof obj !== 'object') return null;
      
      return Object.entries(obj).map(([key, value]) => (
        <div key={key} className="bg-gray-50 p-3 rounded">
          <span className="font-medium text-gray-700 capitalize">
            {key.replace(/_/g, ' ')}:
          </span>
          <p className="text-sm text-gray-600 mt-1">{safeRender(value)}</p>
        </div>
      ));
    };

    return (
      <div className="space-y-6">
        {/* Study Design */}
        {data.study_design && (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">Study Design</h3>
            <p className="text-gray-700">{safeRender(data.study_design)}</p>
          </div>
        )}

        {/* Sample Characteristics */}
        {data.sample_characteristics && (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">Sample Characteristics</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {renderObjectEntries(data.sample_characteristics)}
            </div>
          </div>
        )}

        {/* Methodological Strengths and Weaknesses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Strengths */}
          {data.methodological_strengths && data.methodological_strengths.length > 0 && (
            <div className="bg-green-50 p-6 rounded-lg border border-green-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Methodological Strengths</h3>
              <ul className="space-y-2">
                {renderListItems(data.methodological_strengths, '✓', 'text-green-500')}
              </ul>
            </div>
          )}

          {/* Weaknesses */}
          {data.methodological_weaknesses && data.methodological_weaknesses.length > 0 && (
            <div className="bg-red-50 p-6 rounded-lg border border-red-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">Methodological Weaknesses</h3>
              <ul className="space-y-2">
                {renderListItems(data.methodological_weaknesses, '⚠', 'text-red-500')}
              </ul>
            </div>
          )}
        </div>

        {/* Quality Rating */}
        {data.methodology_quality_rating && (
          <div className="bg-white p-6 rounded-lg border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">Methodology Quality Rating</h3>
            <div className="flex items-center space-x-4">
              <span className={`px-4 py-2 text-lg rounded ${getQualityColor(data.methodology_quality_rating)}`}>
                {safeRender(data.methodology_quality_rating)}
              </span>
              <p className="text-sm text-gray-600">
                Based on comprehensive analysis of study design, sample characteristics, and methodological rigor
              </p>
            </div>
          </div>
        )}

        {/* Additional Methodology Information */}
        {data.study_design || data.sample_characteristics || data.methodological_strengths || data.methodological_weaknesses ? null : (
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-3">Methodology Analysis</h3>
            <p className="text-gray-600">
              No detailed methodology information available for this analysis.
            </p>
          </div>
        )}
      </div>
    );
  };

  const renderBiasAnalysis = () => (
    <div className="space-y-6">
      {/* Bias Summary */}
      {data.bias_summary && (
        <div className="bg-yellow-50 p-6 rounded-lg border-l-4 border-yellow-400">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Bias Assessment Summary</h3>
          <p className="text-gray-700">{data.bias_summary}</p>
        </div>
      )}

      {/* Detected Biases */}
      {data.detected_biases && data.detected_biases.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Detected Biases</h3>
          <div className="space-y-4">
            {data.detected_biases.map((bias, index) => (
              <div key={index} className="bg-red-50 p-4 rounded-lg border border-red-200">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-800">{bias.bias_type || 'Bias'}</h4>
                  <span className={`px-2 py-1 text-xs rounded ${
                    bias.severity === 'high' ? 'bg-red-100 text-red-800' :
                    bias.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {bias.severity || 'Unknown'} Severity
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2"><strong>Description:</strong> {bias.description}</p>
                {bias.evidence && <p className="text-sm text-gray-600 mb-2"><strong>Evidence:</strong> {bias.evidence}</p>}
                {bias.impact && <p className="text-sm text-gray-600"><strong>Impact:</strong> {bias.impact}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Limitations */}
      {data.limitations && data.limitations.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Study Limitations</h3>
          <ul className="space-y-2">
            {data.limitations.map((limitation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-orange-500 mt-1">⚠</span>
                <span className="text-gray-700">{limitation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confounding Factors */}
      {data.confounding_factors && data.confounding_factors.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Confounding Factors</h3>
          <ul className="space-y-2">
            {data.confounding_factors.map((factor, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-purple-500 mt-1">•</span>
                <span className="text-gray-700">{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderStatistics = () => (
    <div className="space-y-6">
      {/* Statistical Tests Used */}
      {data.statistical_tests_used && data.statistical_tests_used.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Statistical Tests Used</h3>
          <div className="space-y-3">
            {data.statistical_tests_used.map((test, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-lg">
                {typeof test === 'string' ? (
                  <p className="text-gray-700">{test}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{test.test_name || 'Test'}</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {typeof test.purpose === 'string' ? test.purpose : 
                       typeof test.description === 'string' ? test.description : 
                       'No description available'}
                    </p>
                    {test.appropriateness && (
                      <p className="text-sm text-gray-600 mt-1">
                        <strong>Appropriateness:</strong> {
                          typeof test.appropriateness === 'string' ? test.appropriateness : 
                          test.appropriateness.overall || 
                          test.appropriateness.appropriateness || 
                          'Appropriateness information available'
                        }
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Appropriateness */}
      {data.test_appropriateness && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Test Appropriateness</h3>
          {typeof data.test_appropriateness === 'string' ? (
            <p className="text-gray-700">{data.test_appropriateness}</p>
          ) : (
            <div className="space-y-4">
              {data.test_appropriateness.overall && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Overall Assessment</h4>
                  <p className="text-gray-600">
                    {typeof data.test_appropriateness.overall === 'string' 
                      ? data.test_appropriateness.overall 
                      : JSON.stringify(data.test_appropriateness.overall)}
                  </p>
                </div>
              )}
              {data.test_appropriateness.appropriateness && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Appropriateness</h4>
                  <p className="text-gray-600">
                    {typeof data.test_appropriateness.appropriateness === 'string' 
                      ? data.test_appropriateness.appropriateness 
                      : JSON.stringify(data.test_appropriateness.appropriateness)}
                  </p>
                </div>
              )}
              {data.test_appropriateness.rationale && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Rationale</h4>
                  <p className="text-gray-600">
                    {typeof data.test_appropriateness.rationale === 'string' 
                      ? data.test_appropriateness.rationale 
                      : JSON.stringify(data.test_appropriateness.rationale)}
                  </p>
                </div>
              )}
              {data.test_appropriateness.alternatives && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Alternatives</h4>
                  <p className="text-gray-600">
                    {typeof data.test_appropriateness.alternatives === 'string' 
                      ? data.test_appropriateness.alternatives 
                      : JSON.stringify(data.test_appropriateness.alternatives)}
                  </p>
                </div>
              )}
              {data.test_appropriateness.type && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Type</h4>
                  <p className="text-gray-600">
                    {typeof data.test_appropriateness.type === 'string' 
                      ? data.test_appropriateness.type 
                      : JSON.stringify(data.test_appropriateness.type)}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Statistical Concerns */}
      {data.statistical_concerns && data.statistical_concerns.length > 0 && (
        <div className="bg-red-50 p-6 rounded-lg border border-red-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Statistical Concerns</h3>
          <div className="space-y-3">
            {data.statistical_concerns.map((concern, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof concern === 'string' ? (
                  <p className="text-gray-700">{concern}</p>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-800">{concern.concern || 'Concern'}</h4>
                      <span className={`px-2 py-1 text-xs rounded ${
                        concern.severity === 'high' ? 'bg-red-100 text-red-800' :
                        concern.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {concern.severity || 'Unknown'} Severity
                      </span>
                    </div>
                    {concern.impact && <p className="text-sm text-gray-600"><strong>Impact:</strong> {concern.impact}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistical Recommendations */}
      {data.statistical_recommendations && data.statistical_recommendations.length > 0 && (
        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Statistical Recommendations</h3>
          <ul className="space-y-2">
            {data.statistical_recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-green-500 mt-1">✓</span>
                <span className="text-gray-700">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderReproducibility = () => (
    <div className="space-y-6">
      {/* Reproducibility Score */}
      {data.reproducibility_score !== undefined && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Reproducibility Score</h3>
          <div className="flex items-center space-x-4">
            <div className="text-3xl font-bold text-blue-600">
              {Math.round(data.reproducibility_score * 100)}%
            </div>
            <div className="flex-1">
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div 
                  className={`h-4 rounded-full ${
                    data.reproducibility_score >= 0.8 ? 'bg-green-500' :
                    data.reproducibility_score >= 0.6 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${data.reproducibility_score * 100}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {data.reproducibility_score >= 0.8 ? 'High Reproducibility' :
                 data.reproducibility_score >= 0.6 ? 'Medium Reproducibility' :
                 'Low Reproducibility'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Data Availability */}
      {data.data_availability && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Data Availability</h3>
          {typeof data.data_availability === 'string' ? (
            <p className="text-gray-700">{data.data_availability}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(data.data_availability).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-3 rounded">
                  <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                  <p className="text-sm text-gray-600 mt-1">{String(value)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Code Availability */}
      {data.code_availability && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Code Availability</h3>
          {typeof data.code_availability === 'string' ? (
            <p className="text-gray-700">{data.code_availability}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(data.code_availability).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-3 rounded">
                  <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                  <p className="text-sm text-gray-600 mt-1">{String(value)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reproducibility Barriers */}
      {data.reproducibility_barriers && data.reproducibility_barriers.length > 0 && (
        <div className="bg-red-50 p-6 rounded-lg border border-red-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Reproducibility Barriers</h3>
          <div className="space-y-3">
            {data.reproducibility_barriers.map((barrier, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof barrier === 'string' ? (
                  <p className="text-gray-700">{barrier}</p>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-800">{barrier.barrier || 'Barrier'}</h4>
                      <span className={`px-2 py-1 text-xs rounded ${
                        barrier.severity === 'high' ? 'bg-red-100 text-red-800' :
                        barrier.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {barrier.severity || 'Unknown'} Severity
                      </span>
                    </div>
                    {barrier.impact && <p className="text-sm text-gray-600"><strong>Impact:</strong> {barrier.impact}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderGaps = () => (
    <div className="space-y-6">
      {/* Research Gaps */}
      {data.research_gaps && data.research_gaps.length > 0 && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Research Gaps</h3>
          <div className="space-y-4">
            {data.research_gaps.map((gap, index) => (
              <div key={index} className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                {typeof gap === 'string' ? (
                  <p className="text-gray-700">{gap}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{gap.gap_type || 'Research Gap'}</h4>
                    <p className="text-sm text-gray-600 mt-1">{gap.description}</p>
                    {gap.significance && <p className="text-sm text-gray-600 mt-1"><strong>Significance:</strong> {gap.significance}</p>}
                    {gap.evidence && <p className="text-sm text-gray-600 mt-1"><strong>Evidence:</strong> {gap.evidence}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Future Directions */}
      {data.future_directions && data.future_directions.length > 0 && (
        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Future Research Directions</h3>
          <div className="space-y-3">
            {data.future_directions.map((direction, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof direction === 'string' ? (
                  <p className="text-gray-700">{direction}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{direction.direction || 'Future Direction'}</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      {typeof direction.rationale === 'string' 
                        ? direction.rationale 
                        : JSON.stringify(direction.rationale)}
                    </p>
                    {direction.feasibility && <p className="text-sm text-gray-600 mt-1"><strong>Feasibility:</strong> {direction.feasibility}</p>}
                    {direction.priority && (
                      <span className={`inline-block px-2 py-1 text-xs rounded mt-2 ${
                        direction.priority === 'High' ? 'bg-red-100 text-red-800' :
                        direction.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {direction.priority} Priority
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unaddressed Questions */}
      {data.unaddressed_questions && data.unaddressed_questions.length > 0 && (
        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Unaddressed Questions</h3>
          <div className="space-y-3">
            {data.unaddressed_questions.map((question, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof question === 'string' ? (
                  <p className="text-gray-700">{question}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{question.question || 'Question'}</h4>
                    <p className="text-sm text-gray-600 mt-1">{question.importance}</p>
                    {question.research_approach && <p className="text-sm text-gray-600 mt-1"><strong>Research Approach:</strong> {question.research_approach}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Methodological Gaps */}
      {data.methodological_gaps && data.methodological_gaps.length > 0 && (
        <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Methodological Gaps</h3>
          <div className="space-y-3">
            {data.methodological_gaps.map((gap, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof gap === 'string' ? (
                  <p className="text-gray-700">{gap}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{gap.gap || 'Methodological Gap'}</h4>
                    <p className="text-sm text-gray-600 mt-1">{gap.description}</p>
                    {gap.improvement && <p className="text-sm text-gray-600 mt-1"><strong>Improvement:</strong> {gap.improvement}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Theoretical Gaps */}
      {data.theoretical_gaps && data.theoretical_gaps.length > 0 && (
        <div className="bg-indigo-50 p-6 rounded-lg border border-indigo-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Theoretical Gaps</h3>
          <div className="space-y-3">
            {data.theoretical_gaps.map((gap, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof gap === 'string' ? (
                  <p className="text-gray-700">{gap}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{gap.gap || 'Theoretical Gap'}</h4>
                    <p className="text-sm text-gray-600 mt-1">{gap.description}</p>
                    {gap.development && <p className="text-sm text-gray-600 mt-1"><strong>Development:</strong> {gap.development}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderCitations = () => (
    <div className="space-y-6">
      {/* Citation Overview */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Citation Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{data.total_citations || 0}</div>
            <div className="text-sm text-gray-600">Total Citations</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {data.citation_quality ? 'High' : 'Unknown'}
            </div>
            <div className="text-sm text-gray-600">Citation Quality</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {data.citation_gaps?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Citation Gaps</div>
          </div>
        </div>
      </div>

      {/* Citation Quality */}
      {data.citation_quality && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Citation Quality Assessment</h3>
          {typeof data.citation_quality === 'string' ? (
            <p className="text-gray-700">{data.citation_quality}</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(data.citation_quality).map(([key, value]) => (
                <div key={key} className="bg-gray-50 p-3 rounded">
                  <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                  <p className="text-sm text-gray-600 mt-1">{String(value)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reference Analysis */}
      {data.reference_analysis && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Reference Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.reference_analysis).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-3 rounded">
                <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                <p className="text-sm text-gray-600 mt-1">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Citation Gaps */}
      {data.citation_gaps && data.citation_gaps.length > 0 && (
        <div className="bg-red-50 p-6 rounded-lg border border-red-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Citation Gaps</h3>
          <div className="space-y-3">
            {data.citation_gaps.map((gap, index) => (
              <div key={index} className="bg-white p-4 rounded-lg">
                {typeof gap === 'string' ? (
                  <p className="text-gray-700">{gap}</p>
                ) : (
                  <div>
                    <h4 className="font-medium text-gray-800">{gap.gap || 'Citation Gap'}</h4>
                    <p className="text-sm text-gray-600 mt-1">{gap.significance}</p>
                    {gap.suggested_sources && <p className="text-sm text-gray-600 mt-1"><strong>Suggested Sources:</strong> {gap.suggested_sources}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bibliometric Indicators */}
      {data.bibliometric_indicators && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Bibliometric Indicators</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.bibliometric_indicators).map(([key, value]) => (
              <div key={key} className="bg-gray-50 p-3 rounded">
                <span className="font-medium text-gray-700 capitalize">{key.replace('_', ' ')}:</span>
                <p className="text-sm text-gray-600 mt-1">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const renderQualityAssessment = () => (
    <div className="space-y-6">
      {/* Overall Quality Score */}
      {data.overall_quality_score !== undefined && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-6 rounded-lg border border-purple-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Overall Quality Score</h3>
          <div className="flex items-center space-x-6">
            <div className="text-6xl font-bold text-purple-600">
              {data.overall_quality_score.toFixed(1)}
            </div>
            <div className="flex-1">
              <div className="w-full bg-gray-200 rounded-full h-8">
                <div 
                  className={`h-8 rounded-full ${
                    data.overall_quality_score >= 85 ? 'bg-green-500' :
                    data.overall_quality_score >= 70 ? 'bg-yellow-500' :
                    data.overall_quality_score >= 55 ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${data.overall_quality_score}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {data.overall_quality_score >= 85 ? 'Excellent Quality' :
                 data.overall_quality_score >= 70 ? 'Good Quality' :
                 data.overall_quality_score >= 55 ? 'Fair Quality' :
                 'Poor Quality'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Quality Breakdown */}
      {data.quality_breakdown && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(data.quality_breakdown).map(([dimension, scores]: [string, any]) => (
              <div key={dimension} className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-800 capitalize">{dimension.replace('_', ' ')}</h4>
                  <span className="text-lg font-bold text-gray-700">{scores.score?.toFixed(1) || 'N/A'}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full ${
                      scores.score >= 80 ? 'bg-green-500' :
                      scores.score >= 60 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${scores.score || 0}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Weight: {(scores.weight * 100).toFixed(0)}% | 
                  Weighted Score: {(scores.weighted_score || 0).toFixed(1)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quality Strengths and Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {data.quality_strengths && data.quality_strengths.length > 0 && (
          <div className="bg-green-50 p-6 rounded-lg border border-green-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Strengths</h3>
            <ul className="space-y-2">
              {data.quality_strengths.map((strength, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.quality_weaknesses && data.quality_weaknesses.length > 0 && (
          <div className="bg-red-50 p-6 rounded-lg border border-red-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Weaknesses</h3>
            <ul className="space-y-2">
              {data.quality_weaknesses.map((weakness, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-red-500 mt-1">⚠</span>
                  <span className="text-gray-700">{weakness}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Quality Recommendations */}
      {data.quality_recommendations && data.quality_recommendations.length > 0 && (
        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Recommendations</h3>
          <ul className="space-y-2">
            {data.quality_recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">💡</span>
                <span className="text-gray-700">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Confidence Level */}
      {data.quality_confidence_level && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">Assessment Confidence</h3>
          <div className="flex items-center space-x-4">
            <span className={`px-4 py-2 text-lg rounded ${
              data.quality_confidence_level === 'Very High' ? 'bg-green-100 text-green-800' :
              data.quality_confidence_level === 'High' ? 'bg-blue-100 text-blue-800' :
              data.quality_confidence_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
              data.quality_confidence_level === 'Low' ? 'bg-orange-100 text-orange-800' :
              'bg-red-100 text-red-800'
            }`}>
              {data.quality_confidence_level}
            </span>
            <p className="text-sm text-gray-600">
              Based on comprehensive analysis of methodology, statistics, bias, reproducibility, and other factors
            </p>
          </div>
        </div>
      )}

      {/* Scoring Criteria */}
      {data.scoring_criteria_used && data.scoring_criteria_used.length > 0 && (
        <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Scoring Criteria Used</h3>
          <ul className="space-y-2">
            {data.scoring_criteria_used.map((criterion, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="text-gray-500 mt-1">•</span>
                <span className="text-gray-700">{criterion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
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
      case 'quality':
        return renderQualityAssessment();
      default:
        return renderOverview();
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Enhanced Research Analysis</h2>
        <p className="text-gray-600">
          Comprehensive analysis using {data.tools_used?.length || 0} specialized tools
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {renderTabContent()}
      </div>
    </div>
  );
}
