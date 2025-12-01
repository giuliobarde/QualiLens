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

  // Helper function to escape CSV values
  const escapeCsvValue = (value: any): string => {
    if (value === null || value === undefined) return '';
    const stringValue = String(value);
    // If value contains comma, newline, or quote, wrap in quotes and escape quotes
    if (stringValue.includes(',') || stringValue.includes('\n') || stringValue.includes('"')) {
      return `"${stringValue.replace(/"/g, '""')}"`;
    }
    return stringValue;
  };

  // Helper function to flatten nested objects for CSV
  const flattenObject = (obj: any, prefix = '', result: Record<string, any> = {}): Record<string, any> => {
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const newKey = prefix ? `${prefix}.${key}` : key;
        const value = obj[key];
        
        if (value === null || value === undefined) {
          result[newKey] = '';
        } else if (Array.isArray(value)) {
          // For arrays, join with semicolon for CSV
          result[newKey] = value.map(item => 
            typeof item === 'object' ? JSON.stringify(item) : String(item)
          ).join('; ');
        } else if (typeof value === 'object') {
          flattenObject(value, newKey, result);
        } else {
          result[newKey] = value;
        }
      }
    }
    return result;
  };

  // Export to CSV
  const exportToCSV = () => {
    if (!data) {
      alert('No data available to export');
      return;
    }

    // Flatten the data object
    const flattened = flattenObject(data);
    
    // Get all keys and sort them
    const keys = Object.keys(flattened).sort();
    
    // Create CSV header
    const header = keys.map(key => escapeCsvValue(key)).join(',');
    
    // Create CSV row
    const row = keys.map(key => escapeCsvValue(flattened[key])).join(',');
    
    // Combine header and row
    const csvContent = `${header}\n${row}`;
    
    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `research_metadata_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Export to JSON
  const exportToJSON = () => {
    if (!data) {
      alert('No data available to export');
      return;
    }

    const jsonContent = JSON.stringify(data, null, 2);
    
    // Create blob and download
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `research_metadata_${new Date().toISOString().split('T')[0]}.json`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

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

  const renderSummary = () => {
    // COMPLETE REFACTOR: Clean, simple approach for peer reviewers
    // Step 1: Extract and normalize all summary data from various possible locations
    
    // Helper: Strip markdown code fences (```json ... ```)
    const stripMarkdownFences = (text: string): string => {
      if (!text || typeof text !== 'string') return text;
      let cleaned = text.trim();
      // Remove opening fence (```json or ```)
      cleaned = cleaned.replace(/^```(?:json)?\s*/i, '');
      // Remove closing fence (```)
      cleaned = cleaned.replace(/\s*```$/g, '');
      return cleaned.trim();
    };

    // Helper: Safely extract text, never return JSON strings
    const safeExtractText = (value: any): string | null => {
      if (!value) return null;
      if (typeof value === 'string') {
        const trimmed = value.trim();
        // NEVER return JSON strings
        if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
          return null;
        }
        return value;
      }
      return null;
    };

    // Helper: Safely extract array
    const safeExtractArray = (value: any): any[] => {
      if (!value) return [];
      if (Array.isArray(value)) return value;
      if (typeof value === 'string') {
        // If it's a JSON string, try to parse it
        const trimmed = value.trim();
        if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
          try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) return parsed;
            if (typeof parsed === 'object' && parsed !== null) {
              // Might be an object with an array field
              const arr = parsed.items || parsed.list || parsed.data || [];
              return Array.isArray(arr) ? arr : [];
            }
          } catch (e) {
            return [];
          }
        }
        return [value]; // Single string becomes array
      }
      return [];
    };

    // Step 2: Try to parse data.summary if it's a JSON string (including markdown-wrapped JSON)
    let parsedSummary: any = null;
    if (data?.summary && typeof data.summary === 'string') {
      let summaryStr = data.summary.trim();
      
      // CRITICAL: Strip markdown code fences if present
      summaryStr = stripMarkdownFences(summaryStr);
      
      // Try to parse as JSON
      if (summaryStr.startsWith('{') || summaryStr.startsWith('[')) {
        try {
          parsedSummary = JSON.parse(summaryStr);
          if (typeof parsedSummary !== 'object' || parsedSummary === null) {
            parsedSummary = null;
          }
        } catch (e) {
          // Parsing failed, try to extract JSON from the string
          // Sometimes there might be extra text before/after JSON
          const jsonMatch = summaryStr.match(/\{[\s\S]*\}/);
          if (jsonMatch) {
            try {
              parsedSummary = JSON.parse(jsonMatch[0]);
              if (typeof parsedSummary !== 'object' || parsedSummary === null) {
                parsedSummary = null;
              }
            } catch (e2) {
              parsedSummary = null;
            }
          } else {
            parsedSummary = null;
          }
        }
      }
    } else if (data?.summary && typeof data.summary === 'object') {
      parsedSummary = data.summary;
    }

    // Step 3: Extract all fields with clear priority
    // Priority: parsedSummary > data (top-level fields)
    const summaryText = parsedSummary?.summary 
      ? safeExtractText(parsedSummary.summary)
      : safeExtractText(data?.summary);
    
    const executiveSummary = safeExtractText(data?.executive_summary);
    
    const keyPoints = parsedSummary?.key_points 
      ? safeExtractArray(parsedSummary.key_points)
      : safeExtractArray(data?.key_points);
    
    const methodologyHighlights = parsedSummary?.methodology_highlights
      ? safeExtractText(parsedSummary.methodology_highlights)
      : safeExtractText(data?.methodology_highlights);
    
    const mainResults = parsedSummary?.main_results
      ? safeExtractText(parsedSummary.main_results)
      : safeExtractText(data?.main_results);
    
    const implications = parsedSummary?.implications
      ? safeExtractText(parsedSummary.implications)
      : safeExtractText(data?.implications);
    
    const strengths = parsedSummary?.strengths
      ? safeExtractArray(parsedSummary.strengths)
      : safeExtractArray(data?.summary_strengths || data?.strengths);
    
    const limitations = parsedSummary?.limitations
      ? safeExtractArray(parsedSummary.limitations)
      : safeExtractArray(data?.limitations);

    // Step 4: Render the summary sections - clean, professional display for peer reviewers
    return (
      <ErrorBoundary>
        <div className="space-y-6">
          {/* Executive Summary */}
          {executiveSummary && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-5 rounded-xl border-l-4 border-blue-500 shadow-sm">
              <div className="flex items-center mb-3">
                <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="font-bold text-blue-900 text-lg">Executive Summary</h4>
              </div>
              <p className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                {executiveSummary}
              </p>
            </div>
          )}
          
          {/* Main Summary Text */}
          {summaryText && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-5 hover:border-blue-300 transition-all shadow-sm">
              <div className="flex items-center mb-4">
                <svg className="w-5 h-5 text-gray-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="font-bold text-gray-800 text-lg">Summary</h4>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{summaryText}</p>
              </div>
            </div>
          )}
          
          {/* Key Points */}
          {keyPoints.length > 0 && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-5 hover:border-blue-300 transition-all shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  <h4 className="font-bold text-gray-800 text-lg">Key Points</h4>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{keyPoints.length}</span>
              </div>
              <div className="space-y-3">
                {keyPoints.map((point: any, index: number) => {
                  const pointText = typeof point === 'string' ? point : (point.text || point.content || point.description || String(point));
                  return (
                    <div key={index} className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-200 hover:shadow-md transition-all">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </div>
                        <p className="text-sm text-gray-700 flex-1 leading-relaxed">{pointText}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* Methodology Highlights */}
          {methodologyHighlights && (
            <div className="bg-white border-2 border-green-200 rounded-xl p-5 hover:border-green-300 transition-all shadow-sm">
              <div className="flex items-center mb-4">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                <h4 className="font-bold text-gray-800 text-lg">Methodology Highlights</h4>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{methodologyHighlights}</p>
              </div>
            </div>
          )}
          
          {/* Main Results */}
          {mainResults && (
            <div className="bg-white border-2 border-purple-200 rounded-xl p-5 hover:border-purple-300 transition-all shadow-sm">
              <div className="flex items-center mb-4">
                <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <h4 className="font-bold text-gray-800 text-lg">Main Results</h4>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{mainResults}</p>
              </div>
            </div>
          )}
          
          {/* Implications */}
          {implications && (
            <div className="bg-white border-2 border-indigo-200 rounded-xl p-5 hover:border-indigo-300 transition-all shadow-sm">
              <div className="flex items-center mb-4">
                <svg className="w-5 h-5 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <h4 className="font-bold text-gray-800 text-lg">Implications</h4>
              </div>
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{implications}</p>
              </div>
            </div>
          )}
          
          {/* Strengths */}
          {strengths.length > 0 && (
            <div className="bg-white border-2 border-green-200 rounded-xl p-5 hover:border-green-300 transition-all shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4 className="font-bold text-gray-800 text-lg">Strengths</h4>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{strengths.length}</span>
              </div>
              <div className="space-y-2">
                {strengths.map((strength: any, index: number) => {
                  const strengthText = typeof strength === 'string' ? strength : (strength.text || strength.content || strength.description || String(strength));
                  return (
                    <div key={index} className="bg-green-50 p-3 rounded-lg border border-green-200 flex items-start space-x-2">
                      <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <p className="text-sm text-gray-700 flex-1">{strengthText}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Limitations */}
          {limitations.length > 0 && (
            <div className="bg-white border-2 border-orange-200 rounded-xl p-5 hover:border-orange-300 transition-all shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <h4 className="font-bold text-gray-800 text-lg">Limitations</h4>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{limitations.length}</span>
              </div>
              <div className="space-y-2">
                {limitations.map((limitation: any, index: number) => {
                  const limitationText = typeof limitation === 'string' ? limitation : (limitation.text || limitation.content || limitation.description || String(limitation));
                  return (
                    <div key={index} className="bg-orange-50 p-3 rounded-lg border border-orange-200 flex items-start space-x-2">
                      <svg className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <p className="text-sm text-gray-700 flex-1">{limitationText}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Fallback message if no summary data */}
          {!summaryText && keyPoints.length === 0 && !methodologyHighlights && !mainResults && !implications && strengths.length === 0 && limitations.length === 0 && !executiveSummary && (
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 text-center">
              <p className="text-sm text-gray-600">
                No summary information available for this analysis.
              </p>
            </div>
          )}
        </div>
      </ErrorBoundary>
    );
  };

  const renderMethodology = () => {
    const methodologies = data?.detected_methodologies?.methodologies || [];
    const primaryMethodology = data?.primary_methodology || data?.detected_methodologies?.primary_methodology;
    const overallApproach = data?.overall_methodological_approach || data?.detected_methodologies?.overall_methodological_approach;

    const getQualityBadgeColor = (rating: string) => {
      switch (rating?.toLowerCase()) {
        case 'excellent': return 'bg-green-100 text-green-800 border-green-300';
        case 'good': return 'bg-blue-100 text-blue-800 border-blue-300';
        case 'fair': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
        case 'poor': return 'bg-orange-100 text-orange-800 border-orange-300';
        case 'very_poor': return 'bg-red-100 text-red-800 border-red-300';
        default: return 'bg-gray-100 text-gray-800 border-gray-300';
      }
    };

    const getCategoryIcon = (category: string) => {
      switch (category?.toLowerCase()) {
        case 'experimental': return '🧪';
        case 'observational': return '👁️';
        case 'qualitative': return '💬';
        case 'mixed': return '🔀';
        case 'survey': return '📋';
        case 'review': return '📚';
        case 'specialized': return '⚡';
        default: return '🔬';
      }
    };

    return (
      <ErrorBoundary>
        <div className="space-y-4">
          {/* Overall Methodological Approach */}
          {overallApproach && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border-l-4 border-blue-500">
              <h4 className="font-semibold text-blue-900 mb-2">Methodological Approach</h4>
              <SafeRenderer data={overallApproach} className="text-sm text-blue-800" />
            </div>
          )}

          {/* Primary Methodology */}
          {primaryMethodology && primaryMethodology !== 'Unknown' && (
            <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-200">
              <h4 className="font-semibold text-indigo-900 mb-1 text-sm">Primary Methodology</h4>
              <span className="text-indigo-800 font-medium">{primaryMethodology}</span>
            </div>
          )}

          {/* Detected Methodologies */}
          {methodologies.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3">Detected Methodologies ({methodologies.length})</h4>
              <div className="space-y-3">
                {methodologies.map((methodology: any, index: number) => (
                  <div key={index} className="bg-white border-2 border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-all">
                    {/* Methodology Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-xl">{getCategoryIcon(methodology.category)}</span>
                        <div>
                          <h5 className="font-semibold text-gray-900">{methodology.type}</h5>
                          <span className="text-xs text-gray-500 uppercase">{methodology.category}</span>
                        </div>
                      </div>
                      {methodology.quality_assessment?.quality_rating && (
                        <span className={`px-2 py-1 text-xs font-medium rounded border ${getQualityBadgeColor(methodology.quality_assessment.quality_rating)}`}>
                          {methodology.quality_assessment.quality_rating.replace('_', ' ')}
                        </span>
                      )}
                    </div>

                    {/* Quality Assessment Rationale */}
                    {methodology.quality_assessment?.rationale && (
                      <div className="mb-3 p-3 bg-gray-50 rounded">
                        <p className="text-xs font-semibold text-gray-700 mb-1">Assessment:</p>
                        <SafeRenderer data={methodology.quality_assessment.rationale} className="text-sm text-gray-700" />
                      </div>
                    )}

                    {/* Appropriateness Indicator */}
                    {methodology.quality_assessment?.is_appropriate !== undefined && (
                      <div className={`flex items-center space-x-2 mb-2 p-2 rounded ${
                        methodology.quality_assessment.is_appropriate
                          ? 'bg-green-50 text-green-800'
                          : 'bg-red-50 text-red-800'
                      }`}>
                        <span>{methodology.quality_assessment.is_appropriate ? '✓' : '⚠️'}</span>
                        <span className="text-xs font-medium">
                          {methodology.quality_assessment.is_appropriate
                            ? 'Appropriate for research question'
                            : 'May not be appropriate for research question'}
                        </span>
                      </div>
                    )}

                    {/* Strengths & Weaknesses */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
                      {methodology.quality_assessment?.strengths && methodology.quality_assessment.strengths.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-green-700 mb-1">Strengths:</p>
                          <ul className="space-y-1">
                            {methodology.quality_assessment.strengths.slice(0, 2).map((strength: string, idx: number) => (
                              <li key={idx} className="text-xs text-green-700 flex items-start">
                                <span className="text-green-500 mr-1">✓</span>
                                <SafeRenderer data={strength} />
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {methodology.quality_assessment?.weaknesses && methodology.quality_assessment.weaknesses.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold text-red-700 mb-1">Weaknesses:</p>
                          <ul className="space-y-1">
                            {methodology.quality_assessment.weaknesses.slice(0, 2).map((weakness: string, idx: number) => (
                              <li key={idx} className="text-xs text-red-700 flex items-start">
                                <span className="text-red-500 mr-1">⚠</span>
                                <SafeRenderer data={weakness} />
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Evidence Text (small preview) */}
                    {methodology.evidence_text && (
                      <div className="text-xs text-gray-600 italic border-t border-gray-200 pt-2 mt-2">
                        <span className="font-semibold">Evidence: </span>
                        <SafeRenderer data={methodology.evidence_text.substring(0, 150) + (methodology.evidence_text.length > 150 ? '...' : '')} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Traditional Study Design (fallback if no methodologies detected) */}
          {methodologies.length === 0 && data?.study_design && (
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
  };

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
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center">
            <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            Analysis Sections
          </h3>
          <div className="flex gap-2">
            <button
              onClick={exportToCSV}
              className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center gap-1.5 text-xs font-medium"
              title="Export metadata as CSV"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export CSV
            </button>
            <button
              onClick={exportToJSON}
              className="px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 flex items-center gap-1.5 text-xs font-medium"
              title="Export metadata as JSON"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export JSON
            </button>
          </div>
        </div>
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