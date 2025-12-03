'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface EvidenceItem {
  id: string;
  category: string;
  text_snippet: string;
  rationale: string;
  page_number?: number;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  confidence?: number;
  severity?: string;
  score_impact?: number;
}

interface EvidenceVisualizationProps {
  evidenceTraces: EvidenceItem[];
  pdfContent?: string | null;
  onEvidenceClick?: (evidence: EvidenceItem) => void;
  selectedCategory?: string;
  onCategoryChange?: (category: string) => void;
  onExportFunctionsReady?: (functions: { exportSelected: () => void; exportAll: () => void }) => void;
  selectedEvidence?: EvidenceItem | null;
}

type EvidenceCategory = 'all' | 'bias' | 'limitation' | 'methodology' | 'reproducibility' | 'statistics';

function EvidenceVisualization({
  evidenceTraces = [],
  pdfContent,
  onEvidenceClick,
  selectedCategory: externalSelectedCategory,
  onCategoryChange,
  onExportFunctionsReady,
  selectedEvidence: externalSelectedEvidence
}: EvidenceVisualizationProps) {
  const [internalSelectedCategory, setInternalSelectedCategory] = useState<EvidenceCategory>('all');
  const selectedCategory = (externalSelectedCategory as EvidenceCategory) || internalSelectedCategory;

  const handleCategoryChange = (category: EvidenceCategory) => {
    setInternalSelectedCategory(category);
    if (onCategoryChange) {
      onCategoryChange(category);
    }
  };
  const [internalSelectedEvidence, setInternalSelectedEvidence] = useState<EvidenceItem | null>(null);
  const selectedEvidence = externalSelectedEvidence || internalSelectedEvidence;
  const [hoveredEvidenceId, setHoveredEvidenceId] = useState<string | null>(null);
  const pdfViewerRef = useRef<HTMLIFrameElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const filteredEvidence = selectedCategory === 'all'
    ? evidenceTraces.filter(e => e.category !== 'research_gap')
    : evidenceTraces.filter(e => e.category === selectedCategory && e.category !== 'research_gap');

  const evidenceByPage = filteredEvidence.reduce((acc, evidence) => {
    const page = evidence.page_number || 0;
    if (!acc[page]) acc[page] = [];
    acc[page].push(evidence);
    return acc;
  }, {} as Record<number, EvidenceItem[]>);

  const handleEvidenceClick = (evidence: EvidenceItem) => {
    setInternalSelectedEvidence(evidence);
    if (onEvidenceClick) {
      onEvidenceClick(evidence);
    }
  };

  const handleExportScreenshot = useCallback(async () => {
    if (!selectedEvidence || !pdfContent) return;
    try {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const exportData = {
        evidence: selectedEvidence,
        timestamp: new Date().toISOString(),
        category: selectedEvidence.category,
        page: selectedEvidence.page_number,
        rationale: selectedEvidence.rationale
      };
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `evidence-${selectedEvidence.id}-${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export evidence:', error);
    }
  }, [selectedEvidence, pdfContent]);

  const handleExportAll = useCallback(() => {
    const filteredTraces = evidenceTraces.filter(e => e.category !== 'research_gap');
    const exportData = {
      evidence: filteredTraces,
      timestamp: new Date().toISOString(),
      total_count: filteredTraces.length
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `all-evidence-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [evidenceTraces]);

  useEffect(() => {
    if (onExportFunctionsReady) {
      onExportFunctionsReady({
        exportSelected: handleExportScreenshot,
        exportAll: handleExportAll
      });
    }
  }, [onExportFunctionsReady, handleExportScreenshot, handleExportAll]);

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'bias':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'limitation':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'methodology':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'reproducibility':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'statistics':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 font-semibold';
      case 'medium':
        return 'text-yellow-600 font-medium';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  if (evidenceTraces.length === 0) {
    return (
      <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6 border border-gray-200/50">
        <div className="text-center py-8">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-gray-600">No evidence traces available</p>
          <p className="text-sm text-gray-500 mt-2">Evidence will appear here after analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 overflow-hidden">
      <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Evidence Visualization</h3>
            <p className="text-sm text-gray-600 mt-1">
              {filteredEvidence.length} evidence item{filteredEvidence.length !== 1 ? 's' : ''} found
            </p>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2 flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700">Filter:</span>
          {(['all', 'bias', 'limitation', 'methodology', 'reproducibility', 'statistics'] as EvidenceCategory[]).map((category) => (
            <button
              key={category}
              onClick={() => handleCategoryChange(category)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
              {category !== 'all' && (
                <span className="ml-1.5 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                  {evidenceTraces.filter(e => e.category === category).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="flex h-[600px]">
        <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
          <div className="p-4 space-y-3">
            {Object.entries(evidenceByPage)
              .sort(([a], [b]) => Number(a) - Number(b))
              .map(([page, evidenceList]) => (
                <div key={page} className="mb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-xs font-semibold text-gray-500 uppercase">Page {page}</span>
                    <span className="text-xs text-gray-400">({evidenceList.length} items)</span>
                  </div>
                  {evidenceList.map((evidence) => (
                    <div
                      key={evidence.id}
                      onClick={() => handleEvidenceClick(evidence)}
                      onMouseEnter={() => setHoveredEvidenceId(evidence.id)}
                      onMouseLeave={() => setHoveredEvidenceId(null)}
                      className={`p-3 rounded-lg border-2 cursor-pointer transition-all mb-2 ${
                        selectedEvidence?.id === evidence.id
                          ? 'border-blue-500 bg-blue-50 shadow-md'
                          : hoveredEvidenceId === evidence.id
                          ? 'border-gray-400 bg-gray-50 shadow-sm'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(evidence.category)}`}>
                          {evidence.category}
                        </span>
                        {evidence.severity && (
                          <span className={`text-xs ${getSeverityColor(evidence.severity)}`}>
                            {evidence.severity}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                        {evidence.text_snippet}
                      </p>
                      {evidence.page_number && (
                        <div className="flex items-center space-x-1 text-xs text-gray-500">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <span>Page {evidence.page_number}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-gray-50">
          {selectedEvidence ? (
            <div className="p-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-lg text-sm font-medium ${getCategoryColor(selectedEvidence.category)}`}>
                      {selectedEvidence.category}
                    </span>
                    {selectedEvidence.severity && (
                      <span className={`px-2 py-1 rounded text-sm ${getSeverityColor(selectedEvidence.severity)}`}>
                        Severity: {selectedEvidence.severity}
                      </span>
                    )}
                    {selectedEvidence.confidence && (
                      <span className="px-2 py-1 rounded text-sm bg-gray-100 text-gray-700">
                        Confidence: {(selectedEvidence.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Evidence Text</h4>
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                      {selectedEvidence.text_snippet}
                    </p>
                  </div>
                </div>

                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Rationale</h4>
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                      {selectedEvidence.rationale}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  {selectedEvidence.page_number && (
                    <div>
                      <span className="text-xs font-semibold text-gray-600">Page Number</span>
                      <p className="text-sm text-gray-800 mt-1">Page {selectedEvidence.page_number}</p>
                    </div>
                  )}
                  {selectedEvidence.score_impact && (
                    <div>
                      <span className="text-xs font-semibold text-gray-600">Score Impact</span>
                      <p className={`text-sm font-medium mt-1 ${selectedEvidence.score_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {selectedEvidence.score_impact > 0 ? '+' : ''}{selectedEvidence.score_impact.toFixed(1)} points
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
                <p className="text-gray-600">Select an evidence item to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}

export default EvidenceVisualization;
