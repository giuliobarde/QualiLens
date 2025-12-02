'use client';

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { PDFDocument } from 'pdf-lib';

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
  onExportFunctionsReady?: (functions: { exportCurrentPage: () => void; exportAllPages: () => void }) => void;
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
  onExportFunctionsReady
}: EnhancedPDFViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());
  const highlightCanvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());

  const [pdf, setPdf] = useState<pdfjsLib.PDFDocumentProxy | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredEvidenceId, setHoveredEvidenceId] = useState<string | null>(null);
  const [hoveredEvidence, setHoveredEvidence] = useState<EvidenceItem | null>(null);
  const [hoverPosition, setHoverPosition] = useState<{ x: number; y: number } | null>(null);
  const [showHighlights, setShowHighlights] = useState<boolean>(true); // Default: highlights visible
  const [enabledCategories, setEnabledCategories] = useState<Set<string>>(new Set(['bias', 'methodology', 'reproducibility', 'statistics'])); // All categories enabled by default
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const pageRenderingRef = useRef<Set<number>>(new Set());
  const lastScrolledEvidenceIdRef = useRef<string | null>(null);

  // Filter evidence by enabled categories - use useMemo to prevent recreation on every render
  const filteredEvidence = useMemo(() => {
    // Filter by enabled categories only (no external category filter)
    return evidenceTraces.filter(e => enabledCategories.has(e.category));
  }, [evidenceTraces, enabledCategories]);

  // Group evidence by page - use useMemo to prevent recreation on every render
  const evidenceByPage = useMemo(() => {
    return filteredEvidence.reduce((acc, evidence) => {
      const page = evidence.page_number || 1;
      if (!acc[page]) acc[page] = [];
      acc[page].push(evidence);
      return acc;
    }, {} as Record<number, EvidenceItem[]>);
  }, [filteredEvidence]);

  // Debug evidence data
  useEffect(() => {
    console.log('🔍 EnhancedPDFViewer Evidence Debug:');
    console.log('- Total evidence traces:', evidenceTraces.length);
    console.log('- Filtered evidence:', filteredEvidence.length);
    
    const pageSummary = Object.keys(evidenceByPage).map(p => {
      const pageNum = Number(p);
      return { page: pageNum, count: evidenceByPage[pageNum].length, evidenceIds: evidenceByPage[pageNum].map(e => e.id) };
    });
    console.log('- Evidence by page:', pageSummary);
    console.log('- Pages with evidence:', pageSummary.map(p => p.page).sort((a, b) => a - b));
    
    // Show detailed breakdown
    filteredEvidence.forEach((ev, idx) => {
      console.log(`- Evidence ${idx + 1}/${filteredEvidence.length}:`, {
        id: ev.id,
        category: ev.category,
        page: ev.page_number,
        hasBbox: !!ev.bounding_box,
        bbox: ev.bounding_box,
        textSnippet: ev.text_snippet?.substring(0, 80)
      });
    });
  }, [evidenceTraces, filteredEvidence, evidenceByPage]);

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

  // Render highlights for a page - use useCallback with stable dependencies
  const renderHighlights = useCallback((pageNum: number, pageWidth: number, pageHeight: number) => {
    const highlightCanvas = highlightCanvasRefs.current.get(pageNum);
    if (!highlightCanvas) {
      console.warn(`⚠️ No highlight canvas for page ${pageNum}`);
      return;
    }

    const ctx = highlightCanvas.getContext('2d');
    if (!ctx) {
      console.warn(`⚠️ Could not get 2d context for highlight canvas on page ${pageNum}`);
      return;
    }

    // Set canvas size first
    highlightCanvas.width = pageWidth;
    highlightCanvas.height = pageHeight;

    // Clear previous highlights
    ctx.clearRect(0, 0, highlightCanvas.width, highlightCanvas.height);

    // If highlights are disabled, just clear and return
    if (!showHighlights) {
      return;
    }

    const pageEvidence = evidenceByPage[pageNum] || [];
    
    console.log(`🎨 Rendering highlights for page ${pageNum}:`, {
      pageWidth,
      pageHeight,
      evidenceCount: pageEvidence.length,
      evidenceIds: pageEvidence.map(e => e.id)
    });
    
    if (pageEvidence.length === 0) {
      console.log(`ℹ️ No evidence for page ${pageNum}`);
      return;
    }

    let renderedCount = 0;
    let skippedCount = 0;

    pageEvidence.forEach((evidence, idx) => {
      const bbox = evidence.bounding_box;
      if (!bbox) {
        console.warn(`⚠️ Evidence ${evidence.id} on page ${pageNum} has no bounding box`);
        skippedCount++;
        return;
      }

      // Validate bounding box values
      if (typeof bbox.x !== 'number' || typeof bbox.y !== 'number' || 
          typeof bbox.width !== 'number' || typeof bbox.height !== 'number') {
        console.warn(`⚠️ Evidence ${evidence.id} on page ${pageNum} has invalid bbox types:`, bbox);
        skippedCount++;
        return;
      }

      const x = bbox.x * pageWidth;
      const y = bbox.y * pageHeight;
      const width = bbox.width * pageWidth;
      const height = bbox.height * pageHeight;

      // Validate coordinates
      if (isNaN(x) || isNaN(y) || isNaN(width) || isNaN(height)) {
        console.warn(`⚠️ Evidence ${evidence.id} on page ${pageNum} has NaN coordinates:`, { x, y, width, height });
        skippedCount++;
        return;
      }

      // Validate coordinates are within reasonable bounds
      if (x < 0 || y < 0 || width <= 0 || height <= 0 || 
          x + width > pageWidth * 1.1 || y + height > pageHeight * 1.1) {
        console.warn(`⚠️ Evidence ${evidence.id} on page ${pageNum} has out-of-bounds coordinates:`, {
          x, y, width, height, pageWidth, pageHeight
        });
        // Still render, but clamp to bounds
        const clampedX = Math.max(0, Math.min(x, pageWidth - 10));
        const clampedY = Math.max(0, Math.min(y, pageHeight - 10));
        const clampedWidth = Math.min(width, pageWidth - clampedX);
        const clampedHeight = Math.min(height, pageHeight - clampedY);
        
        if (clampedWidth > 0 && clampedHeight > 0) {
          const colors = getCategoryColor(evidence.category);
          ctx.fillStyle = colors.fill;
          ctx.fillRect(clampedX, clampedY, clampedWidth, clampedHeight);
          ctx.strokeStyle = colors.stroke;
          ctx.lineWidth = 1;
          ctx.strokeRect(clampedX, clampedY, clampedWidth, clampedHeight);
          renderedCount++;
          console.log(`✅ Rendered clamped highlight for evidence ${evidence.id} on page ${pageNum}`);
        } else {
          skippedCount++;
        }
        return;
      }

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

      renderedCount++;
      console.log(`✅ Rendered highlight ${idx + 1}/${pageEvidence.length} for evidence ${evidence.id} (${evidence.category}) on page ${pageNum}:`, {
        bbox: { x: bbox.x, y: bbox.y, width: bbox.width, height: bbox.height },
        canvasCoords: { x, y, width, height }
      });
    });

    console.log(`📊 Highlight rendering summary for page ${pageNum}: ${renderedCount} rendered, ${skippedCount} skipped`);
  }, [evidenceByPage, selectedEvidenceId, hoveredEvidenceId, showHighlights, enabledCategories]);

  // Render a specific page
  const renderPage = useCallback(async (pageNum: number) => {
    if (!pdf || pageRenderingRef.current.has(pageNum)) return;

    pageRenderingRef.current.add(pageNum);

    try {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale });

      // Render PDF page to canvas
      const canvas = canvasRefs.current.get(pageNum);
      if (!canvas) {
        console.warn(`⚠️ No canvas element for page ${pageNum}`);
        return;
      }

      const context = canvas.getContext('2d');
      if (!context) {
        console.warn(`⚠️ Could not get 2d context for page ${pageNum}`);
        return;
      }

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      // Set canvas display size to match viewport
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
        // @ts-ignore - PDF.js render context type definition may vary
      };

      await page.render(renderContext as any).promise;

      // Get highlight canvas and ensure it matches PDF canvas size
      const highlightCanvas = highlightCanvasRefs.current.get(pageNum);
      if (highlightCanvas) {
        highlightCanvas.width = viewport.width;
        highlightCanvas.height = viewport.height;
        highlightCanvas.style.width = `${viewport.width}px`;
        highlightCanvas.style.height = `${viewport.height}px`;
        highlightCanvas.style.position = 'absolute';
        highlightCanvas.style.top = '0';
        highlightCanvas.style.left = '0';
      }

      // Render highlights on separate canvas after a short delay to ensure canvas is ready
      setTimeout(() => {
        renderHighlights(pageNum, viewport.width, viewport.height);
      }, 50);

      console.log(`✅ Rendered page ${pageNum} (${viewport.width}x${viewport.height})`);
    } catch (err) {
      console.error(`❌ Failed to render page ${pageNum}:`, err);
    } finally {
      pageRenderingRef.current.delete(pageNum);
    }
  }, [pdf, scale, renderHighlights]);

  // Re-render highlights when selection, filter, or visibility changes
  useEffect(() => {
    if (!pdf) {
      console.log('⏳ Waiting for PDF to load before rendering highlights');
      return;
    }

    console.log('🔄 Re-rendering highlights for all pages:', {
      numPages,
      selectedEvidenceId,
      hoveredEvidenceId,
      showHighlights,
      enabledCategories: Array.from(enabledCategories),
      filteredEvidenceCount: filteredEvidence.length
    });

    // Use a timeout to batch updates and avoid infinite loops
    const timeoutId = setTimeout(() => {
      // Render highlights for all pages that have evidence
      const pagesWithEvidence = Object.keys(evidenceByPage).map(p => Number(p));
      console.log(`🎨 Re-rendering highlights for pages with evidence: ${pagesWithEvidence.join(', ')}`);
      
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const canvas = canvasRefs.current.get(pageNum);
        const pageEvidence = evidenceByPage[pageNum] || [];
        
        if (pageEvidence.length > 0) {
          if (canvas && canvas.width > 0) {
            // Canvas exists and is rendered, render highlights
            renderHighlights(pageNum, canvas.width, canvas.height);
          } else {
            // Canvas doesn't exist yet, but we have evidence - log a warning
            console.warn(`⚠️ Page ${pageNum} has ${pageEvidence.length} evidence items but canvas not rendered yet`);
          }
        }
      }
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [selectedEvidenceId, hoveredEvidenceId, showHighlights, enabledCategories, pdf, numPages, evidenceByPage, renderHighlights]);

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

    // Also render pages that have evidence (render all pages with evidence, not just first 5)
    const evidencePages = Object.keys(evidenceByPage)
      .map(p => Number(p))
      .filter(p => p >= 1 && p <= numPages);
    evidencePages.forEach(pageNum => {
      pagesToRender.add(pageNum);
    });
    
    console.log(`📄 Pages to render: ${Array.from(pagesToRender).sort((a, b) => a - b).join(', ')}`);
    console.log(`📊 Pages with evidence: ${evidencePages.sort((a, b) => a - b).join(', ')}`);

    // Render all pages in the set
    pagesToRender.forEach(pageNum => {
      if (!pageRenderingRef.current.has(pageNum)) {
        renderPage(pageNum);
      }
    });
  }, [pdf, numPages, scale, currentPage, renderPage, evidenceByPage]);

  // Re-render highlights when current page changes (in case page was already rendered)
  useEffect(() => {
    if (!pdf || numPages === 0) return;
    
    const canvas = canvasRefs.current.get(currentPage);
    const pageEvidence = evidenceByPage[currentPage] || [];
    
    if (canvas && canvas.width > 0 && pageEvidence.length > 0) {
      console.log(`🔄 Re-rendering highlights for current page ${currentPage} (has ${pageEvidence.length} evidence items)`);
      // Small delay to ensure canvas is ready
      setTimeout(() => {
        renderHighlights(currentPage, canvas.width, canvas.height);
      }, 100);
    }
  }, [currentPage, pdf, numPages, evidenceByPage, renderHighlights]);

  // Navigate to page when evidence is selected (only on click, not on hover)
  useEffect(() => {
    if (!selectedEvidenceId || !pdf || numPages === 0 || evidenceTraces.length === 0) return;

    // Only scroll if this is a new evidence selection (not the same one we already scrolled to)
    if (lastScrolledEvidenceIdRef.current === selectedEvidenceId) {
      return;
    }

    const selectedEvidence = evidenceTraces.find(e => e.id === selectedEvidenceId);
    if (selectedEvidence && selectedEvidence.page_number) {
      const targetPage = selectedEvidence.page_number;
      
      // Validate page number is within bounds
      if (targetPage >= 1 && targetPage <= numPages) {
        console.log(`📍 Navigating to page ${targetPage} for evidence ${selectedEvidenceId}`);
        
        // Mark this evidence as scrolled to
        lastScrolledEvidenceIdRef.current = selectedEvidenceId;
        
        // Set current page to navigate to the evidence location
        setCurrentPage(targetPage);
        
        // Ensure the page is rendered
        if (!pageRenderingRef.current.has(targetPage)) {
          renderPage(targetPage);
        }
        
        // Scroll to the page container after a short delay to ensure rendering
        setTimeout(() => {
          if (containerRef.current) {
            // Scroll the container to top to show the current page
            containerRef.current.scrollTop = 0;
          }
        }, 200);
      } else {
        console.warn(`⚠️ Invalid page number ${targetPage} for evidence ${selectedEvidenceId} (valid range: 1-${numPages})`);
      }
    }
  }, [selectedEvidenceId, pdf, numPages, evidenceTraces, renderPage]);

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
    setHoveredEvidence(foundEvidence);
    setHoverPosition(foundEvidence ? { x: event.clientX, y: event.clientY } : null);
    canvas.style.cursor = foundEvidence ? 'pointer' : 'default';
  };

  // Export screenshot of current page with evidence highlights
  const exportCurrentPage = useCallback(() => {
    const pdfCanvas = canvasRefs.current.get(currentPage);
    const highlightCanvas = highlightCanvasRefs.current.get(currentPage);

    if (!pdfCanvas) {
      console.warn('No PDF canvas found for current page');
      return;
    }

    try {
      // Create a new canvas to combine both layers
      const combinedCanvas = document.createElement('canvas');
      combinedCanvas.width = pdfCanvas.width;
      combinedCanvas.height = pdfCanvas.height;
      const ctx = combinedCanvas.getContext('2d');

      if (!ctx) {
        console.error('Failed to get 2D context for combined canvas');
        return;
      }

      // Draw PDF canvas first (background)
      ctx.drawImage(pdfCanvas, 0, 0);

      // Draw highlight canvas on top if it exists and highlights are enabled
      if (highlightCanvas && showHighlights && highlightCanvas.width > 0 && highlightCanvas.height > 0) {
        ctx.drawImage(highlightCanvas, 0, 0);
      }

      // Convert to blob and download
      combinedCanvas.toBlob((blob) => {
        if (!blob) {
          console.error('Failed to create blob from canvas');
          return;
        }

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const pageSuffix = numPages > 1 ? `_page-${currentPage}` : '';
        const downloadFileName = fileName 
          ? `${fileName.replace(/\.pdf$/i, '')}${pageSuffix}_evidence-${timestamp}.png`
          : `document${pageSuffix}_evidence-${timestamp}.png`;
        
        link.href = url;
        link.download = downloadFileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        console.log(`✅ Screenshot exported: ${downloadFileName}`);
      }, 'image/png');
    } catch (error) {
      console.error('Error exporting screenshot:', error);
    }
  }, [currentPage, showHighlights, numPages, fileName]);

  // Export all pages with evidence highlights
  const exportAllPages = useCallback(async () => {
    if (!pdf || numPages === 0) {
      console.warn('PDF not loaded or no pages available');
      return;
    }

    setIsExporting(true);

    try {
      // First, ensure all pages are rendered
      const pagesToRender: number[] = [];
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfCanvas = canvasRefs.current.get(pageNum);
        if (!pdfCanvas || pdfCanvas.width === 0) {
          pagesToRender.push(pageNum);
        }
      }

      // Render missing pages
      if (pagesToRender.length > 0) {
        console.log(`Rendering ${pagesToRender.length} missing pages before export...`);
        for (const pageNum of pagesToRender) {
          await renderPage(pageNum);
          // Wait for canvas to be ready and highlights to render
          await new Promise(resolve => setTimeout(resolve, 300));
          
          // Ensure highlights are rendered
          const pdfCanvas = canvasRefs.current.get(pageNum);
          if (pdfCanvas && pdfCanvas.width > 0) {
            renderHighlights(pageNum, pdfCanvas.width, pdfCanvas.height);
            await new Promise(resolve => setTimeout(resolve, 100));
          }
        }
      }

      // Ensure highlights are rendered for all pages (including already rendered ones)
      console.log('Ensuring highlights are rendered for all pages...');
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfCanvas = canvasRefs.current.get(pageNum);
        if (pdfCanvas && pdfCanvas.width > 0) {
          renderHighlights(pageNum, pdfCanvas.width, pdfCanvas.height);
        }
      }
      // Wait for all highlights to render
      await new Promise(resolve => setTimeout(resolve, 200));

      // Create a new PDF document
      const pdfDoc = await PDFDocument.create();

      // Process each page and add it to the PDF
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfCanvas = canvasRefs.current.get(pageNum);
        const highlightCanvas = highlightCanvasRefs.current.get(pageNum);

        if (!pdfCanvas || pdfCanvas.width === 0) {
          console.warn(`Page ${pageNum} not rendered, skipping...`);
          continue;
        }

        // Get the original PDF page to get correct dimensions in points
        const pdfPage = await pdf.getPage(pageNum);
        const originalViewport = pdfPage.getViewport({ scale: 1.0 }); // Get unscaled viewport for original dimensions
        
        // Create combined canvas for this page
        const pageCanvas = document.createElement('canvas');
        pageCanvas.width = pdfCanvas.width;
        pageCanvas.height = pdfCanvas.height;
        const ctx = pageCanvas.getContext('2d');

        if (!ctx) {
          console.warn(`Failed to get context for page ${pageNum}`);
          continue;
        }

        // Draw PDF canvas
        ctx.drawImage(pdfCanvas, 0, 0);

        // Draw highlight canvas if enabled
        if (highlightCanvas && showHighlights && highlightCanvas.width > 0 && highlightCanvas.height > 0) {
          ctx.drawImage(highlightCanvas, 0, 0);
        }

        // Convert canvas to PNG image data
        const imageDataUrl = pageCanvas.toDataURL('image/png');
        const imageBytes = await fetch(imageDataUrl).then(res => res.arrayBuffer());
        
        // Embed the image in the PDF
        const image = await pdfDoc.embedPng(imageBytes);
        
        // Use the original viewport dimensions (already in points)
        // The canvas is scaled, but we want the PDF page to match the original PDF size
        const pdfWidth = originalViewport.width;
        const pdfHeight = originalViewport.height;
        
        // Add a new page with the image
        // Scale the image to fit the PDF page dimensions
        const page = pdfDoc.addPage([pdfWidth, pdfHeight]);
        page.drawImage(image, {
          x: 0,
          y: 0,
          width: pdfWidth,
          height: pdfHeight,
        });

        console.log(`✅ Added page ${pageNum} to PDF (${pdfWidth}x${pdfHeight} points)`);
      }

      // Save the PDF
      const pdfBytes = await pdfDoc.save();
      
      // Create blob and download
      // Convert to Uint8Array with ArrayBuffer to satisfy Blob type requirements
      const blob = new Blob([new Uint8Array(pdfBytes)], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const downloadFileName = fileName 
        ? `${fileName.replace(/\.pdf$/i, '')}_evidence-${timestamp}.pdf`
        : `document_evidence-${timestamp}.pdf`;
      
      link.href = url;
      link.download = downloadFileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log(`✅ PDF with ${numPages} pages exported: ${downloadFileName}`);
      setIsExporting(false);
    } catch (error) {
      console.error('Error exporting all pages:', error);
      setIsExporting(false);
    }
  }, [pdf, numPages, showHighlights, fileName, renderPage]);

  // Handle export option selection
  const handleExportOption = useCallback((option: 'current' | 'all') => {
    if (option === 'current') {
      exportCurrentPage();
    } else {
      exportAllPages();
    }
  }, [exportCurrentPage, exportAllPages]);

  // Expose export functions to parent
  useEffect(() => {
    if (onExportFunctionsReady && pdf && numPages > 0) {
      onExportFunctionsReady({
        exportCurrentPage,
        exportAllPages
      });
    }
  }, [onExportFunctionsReady, exportCurrentPage, exportAllPages, pdf, numPages]);

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
    <div className="w-full h-full flex flex-col bg-gray-50">
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
          {/* Highlight Toggle */}
          {filteredEvidence.length > 0 && (
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showHighlights}
                onChange={(e) => setShowHighlights(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
              />
              <span className="text-sm text-gray-700 font-medium">Show Highlights</span>
            </label>
          )}
          
          
          <div className="flex items-center space-x-2 border-l border-gray-300 pl-4">
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
      {evidenceTraces.length > 0 && showHighlights && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center space-x-4 text-xs flex-wrap gap-2">
          <span className="font-semibold text-gray-700">Evidence Highlights:</span>
          
          {(['bias', 'methodology', 'reproducibility', 'statistics'] as const).map((category) => {
            const isEnabled = enabledCategories.has(category);
            const categoryCount = evidenceTraces.filter(e => e.category === category).length;
            const categoryLabel = category.charAt(0).toUpperCase() + category.slice(1);
            
            return (
              <button
                key={category}
                onClick={() => {
                  const newEnabled = new Set(enabledCategories);
                  if (isEnabled) {
                    newEnabled.delete(category);
                  } else {
                    newEnabled.add(category);
                  }
                  setEnabledCategories(newEnabled);
                }}
                className={`flex items-center space-x-1 px-2 py-1 rounded transition-all ${
                  isEnabled
                    ? 'bg-white hover:bg-blue-100 border border-blue-300'
                    : 'bg-gray-200 hover:bg-gray-300 border border-gray-400 opacity-50'
                }`}
                title={`${isEnabled ? 'Hide' : 'Show'} ${categoryLabel} (${categoryCount} items)`}
              >
                <div 
                  className="w-4 h-4 rounded border-2" 
                  style={{ 
                    backgroundColor: isEnabled ? getCategoryColor(category).fill : 'rgba(156, 163, 175, 0.3)',
                    borderColor: isEnabled ? getCategoryColor(category).stroke : '#9ca3af'
                  }}
                ></div>
                <span className={isEnabled ? 'text-gray-700 font-medium' : 'text-gray-500'}>
                  {categoryLabel}
                </span>
                {categoryCount > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    isEnabled ? 'bg-blue-100 text-blue-700' : 'bg-gray-300 text-gray-600'
                  }`}>
                    {categoryCount}
                  </span>
                )}
              </button>
            );
          })}
          
          <span className="ml-4 text-gray-600 font-medium">
            {filteredEvidence.length} evidence item{filteredEvidence.length !== 1 ? 's' : ''} shown
          </span>
        </div>
      )}

      {/* PDF Pages */}
      <div ref={containerRef} className="flex-1 overflow-auto p-4 bg-gray-50">
        <div className="flex flex-col items-center space-y-4">
          {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNum) => {
            const hasEvidence = evidenceByPage[pageNum] && evidenceByPage[pageNum].length > 0;
            return (
            <div
              key={pageNum}
              className="relative bg-white shadow-md rounded-lg overflow-hidden"
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
              {showHighlights && (
              <canvas
                ref={(el) => {
                  if (el) {
                    highlightCanvasRefs.current.set(pageNum, el);
                    // Ensure canvas is properly sized when ref is set
                    const pdfCanvas = canvasRefs.current.get(pageNum);
                    if (pdfCanvas && pdfCanvas.width > 0) {
                      el.width = pdfCanvas.width;
                      el.height = pdfCanvas.height;
                      el.style.width = `${pdfCanvas.width}px`;
                      el.style.height = `${pdfCanvas.height}px`;
                      // Re-render highlights if evidence exists
                      if (evidenceByPage[pageNum] && evidenceByPage[pageNum].length > 0) {
                        setTimeout(() => {
                          renderHighlights(pageNum, pdfCanvas.width, pdfCanvas.height);
                        }, 100);
                      }
                    }
                  }
                }}
                className="absolute top-0 left-0 pointer-events-auto"
                style={{ 
                  cursor: 'default',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  zIndex: 10
                }}
                onClick={(e) => handleCanvasClick(pageNum, e)}
                onMouseMove={(e) => handleCanvasHover(pageNum, e)}
                onMouseLeave={() => {
                  setHoveredEvidenceId(null);
                  setHoveredEvidence(null);
                  setHoverPosition(null);
                }}
              />
              )}

              {/* Score Impact Tooltip */}
              {hoveredEvidence && hoverPosition && hoveredEvidence.score_impact !== undefined && (
                <div
                  className="fixed z-50 bg-gray-900 text-white text-sm rounded-lg shadow-xl p-3 max-w-xs pointer-events-none"
                  style={{
                    left: `${hoverPosition.x + 10}px`,
                    top: `${hoverPosition.y - 10}px`,
                    transform: 'translateY(-100%)'
                  }}
                >
                  <div className="font-semibold mb-1 capitalize">{hoveredEvidence.category}</div>
                  <div className="text-xs text-gray-300 mb-2">{hoveredEvidence.text_snippet.substring(0, 100)}...</div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-400">Score Impact:</span>
                    <span className={`font-bold ${hoveredEvidence.score_impact > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {hoveredEvidence.score_impact > 0 ? '+' : ''}{hoveredEvidence.score_impact.toFixed(1)} points
                    </span>
                  </div>
                  {hoveredEvidence.severity && (
                    <div className="text-xs text-gray-400 mt-1">
                      Severity: <span className="capitalize">{hoveredEvidence.severity}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Page number indicator */}
              <div className="absolute top-2 left-2 bg-gray-900 bg-opacity-75 text-white px-2 py-1 rounded text-xs font-medium">
                Page {pageNum}
                {hasEvidence && (
                  <span className="ml-2 px-1.5 py-0.5 bg-blue-500 rounded text-xs">
                    {evidenceByPage[pageNum].length} evidence
                  </span>
                )}
              </div>
            </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
