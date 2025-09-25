'use client';

import React from 'react';

interface ResearchData {
  title?: string;
  authors?: string[];
  abstract?: string;
  methodology?: string;
  study_design?: string;
  sample_size?: number;
  participants?: {
    demographics?: string;
    inclusion_criteria?: string;
    exclusion_criteria?: string;
    recruitment_method?: string;
  };
  results?: {
    primary_outcomes?: string;
    secondary_outcomes?: string;
    statistical_significance?: string;
    effect_sizes?: string;
    confidence_intervals?: string;
    p_values?: string;
  };
  conclusions?: string;
  limitations?: string[];
  keywords?: string[];
  publication_year?: number;
  journal?: string;
  doi?: string;
  research_questions?: string[];
  hypotheses?: string[];
  statistical_tests?: string[];
  effect_direction?: string;
  clinical_significance?: string;
  practical_implications?: string;
  future_research?: string[];
}

interface PaperSummary {
  executive_summary?: string;
  key_findings?: string[];
  methodology_summary?: string;
  results_summary?: string;
  implications?: string;
  significance?: string;
  contribution_to_field?: string;
}

interface KeyDiscovery {
  discovery: string;
  significance: string;
  evidence: string;
  implications: string;
  confidence_level: string;
}

interface KeyDiscoveries {
  key_discoveries?: KeyDiscovery[];
  novel_contributions?: string[];
  breakthrough_findings?: string[];
}

interface MethodologyAnalysis {
  study_design?: string;
  sample_characteristics?: string;
  data_collection?: string;
  analysis_methods?: string;
  validity_measures?: string;
  ethical_considerations?: string;
  limitations?: string;
  strengths?: string;
  quality_rating?: string;
}

interface ResultsAnalysis {
  primary_outcomes?: string;
  secondary_outcomes?: string;
  statistical_significance?: string;
  effect_sizes?: string;
  confidence_intervals?: string;
  clinical_significance?: string;
  unexpected_findings?: string;
  negative_findings?: string;
  results_interpretation?: string;
}

interface QualityAssessment {
  overall_quality?: string;
  strengths?: string[];
  weaknesses?: string[];
  research_gaps?: string[];
  future_directions?: string[];
  reproducibility?: string;
  generalizability?: string;
  bias_assessment?: string;
  recommendations?: string;
}

interface DetailedAnalysis {
  paper_summary?: PaperSummary;
  key_discoveries?: KeyDiscoveries;
  methodology_analysis?: MethodologyAnalysis;
  results_analysis?: ResultsAnalysis;
  quality_assessment?: QualityAssessment;
}

interface ResearchDataDisplayProps {
  data: ResearchData;
  detailedAnalysis?: DetailedAnalysis;
  className?: string;
}

export default function ResearchDataDisplay({ data, detailedAnalysis, className = '' }: ResearchDataDisplayProps) {
  const formatList = (items: string[] | undefined) => {
    if (!items || items.length === 0) return 'N/A';
    return items.map((item, index) => (
      <li key={index} className="text-sm text-gray-600">{item}</li>
    ));
  };

  const formatAuthors = (authors: string[] | undefined) => {
    if (!authors || authors.length === 0) return 'N/A';
    return authors.join(', ');
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 space-y-6 ${className}`}>
      <div className="border-b pb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Research Analysis Results</h2>
        <p className="text-gray-600">Extracted key data from the research paper</p>
      </div>

      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Basic Information</h3>
          <div className="space-y-2">
            <div>
              <span className="font-medium text-gray-700">Title:</span>
              <p className="text-sm text-gray-600">{data.title || 'N/A'}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Authors:</span>
              <p className="text-sm text-gray-600">{formatAuthors(data.authors)}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Journal:</span>
              <p className="text-sm text-gray-600">{data.journal || 'N/A'}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Year:</span>
              <p className="text-sm text-gray-600">{data.publication_year || 'N/A'}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">DOI:</span>
              <p className="text-sm text-gray-600">{data.doi || 'N/A'}</p>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Study Details</h3>
          <div className="space-y-2">
            <div>
              <span className="font-medium text-gray-700">Sample Size:</span>
              <p className="text-sm text-gray-600">{data.sample_size || 'N/A'}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Study Design:</span>
              <p className="text-sm text-gray-600">{data.study_design || 'N/A'}</p>
            </div>
            <div>
              <span className="font-medium text-gray-700">Methodology:</span>
              <p className="text-sm text-gray-600">{data.methodology || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Abstract */}
      {data.abstract && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Abstract</h3>
          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{data.abstract}</p>
        </div>
      )}

      {/* Participants */}
      {data.participants && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Participants</h3>
          <div className="space-y-2">
            {data.participants.demographics && (
              <div>
                <span className="font-medium text-gray-700">Demographics:</span>
                <p className="text-sm text-gray-600">{data.participants.demographics}</p>
              </div>
            )}
            {data.participants.inclusion_criteria && (
              <div>
                <span className="font-medium text-gray-700">Inclusion Criteria:</span>
                <p className="text-sm text-gray-600">{data.participants.inclusion_criteria}</p>
              </div>
            )}
            {data.participants.exclusion_criteria && (
              <div>
                <span className="font-medium text-gray-700">Exclusion Criteria:</span>
                <p className="text-sm text-gray-600">{data.participants.exclusion_criteria}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results */}
      {data.results && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Results</h3>
          <div className="space-y-2">
            {data.results.primary_outcomes && (
              <div>
                <span className="font-medium text-gray-700">Primary Outcomes:</span>
                <p className="text-sm text-gray-600">{data.results.primary_outcomes}</p>
              </div>
            )}
            {data.results.secondary_outcomes && (
              <div>
                <span className="font-medium text-gray-700">Secondary Outcomes:</span>
                <p className="text-sm text-gray-600">{data.results.secondary_outcomes}</p>
              </div>
            )}
            {data.results.statistical_significance && (
              <div>
                <span className="font-medium text-gray-700">Statistical Significance:</span>
                <p className="text-sm text-gray-600">{data.results.statistical_significance}</p>
              </div>
            )}
            {data.results.effect_sizes && (
              <div>
                <span className="font-medium text-gray-700">Effect Sizes:</span>
                <p className="text-sm text-gray-600">{data.results.effect_sizes}</p>
              </div>
            )}
            {data.results.p_values && (
              <div>
                <span className="font-medium text-gray-700">P-values:</span>
                <p className="text-sm text-gray-600">{data.results.p_values}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Research Questions */}
      {data.research_questions && data.research_questions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Research Questions</h3>
          <ul className="space-y-1">
            {formatList(data.research_questions)}
          </ul>
        </div>
      )}

      {/* Hypotheses */}
      {data.hypotheses && data.hypotheses.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Hypotheses</h3>
          <ul className="space-y-1">
            {formatList(data.hypotheses)}
          </ul>
        </div>
      )}

      {/* Statistical Tests */}
      {data.statistical_tests && data.statistical_tests.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Statistical Tests</h3>
          <ul className="space-y-1">
            {formatList(data.statistical_tests)}
          </ul>
        </div>
      )}

      {/* Conclusions */}
      {data.conclusions && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Conclusions</h3>
          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{data.conclusions}</p>
        </div>
      )}

      {/* Limitations */}
      {data.limitations && data.limitations.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Limitations</h3>
          <ul className="space-y-1">
            {formatList(data.limitations)}
          </ul>
        </div>
      )}

      {/* Keywords */}
      {data.keywords && data.keywords.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {data.keywords.map((keyword, index) => (
              <span key={index} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Clinical Significance */}
      {data.clinical_significance && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Clinical Significance</h3>
          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{data.clinical_significance}</p>
        </div>
      )}

      {/* Practical Implications */}
      {data.practical_implications && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Practical Implications</h3>
          <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{data.practical_implications}</p>
        </div>
      )}

      {/* Future Research */}
      {data.future_research && data.future_research.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Future Research Directions</h3>
          <ul className="space-y-1">
            {formatList(data.future_research)}
          </ul>
        </div>
      )}

      {/* Detailed Analysis Section */}
      {detailedAnalysis && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Analysis</h2>
          
          {/* Paper Summary */}
          {detailedAnalysis.paper_summary && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Paper Summary</h3>
              
              {detailedAnalysis.paper_summary.executive_summary && (
                <div className="mb-4">
                  <h4 className="text-lg font-medium text-gray-700 mb-2">Executive Summary</h4>
                  <p className="text-sm text-gray-600 bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
                    {detailedAnalysis.paper_summary.executive_summary}
                  </p>
                </div>
              )}
              
              {detailedAnalysis.paper_summary.key_findings && detailedAnalysis.paper_summary.key_findings.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-lg font-medium text-gray-700 mb-2">Key Findings</h4>
                  <ul className="space-y-2">
                    {detailedAnalysis.paper_summary.key_findings.map((finding, index) => (
                      <li key={index} className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {detailedAnalysis.paper_summary.contribution_to_field && (
                <div className="mb-4">
                  <h4 className="text-lg font-medium text-gray-700 mb-2">Contribution to Field</h4>
                  <p className="text-sm text-gray-600 bg-green-50 p-4 rounded-lg border-l-4 border-green-400">
                    {detailedAnalysis.paper_summary.contribution_to_field}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Key Discoveries */}
          {detailedAnalysis.key_discoveries && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Key Discoveries</h3>
              
              {detailedAnalysis.key_discoveries.key_discoveries && detailedAnalysis.key_discoveries.key_discoveries.length > 0 && (
                <div className="space-y-4">
                  {detailedAnalysis.key_discoveries.key_discoveries.map((discovery, index) => (
                    <div key={index} className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-400">
                      <h4 className="font-medium text-gray-800 mb-2">Discovery {index + 1}</h4>
                      <p className="text-sm text-gray-600 mb-2"><strong>Finding:</strong> {discovery.discovery}</p>
                      <p className="text-sm text-gray-600 mb-2"><strong>Significance:</strong> {discovery.significance}</p>
                      <p className="text-sm text-gray-600 mb-2"><strong>Evidence:</strong> {discovery.evidence}</p>
                      <p className="text-sm text-gray-600 mb-2"><strong>Implications:</strong> {discovery.implications}</p>
                      <span className={`inline-block px-2 py-1 text-xs rounded ${
                        discovery.confidence_level === 'High' ? 'bg-green-100 text-green-800' :
                        discovery.confidence_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        Confidence: {discovery.confidence_level}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              {detailedAnalysis.key_discoveries.breakthrough_findings && detailedAnalysis.key_discoveries.breakthrough_findings.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-lg font-medium text-gray-700 mb-2">Breakthrough Findings</h4>
                  <ul className="space-y-2">
                    {detailedAnalysis.key_discoveries.breakthrough_findings.map((finding, index) => (
                      <li key={index} className="text-sm text-gray-600 bg-orange-50 p-3 rounded border-l-4 border-orange-400">
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Methodology Analysis */}
          {detailedAnalysis.methodology_analysis && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Methodology Analysis</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {detailedAnalysis.methodology_analysis.study_design && (
                  <div className="bg-gray-50 p-4 rounded">
                    <h4 className="font-medium text-gray-700 mb-2">Study Design</h4>
                    <p className="text-sm text-gray-600">{detailedAnalysis.methodology_analysis.study_design}</p>
                  </div>
                )}
                
                {detailedAnalysis.methodology_analysis.sample_characteristics && (
                  <div className="bg-gray-50 p-4 rounded">
                    <h4 className="font-medium text-gray-700 mb-2">Sample Characteristics</h4>
                    <p className="text-sm text-gray-600">{detailedAnalysis.methodology_analysis.sample_characteristics}</p>
                  </div>
                )}
                
                {detailedAnalysis.methodology_analysis.quality_rating && (
                  <div className="bg-gray-50 p-4 rounded">
                    <h4 className="font-medium text-gray-700 mb-2">Quality Rating</h4>
                    <span className={`inline-block px-3 py-1 text-sm rounded ${
                      detailedAnalysis.methodology_analysis.quality_rating?.toLowerCase().includes('high') ? 'bg-green-100 text-green-800' :
                      detailedAnalysis.methodology_analysis.quality_rating?.toLowerCase().includes('medium') ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {detailedAnalysis.methodology_analysis.quality_rating}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quality Assessment */}
          {detailedAnalysis.quality_assessment && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Quality Assessment</h3>
              
              {detailedAnalysis.quality_assessment.overall_quality && (
                <div className="mb-4">
                  <h4 className="text-lg font-medium text-gray-700 mb-2">Overall Quality</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg">
                    {detailedAnalysis.quality_assessment.overall_quality}
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {detailedAnalysis.quality_assessment.strengths && detailedAnalysis.quality_assessment.strengths.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-700 mb-2">Strengths</h4>
                    <ul className="space-y-1">
                      {detailedAnalysis.quality_assessment.strengths.map((strength, index) => (
                        <li key={index} className="text-sm text-gray-600 bg-green-50 p-2 rounded">
                          ✓ {strength}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {detailedAnalysis.quality_assessment.weaknesses && detailedAnalysis.quality_assessment.weaknesses.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-700 mb-2">Weaknesses</h4>
                    <ul className="space-y-1">
                      {detailedAnalysis.quality_assessment.weaknesses.map((weakness, index) => (
                        <li key={index} className="text-sm text-gray-600 bg-red-50 p-2 rounded">
                          ⚠ {weakness}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
