'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

// Set up PDF.js worker - use unpkg CDN for better reliability
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
  console.log('📄 PDF.js worker configured:', pdfjs.GlobalWorkerOptions.workerSrc);
}

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

interface PDFViewerWithHighlightsProps {
  pdfUrl: string | null;
  evidenceTraces: EvidenceItem[];
  onEvidenceClick?: (evidence: EvidenceItem) => void;
  selectedEvidenceId?: string | null;
}

const getCategoryColor = (category: string): string => {
  switch (category) {
    case 'bias':
      return 'rgba(239, 68, 68, 0.4)'; // red-500
    case 'methodology':
      return 'rgba(59, 130, 246, 0.4)'; // blue-500
    case 'reproducibility':
      return 'rgba(34, 197, 94, 0.4)'; // green-500
    case 'statistics':
      return 'rgba(168, 85, 247, 0.4)'; // purple-500
    default:
      return 'rgba(156, 163, 175, 0.4)'; // gray-400
  }
};

const getCategoryBorderColor = (category: string): string => {
  switch (category) {
    case 'bias':
      return '#ef4444'; // red-500
    case 'methodology':
      return '#3b82f6'; // blue-500
    case 'reproducibility':
      return '#22c55e'; // green-500
    case 'statistics':
      return '#a855f7'; // purple-500
    default:
      return '#9ca3af'; // gray-400
  }
};

export default function PDFViewerWithHighlights({
  pdfUrl,
  evidenceTraces = [],
  onEvidenceClick,
  selectedEvidenceId
}: PDFViewerWithHighlightsProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useFallback, setUseFallback] = useState(false);
  const [pageDimensions, setPageDimensions] = useState<Map<number, { width: number; height: number }>>(new Map());
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);
  const [visiblePages, setVisiblePages] = useState<Set<number>>(new Set([1, 2, 3])); // Start with first 3 pages

  // Group evidence by page
  const evidenceByPage = evidenceTraces.reduce((acc, evidence) => {
    const page = evidence.page_number || 1;
    if (!acc[page]) acc[page] = [];
    acc[page].push(evidence);
    return acc;
  }, {} as Record<number, EvidenceItem[]>);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    console.log('✅ PDF loaded successfully! Pages:', numPages);
    setNumPages(numPages);
    setLoading(false);
    setError(null);
  }, []);

  const onDocumentLoadError = useCallback((error: Error) => {
    console.error('PDF load error:', error);
    console.error('PDF URL:', pdfUrl);
    console.error('Error details:', error.message, error.stack);
    setError(`Failed to load PDF: ${error.message || 'Unknown error'}`);
    setLoading(false);
    // Use fallback iframe after a delay
    setTimeout(() => {
      setUseFallback(true);
    }, 2000);
  }, [pdfUrl]);

  const onPageLoadSuccess = useCallback((page: any, pageNum: number) => {
    const viewport = page.getViewport({ scale });
    setPageDimensions(prev => {
      const newMap = new Map(prev);
      newMap.set(pageNum, { width: viewport.width, height: viewport.height });
      return newMap;
    });
  }, [scale]);

  // Intersection Observer for lazy loading pages
  useEffect(() => {
    if (!containerRef.current || numPages === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const pageNum = parseInt(entry.target.getAttribute('data-page') || '1');
            setVisiblePages(prev => {
              const newSet = new Set(prev);
              newSet.add(pageNum);
              // Also add adjacent pages for smooth scrolling
              if (pageNum > 1) newSet.add(pageNum - 1);
              if (pageNum < numPages) newSet.add(pageNum + 1);
              return newSet;
            });
          }
        });
      },
      { rootMargin: '300px' } // Load pages 300px before they're visible
    );

    // Observe all page containers - use a small delay to ensure DOM is ready
    const timeoutId = setTimeout(() => {
      pageRefs.current.forEach((element) => {
        if (element) observer.observe(element);
      });
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      observer.disconnect();
    };
  }, [numPages, visiblePages]);

  // Scroll to selected evidence page
  useEffect(() => {
    if (selectedEvidenceId && evidenceTraces.length > 0) {
      const selectedEvidence = evidenceTraces.find(e => e.id === selectedEvidenceId);
      if (selectedEvidence && selectedEvidence.page_number) {
        const targetPage = selectedEvidence.page_number;
        setPageNumber(targetPage);
        setVisiblePages(prev => {
          const newSet = new Set(prev);
          newSet.add(targetPage);
          // Add surrounding pages
          if (targetPage > 1) newSet.add(targetPage - 1);
          if (targetPage < numPages) newSet.add(targetPage + 1);
          return newSet;
        });
        setTimeout(() => {
          const pageElement = pageRefs.current.get(targetPage);
          if (pageElement) {
            pageElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }, 100);
      }
    }
  }, [selectedEvidenceId, evidenceTraces, numPages]);

  // Render highlights for a page
  const renderHighlights = (pageNum: number) => {
    const pageEvidence = evidenceByPage[pageNum] || [];
    if (pageEvidence.length === 0) return null;

    const dimensions = pageDimensions.get(pageNum);
    if (!dimensions) return null;

    return (
      <div
        className="absolute top-0 left-0 pointer-events-none"
        style={{
          width: `${dimensions.width}px`,
          height: `${dimensions.height}px`,
        }}
      >
        {pageEvidence.map((evidence) => {
          const bbox = evidence.bounding_box;
          if (!bbox) return null;

          const left = bbox.x * dimensions.width;
          const top = bbox.y * dimensions.height;
          const width = bbox.width * dimensions.width;
          const height = bbox.height * dimensions.height;

          const isSelected = selectedEvidenceId === evidence.id;
          const borderColor = getCategoryBorderColor(evidence.category);
          const bgColor = getCategoryColor(evidence.category);

          return (
            <div
              key={evidence.id}
              onClick={(e) => {
                e.stopPropagation();
                if (onEvidenceClick) {
                  onEvidenceClick(evidence);
                }
              }}
              className="absolute cursor-pointer transition-all pointer-events-auto group"
              style={{
                left: `${left}px`,
                top: `${top}px`,
                width: `${width}px`,
                height: `${height}px`,
                backgroundColor: bgColor,
                border: `2px solid ${borderColor}`,
                borderRadius: '4px',
                boxShadow: isSelected ? `0 0 0 3px ${borderColor}` : 'none',
                zIndex: isSelected ? 20 : 10,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.7';
                e.currentTarget.style.transform = 'scale(1.02)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1';
                e.currentTarget.style.transform = 'scale(1)';
              }}
              title={`${evidence.category}: ${evidence.text_snippet.substring(0, 50)}...`}
            >
              {/* Tooltip on hover */}
              <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-30 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap max-w-xs truncate">
                {evidence.text_snippet.substring(0, 100)}...
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Convert data URL to blob URL for better performance with react-pdf
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!pdfUrl) {
      setBlobUrl(null);
      setLoading(false);
      return;
    }

    // If it's already a blob URL, use it directly
    if (pdfUrl.startsWith('blob:')) {
      setBlobUrl(pdfUrl);
      setLoading(true); // Reset loading when blobUrl changes
      return;
    }

    // If it's a data URL, convert to blob URL for better performance
    if (pdfUrl.startsWith('data:')) {
      setLoading(true); // Start loading
      try {
        // Extract base64 data from data URL
        const base64Data = pdfUrl.split(',')[1];
        if (!base64Data) {
          throw new Error('Invalid data URL format');
        }
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'application/pdf' });
        const newBlobUrl = URL.createObjectURL(blob);
        setBlobUrl(newBlobUrl);
        console.log('✅ Converted data URL to blob URL, size:', blob.size, 'bytes');
      } catch (error) {
        console.error('Failed to convert data URL to blob:', error);
        // Fallback to data URL if conversion fails
        setBlobUrl(pdfUrl);
      }
      return;
    }

    // Regular URL
    setBlobUrl(pdfUrl);
    setLoading(true); // Reset loading when blobUrl changes
  }, [pdfUrl]);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (blobUrl && blobUrl.startsWith('blob:') && pdfUrl && !pdfUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [blobUrl, pdfUrl]);

  // Debug: Log PDF URL and state
  useEffect(() => {
    console.log('📄 PDFViewerWithHighlights State:');
    console.log('  - pdfUrl (original):', pdfUrl?.substring(0, 50) + '...');
    console.log('  - blobUrl (converted):', blobUrl?.substring(0, 50) + '...');
    console.log('  - pdfUrl type:', typeof pdfUrl);
    console.log('  - pdfUrl starts with blob?:', pdfUrl?.startsWith('blob:'));
    console.log('  - pdfUrl starts with data?:', pdfUrl?.startsWith('data:'));
    console.log('  - loading:', loading);
    console.log('  - error:', error);
    console.log('  - numPages:', numPages);
    console.log('  - useFallback:', useFallback);
    console.log('  - Worker path:', pdfjs.GlobalWorkerOptions.workerSrc);
  }, [pdfUrl, blobUrl, loading, error, numPages, useFallback]);

  // Timeout to detect if PDF never loads
  useEffect(() => {
    if (!blobUrl || numPages > 0) return;
    
    const timeout = setTimeout(() => {
      if (loading && numPages === 0 && !error) {
        console.warn('⚠️ PDF loading timeout - no response after 10 seconds');
        console.warn('  - blobUrl exists:', !!blobUrl);
        console.warn('  - Worker path:', pdfjs.GlobalWorkerOptions.workerSrc);
        setError('PDF loading timeout. The file may be too large or corrupted.');
        setLoading(false);
      }
    }, 10000);

    return () => clearTimeout(timeout);
  }, [blobUrl, loading, numPages, error]);

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <p className="text-gray-500">No PDF loaded</p>
      </div>
    );
  }

  // Fallback to iframe if react-pdf fails
  if (useFallback) {
    return (
      <div className="w-full h-full">
        <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2 text-xs text-yellow-800">
          Using fallback PDF viewer (react-pdf failed to load)
        </div>
        <iframe
          src={pdfUrl || ''}
          className="w-full h-full border-0"
          title="PDF Viewer"
        />
      </div>
    );
  }

  if (error && !useFallback) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600 mb-2 font-semibold">PDF Load Error</p>
          <p className="text-sm text-gray-600 mb-4">{error}</p>
          <p className="text-xs text-gray-500">Falling back to iframe viewer...</p>
        </div>
      </div>
    );
  }

  if (loading && numPages === 0) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading PDF...</p>
          <p className="text-xs text-gray-500 mt-2">This may take a moment for large files</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-auto bg-gray-100 relative">
      {/* Controls */}
      <div className="sticky top-0 z-30 bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
            disabled={pageNumber === 1}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700">
            Page {pageNumber} of {numPages}
          </span>
          <button
            onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
            disabled={pageNumber === numPages}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
          <button
            onClick={() => setPageNumber(1)}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          >
            First
          </button>
          <button
            onClick={() => setPageNumber(numPages)}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          >
            Last
          </button>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setScale(Math.max(0.5, scale - 0.25))}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded"
          >
            -
          </button>
          <span className="text-sm text-gray-700 w-16 text-center">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={() => setScale(Math.min(3, scale + 0.25))}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded"
          >
            +
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="sticky top-[49px] z-20 bg-white border-b border-gray-200 px-4 py-2 flex items-center space-x-4 text-xs">
        <span className="font-semibold text-gray-700">Evidence Types:</span>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('bias'), borderColor: getCategoryBorderColor('bias') }}></div>
          <span>Bias</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('methodology'), borderColor: getCategoryBorderColor('methodology') }}></div>
          <span>Methodology</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('reproducibility'), borderColor: getCategoryBorderColor('reproducibility') }}></div>
          <span>Reproducibility</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('statistics'), borderColor: getCategoryBorderColor('statistics') }}></div>
          <span>Statistics</span>
        </div>
        {evidenceTraces.length > 0 && (
          <span className="ml-4 text-gray-600">
            {evidenceTraces.length} evidence item{evidenceTraces.length !== 1 ? 's' : ''} found
          </span>
        )}
      </div>

      {/* PDF Document */}
      <div ref={containerRef} className="p-4 flex flex-col items-center">
        {blobUrl && (
          <Document
            file={blobUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading={
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            }
            className="flex flex-col items-center"
            error={
              <div className="text-center py-8 text-red-600">
                <p>Failed to load PDF document</p>
                <button
                  onClick={() => setUseFallback(true)}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Use Fallback Viewer
                </button>
              </div>
            }
          >
          {/* Render all pages but only load visible ones */}
          {numPages > 0 && Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => {
            // Always render first 5 pages, current page, and pages with evidence
            const hasEvidence = evidenceByPage[pageNum] && evidenceByPage[pageNum].length > 0;
            const shouldRender = 
              pageNum <= 5 || 
              visiblePages.has(pageNum) || 
              pageNum === pageNumber || 
              hasEvidence;
            
            return (
              <div
                key={pageNum}
                data-page={pageNum}
                ref={(el) => {
                  if (el) {
                    pageRefs.current.set(pageNum, el);
                  } else {
                    pageRefs.current.delete(pageNum);
                  }
                }}
                className="relative mb-4 shadow-lg bg-white"
                style={{ 
                  display: 'inline-block',
                  minHeight: shouldRender ? 'auto' : '800px', // Placeholder height for non-rendered pages
                }}
              >
                {shouldRender ? (
                  <>
                    <Page
                      pageNumber={pageNum}
                      scale={scale}
                      onLoadSuccess={(page) => onPageLoadSuccess(page, pageNum)}
                      loading={
                        <div className="flex items-center justify-center w-full h-96 bg-gray-100">
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                        </div>
                      }
                      className="border border-gray-200"
                      renderTextLayer={true}
                      renderAnnotationLayer={true}
                    />
                    {/* Highlights overlay */}
                    {renderHighlights(pageNum)}
                  </>
                ) : (
                  <div className="flex items-center justify-center w-full h-96 bg-gray-100 border border-gray-200">
                    <div className="text-center text-gray-500">
                      <p className="text-sm font-medium">Page {pageNum}</p>
                      {hasEvidence && (
                        <p className="text-xs mt-1 text-blue-600 font-semibold">
                          {evidenceByPage[pageNum].length} evidence item{evidenceByPage[pageNum].length !== 1 ? 's' : ''}
                        </p>
                      )}
                      <p className="text-xs mt-2">Scroll to load page</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          </Document>
        )}
        {!blobUrl && pdfUrl && (
          <div className="text-center py-8 text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Preparing PDF...</p>
          </div>
        )}
        {!blobUrl && !pdfUrl && (
          <div className="text-center py-8 text-gray-500">
            <p>No PDF file available</p>
          </div>
        )}
      </div>
    </div>
  );
}
