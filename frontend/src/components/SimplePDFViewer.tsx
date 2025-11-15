'use client';

import { useEffect, useState } from 'react';

interface SimplePDFViewerProps {
  pdfUrl: string | null;
  fileName?: string;
}

export default function SimplePDFViewer({ pdfUrl, fileName }: SimplePDFViewerProps) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (pdfUrl) {
      setLoading(true);
      setError(null);

      // Set a timeout to detect if iframe fails to load
      const timeout = setTimeout(() => {
        setLoading(false);
      }, 3000);

      return () => clearTimeout(timeout);
    }
  }, [pdfUrl]);

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <p className="text-gray-500">No PDF loaded</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative bg-gray-100">
      {/* Download button for large files */}
      {pdfUrl.startsWith('blob:') && (
        <div className="absolute top-4 right-4 z-20">
          <a
            href={pdfUrl}
            download={fileName || 'document.pdf'}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-lg"
            title="Download PDF"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm">Download</span>
          </a>
        </div>
      )}

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading PDF...</p>
            <p className="text-xs text-gray-500 mt-2">This may take a moment for large files</p>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
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
      )}

      <iframe
        src={pdfUrl}
        className="w-full h-full border-0"
        title="PDF Viewer"
        onLoad={() => {
          setLoading(false);
          setError(null);
        }}
        onError={() => {
          setLoading(false);
          setError('Failed to load PDF. The file may be corrupted or in an unsupported format.');
        }}
      />
    </div>
  );
}
