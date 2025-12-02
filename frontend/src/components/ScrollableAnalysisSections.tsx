'use client';

import React, { useState, useEffect } from 'react';
import ErrorBoundary from './ErrorBoundary';
import SafeRenderer from './SafeRenderer';

interface ScrollableAnalysisSectionsProps {
  data: any;
  className?: string;
  onExportFunctionsReady?: (functions: { exportCSV: () => void; exportJSON: () => void }) => void;
}

export default function ScrollableAnalysisSections({ data, className = '', onExportFunctionsReady }: ScrollableAnalysisSectionsProps) {
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

  // Expose export functions to parent
  useEffect(() => {
    if (onExportFunctionsReady) {
      onExportFunctionsReady({
        exportCSV: exportToCSV,
        exportJSON: exportToJSON
      });
    }
  }, [onExportFunctionsReady, data]);

  const sections = [
    { id: 'summary', label: 'Summary', icon: '📝', color: 'blue' },
    { id: 'methodology', label: 'Methodology', icon: '🔬', color: 'green' },
    { id: 'bias', label: 'Bias Analysis', icon: '⚠️', color: 'red' },
    { id: 'reproducibility', label: 'Reproducibility', icon: '🔄', color: 'indigo' },
    { id: 'gaps', label: 'Research Gaps', icon: '🔍', color: 'yellow' },
    { id: 'citations', label: 'Citations', icon: '📚', color: 'pink' },
  ];

  const getColorClasses = (color: string, isActive: boolean) => {
    const colorMap = {
      blue: isActive 
        ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/30' 
        : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50/50',
      green: isActive 
        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg shadow-green-500/30' 
        : 'text-gray-600 hover:text-green-600 hover:bg-green-50/50',
      red: isActive 
        ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg shadow-red-500/30' 
        : 'text-gray-600 hover:text-red-600 hover:bg-red-50/50',
      purple: isActive 
        ? 'bg-gradient-to-r from-purple-500 to-purple-600 text-white shadow-lg shadow-purple-500/30' 
        : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50/50',
      indigo: isActive 
        ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/30' 
        : 'text-gray-600 hover:text-indigo-600 hover:bg-indigo-50/50',
      yellow: isActive 
        ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg shadow-yellow-500/30' 
        : 'text-gray-600 hover:text-yellow-600 hover:bg-yellow-50/50',
      pink: isActive 
        ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white shadow-lg shadow-pink-500/30' 
        : 'text-gray-600 hover:text-pink-600 hover:bg-pink-50/50',
    };
    return colorMap[color as keyof typeof colorMap] || (isActive ? 'bg-gray-600 text-white' : 'text-gray-600 hover:bg-gray-50/50');
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

  const renderGaps = () => {
    // Helper function to normalize text for comparison
    const normalizeText = (text: string): string => {
      if (!text) return '';
      return text.toLowerCase()
        .replace(/[^\w\s]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
    };
    
    // Helper function to check if two gaps are similar
    const areSimilar = (text1: string, text2: string): boolean => {
      const norm1 = normalizeText(text1);
      const norm2 = normalizeText(text2);
      
      // Check if one contains the other (for pattern vs expanded versions)
      if (norm1.length > 20 && norm2.length > 20) {
        if (norm1.includes(norm2) || norm2.includes(norm1)) {
          return true;
        }
      }
      
      // Calculate word overlap
      const words1 = new Set(norm1.split(' ').filter(w => w.length > 3));
      const words2 = new Set(norm2.split(' ').filter(w => w.length > 3));
      
      if (words1.size === 0 || words2.size === 0) return false;
      
      const intersection = new Set([...words1].filter(w => words2.has(w)));
      const union = new Set([...words1, ...words2]);
      
      const similarity = intersection.size / union.size;
      return similarity >= 0.5; // 50% word overlap
    };
    
    // Collect research gaps from data.research_gaps
    const researchGaps = data?.research_gaps && Array.isArray(data.research_gaps) ? data.research_gaps : [];
    
    // Collect research gap evidence traces
    const researchGapEvidence = data?.evidence_traces && Array.isArray(data.evidence_traces)
      ? data.evidence_traces.filter((e: any) => e.category === 'research_gap')
      : [];
    
    // Process research gaps - prefer structured format
    const processedGaps: any[] = [];
    
    // First, add structured research gaps (prefer these as they have more info)
    researchGaps.forEach((gap: any) => {
      if (typeof gap === 'string') {
        processedGaps.push({
          type: 'gap',
          content: gap,
          description: gap,
          gap_type: 'methodological',
          significance: '',
          evidence: '',
          verification_reasoning: '',
          original: gap
        });
      } else {
        // Use standardized format
        const description = gap.description || gap.gap || gap.text || '';
        if (description) {
          processedGaps.push({
            type: 'gap',
            content: description, // For display, use description
            description: description,
            gap_type: gap.gap_type || gap.type || 'methodological',
            significance: gap.significance || '',
            evidence: gap.evidence || '',
            verification_reasoning: gap.verification_reasoning || gap.reasoning || '',
            original: gap
          });
        }
      }
    });
    
    // Then, add evidence traces, but deduplicate against existing gaps
    researchGapEvidence.forEach((evidence: any) => {
      const evidenceText = evidence.text_snippet || '';
      const rationale = evidence.rationale || '';
      
      // Skip if this is a methodological gap or unaddressed question (they're shown separately)
      if (rationale.includes('Methodological Gap:') || rationale.includes('Unaddressed Question:')) {
        return; // These will be shown in their respective sections
      }
      
      // Extract description from rationale (it's usually at the start)
      let description = evidenceText;
      let gapType = 'methodological'; // Default
      let significance = '';
      
      if (rationale) {
        // Extract gap type from rationale
        const typeMatch = rationale.match(/RESEARCH GAP:\s*(\w+)/i);
        if (typeMatch) {
          gapType = typeMatch[1].toLowerCase();
        }
        
        // Try to extract description from formatted rationale
        const descMatch = rationale.match(/GAP DESCRIPTION:\s*(.+?)(?:\n|💡|📄|🔬)/i);
        if (descMatch) {
          description = descMatch[1].trim();
        } else {
          // Fallback: use first line or text_snippet
          description = rationale.split('\n')[0] || evidenceText;
        }
        
        // Extract significance
        const sigMatch = rationale.match(/SIGNIFICANCE:\s*(.+?)(?:\n|📄|🔬)/i);
        if (sigMatch) {
          significance = sigMatch[1].trim();
        }
      }
      
      // Check if this evidence is a duplicate of an existing gap
      const isDuplicate = processedGaps.some(existing => {
        const existingDesc = existing.description || existing.content || '';
        return areSimilar(description, existingDesc);
      });
      
      if (!isDuplicate && description) {
        // Add as new gap, preferring evidence trace format (richer)
        processedGaps.push({
          type: 'evidence',
          content: description, // Use clean description for display
          description: description,
          gap_type: gapType,
          significance: significance,
          evidence: evidenceText,
          verification_reasoning: rationale,
          page: evidence.page_number,
          textSnippet: evidenceText,
          original: evidence
        });
      }
    });
    
    const totalCount = processedGaps.length;
    
    return (
      <ErrorBoundary>
        <div className="space-y-4">
          {totalCount > 0 && (
            <div className="bg-white border-2 border-yellow-200 rounded-xl p-5 hover:border-yellow-300 transition-all shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  <h4 className="font-bold text-gray-800 text-lg">Research Gaps</h4>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{totalCount}</span>
              </div>
              <div className="space-y-3">
                {processedGaps.map((item: any, index: number) => {
                  // Use description for clean display, fallback to content
                  const displayText = item.description || item.content || '';
                  
                  // Get gap type for badge
                  const gapType = item.gap_type || 'methodological';
                  const gapTypeColors: Record<string, { bg: string; text: string }> = {
                    methodological: { bg: 'bg-blue-100', text: 'text-blue-800' },
                    theoretical: { bg: 'bg-purple-100', text: 'text-purple-800' },
                    empirical: { bg: 'bg-green-100', text: 'text-green-800' },
                    practical: { bg: 'bg-orange-100', text: 'text-orange-800' }
                  };
                  const typeColor = gapTypeColors[gapType] || { bg: 'bg-gray-100', text: 'text-gray-800' };
                  
                  return (
                    <div key={index} className="bg-gradient-to-r from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-200 hover:shadow-md transition-all">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 w-6 h-6 bg-yellow-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          {/* Gap Type Badge */}
                          {gapType && (
                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-2 ${typeColor.bg} ${typeColor.text}`}>
                              {gapType.charAt(0).toUpperCase() + gapType.slice(1)}
                            </span>
                          )}
                          
                          {/* Description */}
                          <p className="text-sm text-gray-700 leading-relaxed font-medium mb-1">
                            <SafeRenderer data={displayText} />
                          </p>
                          
                          {/* Significance (if available) */}
                          {item.significance && (
                            <p className="text-xs text-gray-600 italic mt-1">
                              <span className="font-semibold">Significance:</span> {item.significance}
                            </p>
                          )}
                          
                          {/* Evidence (if available and different from description) */}
                          {item.evidence && item.evidence !== displayText && (
                            <p className="text-xs text-gray-500 mt-1 bg-gray-50 p-2 rounded">
                              <span className="font-semibold">Evidence:</span> {item.evidence.substring(0, 200)}{item.evidence.length > 200 ? '...' : ''}
                            </p>
                          )}
                          
                          {/* Page number */}
                          {item.page && (
                            <span className="text-xs text-yellow-600 mt-1 inline-block">(Page {item.page})</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        
        {(() => {
          // Collect future directions from data
          const directionsFromData = data?.future_directions && Array.isArray(data.future_directions) 
            ? data.future_directions 
            : [];
          
          // Extract methodological gaps that suggest future directions
          const methodologicalGaps = data?.methodological_gaps && Array.isArray(data.methodological_gaps)
            ? data.methodological_gaps
            : [];
          
          const gapsAsDirections = methodologicalGaps
            .map((gap: any) => {
              if (typeof gap === 'string') return gap;
              return gap.improvement || gap.description || gap.gap || '';
            })
            .filter((d: string) => d);
          
          // Combine and deduplicate
          const allDirections = [...directionsFromData, ...gapsAsDirections];
          const uniqueDirections = Array.from(new Set(allDirections.map((d: any) => {
            if (typeof d === 'string') return d;
            return d.direction || d.text || String(d);
          })));
          
          return uniqueDirections.length > 0 ? (
            <div>
              <h4 className="font-semibold text-green-800 mb-2">Future Directions</h4>
              <ul className="space-y-1">
                {uniqueDirections.slice(0, 5).map((direction: any, index: number) => (
                  <li key={index} className="text-sm text-green-700 flex items-start">
                    <span className="text-green-500 mr-2">→</span>
                    <SafeRenderer data={typeof direction === 'string' ? direction : (direction.direction || direction.text || String(direction))} />
                  </li>
                ))}
              </ul>
            </div>
          ) : null;
        })()}
        
        {(() => {
          // Collect unaddressed questions from both data and evidence traces
          const questionsFromData = data?.unaddressed_questions && Array.isArray(data.unaddressed_questions) 
            ? data.unaddressed_questions 
            : [];
          
          // Extract questions from evidence traces
          const questionsFromEvidence = researchGapEvidence
            .filter((e: any) => e.rationale?.includes('Unaddressed Question:'))
            .map((e: any) => {
              const match = e.rationale?.match(/Unaddressed Question:\s*(.+?)(?:\.\s|$)/i);
              return match ? match[1].trim() : null;
            })
            .filter((q: any) => q);
          
          // Combine and deduplicate
          const allQuestions = [...questionsFromData, ...questionsFromEvidence];
          const uniqueQuestions = Array.from(new Set(allQuestions.map((q: any) => {
            if (typeof q === 'string') return q;
            return q.question || q.text || String(q);
          })));
          
          return uniqueQuestions.length > 0 ? (
            <div>
              <h4 className="font-semibold text-blue-800 mb-2">Unaddressed Questions</h4>
              <ul className="space-y-1">
                {uniqueQuestions.slice(0, 5).map((question: any, index: number) => (
                  <li key={index} className="text-sm text-blue-700 flex items-start">
                    <span className="text-blue-500 mr-2">?</span>
                    <SafeRenderer data={typeof question === 'string' ? question : (question.question || question.text || String(question))} />
                  </li>
                ))}
              </ul>
            </div>
          ) : null;
        })()}
      </div>
    </ErrorBoundary>
    );
  };

  const renderCitations = () => {
    // Get citations from various possible locations
    const extractedCitations = 
      data?.citation_analysis?.extracted_citations || 
      data?.extracted_citations || 
      [];
    
    const totalCitations = data?.total_citations || 
      data?.citation_analysis?.total_citations || 
      extractedCitations.length || 
      0;

    return (
      <ErrorBoundary>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-blue-50 p-3 rounded text-center">
              <div className="text-lg font-bold text-blue-600">{totalCitations}</div>
              <div className="text-xs text-blue-600">Total Citations</div>
            </div>
            <div className="bg-green-50 p-3 rounded text-center">
              <div className="text-lg font-bold text-green-600">
                {data?.citation_quality || data?.citation_analysis?.citation_quality ? 'High' : 'Unknown'}
              </div>
              <div className="text-xs text-green-600">Quality</div>
            </div>
          </div>
          
          {/* Citations List */}
          {extractedCitations && Array.isArray(extractedCitations) && extractedCitations.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3">All Citations ({extractedCitations.length})</h4>
              <div className="max-h-96 overflow-y-auto space-y-3 pr-2">
                {extractedCitations.map((citation: any, index: number) => (
                  <div 
                    key={citation.citation_number || index} 
                    className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-pink-100 rounded-full flex items-center justify-center text-pink-600 font-semibold text-sm">
                        {citation.citation_number || index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        {/* Authors */}
                        {citation.authors && citation.authors.length > 0 && (
                          <div className="mb-1">
                            <span className="text-sm font-semibold text-gray-700">
                              {citation.authors.slice(0, 3).join(', ')}
                              {citation.authors.length > 3 && ` et al.`}
                            </span>
                          </div>
                        )}
                        
                        {/* Title */}
                        {citation.title && (
                          <div className="mb-1">
                            <span className="text-sm font-medium text-gray-800 italic">
                              {citation.title.length > 150 ? `${citation.title.substring(0, 150)}...` : citation.title}
                            </span>
                          </div>
                        )}
                        
                        {/* Journal/Book Title */}
                        {(citation.journal || citation.book_title) && (
                          <div className="mb-1">
                            <span className="text-sm text-gray-600">
                              {citation.journal || citation.book_title}
                              {citation.volume && `, Vol. ${citation.volume}`}
                              {citation.issue && `, No. ${citation.issue}`}
                            </span>
                          </div>
                        )}
                        
                        {/* Year, Pages, DOI */}
                        <div className="flex flex-wrap gap-2 text-xs text-gray-500 mt-1">
                          {citation.year && (
                            <span className="bg-gray-100 px-2 py-0.5 rounded">{citation.year}</span>
                          )}
                          {citation.pages && (
                            <span className="bg-gray-100 px-2 py-0.5 rounded">pp. {citation.pages}</span>
                          )}
                          {citation.doi && (
                            <span className="bg-blue-100 px-2 py-0.5 rounded text-blue-700">
                              DOI: {citation.doi.length > 30 ? `${citation.doi.substring(0, 30)}...` : citation.doi}
                            </span>
                          )}
                          {citation.citation_style && (
                            <span className="bg-purple-100 px-2 py-0.5 rounded text-purple-700">
                              {citation.citation_style}
                            </span>
                          )}
                        </div>
                        
                        {/* Raw citation as fallback if structured data is minimal */}
                        {(!citation.title && !citation.authors?.length) && citation.raw && (
                          <div className="mt-2 text-xs text-gray-600 italic">
                            {citation.raw.length > 200 ? `${citation.raw.substring(0, 200)}...` : citation.raw}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
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
  };

  const renderSectionContent = () => {
    switch (activeSection) {
      case 'summary':
        return renderSummary();
      case 'methodology':
        return renderMethodology();
      case 'bias':
        return renderBiasAnalysis();
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
      {/* Modern Section Navigation */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-sm">
        <div className="px-6 pt-5 pb-3">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-indigo-600 rounded-full"></div>
              <span>Analytics Sections</span>
            </h3>
          </div>
          
          {/* Modern Horizontal Scrollable Tab Bar */}
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`
                  relative px-5 py-2.5 rounded-full text-sm font-medium
                  transition-all duration-300 ease-out
                  whitespace-nowrap
                  flex items-center gap-2
                  ${activeSection === section.id 
                    ? getColorClasses(section.color, true) + ' scale-105'
                    : getColorClasses(section.color, false) + ' bg-white border border-gray-200 hover:border-gray-300'
                  }
                  ${activeSection === section.id ? 'shadow-md' : 'shadow-sm hover:shadow'}
                `}
              >
                <span className={`text-base transition-transform duration-300 ${activeSection === section.id ? 'scale-110' : ''}`}>
                  {section.icon}
                </span>
                <span className="font-semibold">{section.label}</span>
                {activeSection === section.id && (
                  <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-white rounded-full animate-pulse"></div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Modern Section Content */}
      <div className="flex-1 overflow-y-auto p-6 analysis-scroll bg-gradient-to-b from-gray-50/50 to-white">
        <div className="max-w-5xl mx-auto">
          <div className="animate-fade-in">
            {renderSectionContent()}
          </div>
        </div>
      </div>
    </div>
  );
}