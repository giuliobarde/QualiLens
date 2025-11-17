'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';

// Configure PDF.js worker - use a stable known version from CDN or fallback to local
if (typeof window !== 'undefined') {
  // Try using a stable version from unpkg that matches our pdfjs-dist version
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/build/pdf.worker.min.mjs`;
  console.log('📄 PDF.js worker configured:', pdfjsLib.GlobalWorkerOptions.workerSrc);
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

interface EnhancedPDFViewerProps {
  pdfUrl: string | null;
  fileName?: string;
  evidenceTraces?: EvidenceItem[];
  selectedEvidenceId?: string | null;
  onEvidenceClick?: (evidence: EvidenceItem) => void;
  categoryFilter?: string; // 'all' or specific category
}

const getCategoryColor = (category: string): { fill: string; stroke: string } => {
  switch (category) {
    case 'bias':
      return { fill: 'rgba(239, 68, 68, 0.3)', stroke: '#ef4444' }; // red
    case 'methodology':
      return { fill: 'rgba(59, 130, 246, 0.3)', stroke: '#3b82f6' }; // blue
    case 'reproducibility':
      return { fill: 'rgba(34, 197, 94, 0.3)', stroke: '#22c55e' }; // green
    case 'statistics':
      return { fill: 'rgba(168, 85, 247, 0.3)', stroke: '#a855f7' }; // purple
    default:
      return { fill: 'rgba(156, 163, 175, 0.3)', stroke: '#9ca3af' }; // gray
  }
};

export default function EnhancedPDFViewer({
  pdfUrl,
  fileName,
  evidenceTraces = [],
  selectedEvidenceId,
  onEvidenceClick,
  categoryFilter = 'all'
}: EnhancedPDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());
  const highlightCanvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());

  const [pdf, setPdf] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.5);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredEvidenceId, setHoveredEvidenceId] = useState<string | null>(null);
  const [pageRendering, setPageRendering] = useState<Set<number>>(new Set());

  // Filter evidence by category
  const filteredEvidence = categoryFilter === 'all'
    ? evidenceTraces
    : evidenceTraces.filter(e => e.category === categoryFilter);

  // Group evidence by page
  const evidenceByPage = filteredEvidence.reduce((acc, evidence) => {
    const page = evidence.page_number || 1;
    if (!acc[page]) acc[page] = [];
    acc[page].push(evidence);
    return acc;
  }, {} as Record<number, EvidenceItem[]>);

  // Load PDF
  useEffect(() => {
    if (!pdfUrl) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    const loadPDF = async () => {
      try {
        let pdfData: string | ArrayBuffer = pdfUrl;

        // Convert data URL to ArrayBuffer if needed
        if (pdfUrl.startsWith('data:')) {
          const base64 = pdfUrl.split(',')[1];
          const binaryString = atob(base64);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          pdfData = bytes.buffer;
        }

        const loadingTask = pdfjsLib.getDocument(pdfData);
        const pdfDoc = await loadingTask.promise;

        setPdf(pdfDoc);
        setNumPages(pdfDoc.numPages);
        setLoading(false);
        console.log('✅ PDF loaded successfully:', pdfDoc.numPages, 'pages');
      } catch (err: any) {
        console.error('❌ Failed to load PDF:', err);
        setError(err.message || 'Failed to load PDF');
        setLoading(false);
      }
    };

    loadPDF();
  }, [pdfUrl]);

  // Render highlights for a page
  const renderHighlights = useCallback((pageNum: number, pageWidth: number, pageHeight: number) => {
    const highlightCanvas = highlightCanvasRefs.current.get(pageNum);
    if (!highlightCanvas) return;

    const ctx = highlightCanvas.getContext('2d');
    if (!ctx) return;

    // Clear previous highlights
    ctx.clearRect(0, 0, highlightCanvas.width, highlightCanvas.height);

    highlightCanvas.width = pageWidth;
    highlightCanvas.height = pageHeight;

    const pageEvidence = evidenceByPage[pageNum] || [];

    pageEvidence.forEach((evidence) => {
      const bbox = evidence.bounding_box;
      if (!bbox) return;

      const x = bbox.x * pageWidth;
      const y = bbox.y * pageHeight;
      const width = bbox.width * pageWidth;
      const height = bbox.height * pageHeight;

      const colors = getCategoryColor(evidence.category);
      const isSelected = selectedEvidenceId === evidence.id;
      const isHovered = hoveredEvidenceId === evidence.id;

      // Draw highlight rectangle
      ctx.fillStyle = colors.fill;
      ctx.fillRect(x, y, width, height);

      // Draw border
      ctx.strokeStyle = colors.stroke;
      ctx.lineWidth = isSelected ? 3 : isHovered ? 2 : 1;
      ctx.strokeRect(x, y, width, height);

      // Add glow effect for selected/hovered
      if (isSelected || isHovered) {
        ctx.shadowColor = colors.stroke;
        ctx.shadowBlur = isSelected ? 10 : 5;
        ctx.strokeRect(x, y, width, height);
        ctx.shadowBlur = 0;
      }
    });
  }, [evidenceByPage, selectedEvidenceId, hoveredEvidenceId]);

  // Render a specific page
  const renderPage = useCallback(async (pageNum: number) => {
    if (!pdf || pageRendering.has(pageNum)) return;

    setPageRendering(prev => new Set(prev).add(pageNum));

    try {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale });

      // Render PDF page to canvas
      const canvas = canvasRefs.current.get(pageNum);
      if (!canvas) return;

      const context = canvas.getContext('2d');
      if (!context) return;

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      await page.render(renderContext).promise;

      // Render highlights on separate canvas
      renderHighlights(pageNum, viewport.width, viewport.height);

      console.log(`✅ Rendered page ${pageNum}`);
    } catch (err) {
      console.error(`❌ Failed to render page ${pageNum}:`, err);
    } finally {
      setPageRendering(prev => {
        const newSet = new Set(prev);
        newSet.delete(pageNum);
        return newSet;
      });
    }
  }, [pdf, pageRendering, scale, renderHighlights]);

  // Re-render highlights when selection or filter changes
  useEffect(() => {
    if (!pdf) return;

    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const canvas = canvasRefs.current.get(pageNum);
      if (canvas && canvas.width > 0) {
        renderHighlights(pageNum, canvas.width, canvas.height);
      }
    }
  }, [selectedEvidenceId, hoveredEvidenceId, categoryFilter, filteredEvidence, pdf]);

  // Render pages when PDF loads or when currentPage changes
  useEffect(() => {
    if (!pdf || numPages === 0) return;

    // Render current page and adjacent pages for smooth navigation
    const pagesToRender = new Set<number>();

    // Add current page
    pagesToRender.add(currentPage);

    // Add previous and next pages for preloading
    if (currentPage > 1) pagesToRender.add(currentPage - 1);
    if (currentPage < numPages) pagesToRender.add(currentPage + 1);

    // Render all pages in the set
    pagesToRender.forEach(pageNum => {
      renderPage(pageNum);
    });
  }, [pdf, numPages, scale, currentPage, renderPage]);

  // Handle evidence click on canvas
  const handleCanvasClick = (pageNum: number, event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = highlightCanvasRefs.current.get(pageNum);
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / canvas.width;
    const y = (event.clientY - rect.top) / canvas.height;

    const pageEvidence = evidenceByPage[pageNum] || [];

    // Find clicked evidence (reverse order to prioritize top items)
    for (let i = pageEvidence.length - 1; i >= 0; i--) {
      const evidence = pageEvidence[i];
      const bbox = evidence.bounding_box;
      if (!bbox) continue;

      if (
        x >= bbox.x &&
        x <= bbox.x + bbox.width &&
        y >= bbox.y &&
        y <= bbox.y + bbox.height
      ) {
        if (onEvidenceClick) {
          onEvidenceClick(evidence);
        }
        break;
      }
    }
  };

  // Handle evidence hover on canvas
  const handleCanvasHover = (pageNum: number, event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = highlightCanvasRefs.current.get(pageNum);
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / canvas.width;
    const y = (event.clientY - rect.top) / canvas.height;

    const pageEvidence = evidenceByPage[pageNum] || [];

    // Find hovered evidence
    let foundEvidence: EvidenceItem | null = null;
    for (let i = pageEvidence.length - 1; i >= 0; i--) {
      const evidence = pageEvidence[i];
      const bbox = evidence.bounding_box;
      if (!bbox) continue;

      if (
        x >= bbox.x &&
        x <= bbox.x + bbox.width &&
        y >= bbox.y &&
        y <= bbox.y + bbox.height
      ) {
        foundEvidence = evidence;
        break;
      }
    }

    setHoveredEvidenceId(foundEvidence?.id || null);
    canvas.style.cursor = foundEvidence ? 'pointer' : 'default';
  };

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <p className="text-gray-500">No PDF loaded</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading PDF...</p>
          <p className="text-xs text-gray-500 mt-2">Preparing evidence visualization...</p>
        </div>
      </div>
    );
  }

  if (error) {
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
          {pdfUrl && (
            <a
              href={pdfUrl}
              download={fileName || 'document.pdf'}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Download PDF</span>
            </a>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col bg-gray-100">
      {/* Controls */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-all"
          >
            Previous
          </button>
          <span className="text-sm text-gray-700 font-medium">
            Page {currentPage} of {numPages}
          </span>
          <button
            onClick={() => setCurrentPage(Math.min(numPages, currentPage + 1))}
            disabled={currentPage === numPages}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-all"
          >
            Next
          </button>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={() => setScale(Math.max(0.5, scale - 0.25))}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium"
          >
            -
          </button>
          <span className="text-sm text-gray-700 w-16 text-center font-medium">
            {Math.round(scale * 100)}%
          </span>
          <button
            onClick={() => setScale(Math.min(3, scale + 0.25))}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium"
          >
            +
          </button>
        </div>

        {pdfUrl.startsWith('blob:') && (
          <a
            href={pdfUrl}
            download={fileName || 'document.pdf'}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all"
            title="Download PDF"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm">Download</span>
          </a>
        )}
      </div>

      {/* Evidence Legend */}
      {filteredEvidence.length > 0 && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center space-x-4 text-xs">
          <span className="font-semibold text-gray-700">Evidence Highlights:</span>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('bias').fill, borderColor: getCategoryColor('bias').stroke }}></div>
            <span>Bias</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('methodology').fill, borderColor: getCategoryColor('methodology').stroke }}></div>
            <span>Methodology</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('reproducibility').fill, borderColor: getCategoryColor('reproducibility').stroke }}></div>
            <span>Reproducibility</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded border-2" style={{ backgroundColor: getCategoryColor('statistics').fill, borderColor: getCategoryColor('statistics').stroke }}></div>
            <span>Statistics</span>
          </div>
          <span className="ml-4 text-gray-600">
            {filteredEvidence.length} evidence item{filteredEvidence.length !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* PDF Pages */}
      <div ref={containerRef} className="flex-1 overflow-auto p-4">
        <div className="flex flex-col items-center space-y-4">
          {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => (
            <div
              key={pageNum}
              className="relative bg-white shadow-lg"
              style={{ display: pageNum === currentPage ? 'block' : 'none' }}
            >
              {/* PDF Canvas */}
              <canvas
                ref={(el) => {
                  if (el) {
                    canvasRefs.current.set(pageNum, el);
                    if (pageNum === currentPage && el.width === 0) {
                      renderPage(pageNum);
                    }
                  }
                }}
                className="block"
              />

              {/* Highlight Canvas Overlay */}
              <canvas
                ref={(el) => {
                  if (el) highlightCanvasRefs.current.set(pageNum, el);
                }}
                className="absolute top-0 left-0 pointer-events-auto"
                onClick={(e) => handleCanvasClick(pageNum, e)}
                onMouseMove={(e) => handleCanvasHover(pageNum, e)}
                onMouseLeave={() => setHoveredEvidenceId(null)}
                style={{ cursor: 'default' }}
              />

              {/* Page number indicator */}
              <div className="absolute top-2 left-2 bg-gray-900 bg-opacity-75 text-white px-2 py-1 rounded text-xs font-medium">
                Page {pageNum}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
