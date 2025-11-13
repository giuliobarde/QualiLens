'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { agentService } from '@/utils/agent-service';
import QualityScoreDisplay from '@/components/QualityScoreDisplay';
import ScrollableAnalysisSections from '@/components/ScrollableAnalysisSections';
import EnhancedProgressBar from '@/components/EnhancedProgressBar';
import CircularScoreDisplay from '@/components/CircularScoreDisplay';

export default function Home() {
  const [query, setQuery] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [pdfContent, setPdfContent] = useState<string | null>(null);
  const [processingType, setProcessingType] = useState<'upload' | 'analysis' | 'detailed_analysis' | 'parallel_processing'>('analysis');
  const [analysisLevel] = useState<'comprehensive'>('comprehensive');
  const [estimatedTime, setEstimatedTime] = useState<number | undefined>(undefined);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Cleanup object URLs on component unmount
  useEffect(() => {
    return () => {
      if (pdfContent && pdfContent.startsWith('blob:')) {
        URL.revokeObjectURL(pdfContent);
      }
    };
  }, [pdfContent]);

  // File selection handler
  const handleFileSelection = useCallback((file: File) => {
    setError(null);
    setAttachedFile(file);
    
    // Determine processing type based on file size
    const fileSize = file.size;
    if (fileSize > 5 * 1024 * 1024) { // > 5MB
      setProcessingType('parallel_processing');
    } else if (fileSize > 2 * 1024 * 1024) { // > 2MB
      setProcessingType('detailed_analysis');
    } else {
      setProcessingType('analysis');
    }
    
    // For large files (>3MB), use object URL instead of base64 to avoid memory issues
    if (fileSize > 3 * 1024 * 1024) {
      const objectUrl = URL.createObjectURL(file);
      setPdfContent(objectUrl);
    } else {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        setPdfContent(result);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf') || 
          file.type.includes('word') || file.name.match(/\.(doc|docx|txt)$/i)) {
        handleFileSelection(file);
      } else {
        setError('Please upload a PDF, Word document, or text file');
      }
    }
  }, [handleFileSelection]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const removeFile = () => {
    // Clean up object URL if it exists
    if (pdfContent && pdfContent.startsWith('blob:')) {
      URL.revokeObjectURL(pdfContent);
    }
    setAttachedFile(null);
    setPdfContent(null);
    setAnalysisResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const exportResults = () => {
    if (!analysisResult) return;
    
    const dataStr = JSON.stringify(analysisResult, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `qualilens-analysis-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() && !attachedFile) return;

    setIsLoading(true);
    
    // Set processing type for text queries
    if (!attachedFile && query.toLowerCase().includes('detailed')) {
      setProcessingType('detailed_analysis');
    } else if (!attachedFile) {
      setProcessingType('analysis');
    }
    
    try {
      let response;
      
      if (attachedFile) {
        // Handle file upload
        console.log('Uploading file:', attachedFile.name);
        setProcessingType('upload');
        response = await agentService.uploadFile(attachedFile);
      } else {
        // Handle text query with comprehensive analysis
        console.log('Processing query:', query, 'with comprehensive analysis');
        const enhancedQuery = `${query} (Analysis level: comprehensive)`;
        response = await agentService.queryAgent({ query: enhancedQuery });
      }
      
      console.log('🔍 FULL RESPONSE DEBUG:');
      console.log('Response success:', response.success);
      console.log('Response agent_used:', (response as any).agent_used);
      console.log('Response tools_used:', (response as any).tools_used);
      console.log('Response classification:', (response as any).classification);
      console.log('Response result keys:', response.result ? Object.keys(response.result) : 'No result');
      console.log('Response result:', response.result);
      
      // Debug the specific result structure
      if (response.result) {
        console.log('🔍 RESULT STRUCTURE DEBUG:');
        console.log('- success:', response.result.success);
        console.log('- tools_used:', response.result.tools_used);
        console.log('- analysis_level:', response.result.analysis_level);
        console.log('- summary:', response.result.summary);
        console.log('- methodology:', response.result.methodology);
        console.log('- bias_detection:', response.result.bias_detection);
        console.log('- statistics:', response.result.statistics);
        console.log('- reproducibility:', response.result.reproducibility);
        console.log('- research_gaps:', response.result.research_gaps);
        console.log('- citations:', response.result.citations);
        
        // CRITICAL: Debug quality score data
        console.log('🎯 QUALITY SCORE DEBUG:');
        console.log('- overall_quality_score:', response.result.overall_quality_score);
        console.log('- quality_breakdown:', response.result.quality_breakdown);
        console.log('- quantitative_scores:', response.result.quantitative_scores);
        console.log('- methodology_quality_rating:', response.result.methodology_quality_rating);
        console.log('- reproducibility_score:', response.result.reproducibility_score);
        console.log('- detected_biases:', response.result.detected_biases);
        console.log('- statistical_concerns:', response.result.statistical_concerns);
      }
      
      // Store the analysis result for display
      if (response.success && response.result) {
        setAnalysisResult(response.result);
        console.log('✅ Analysis result set successfully');
        console.log('Analysis result keys:', Object.keys(response.result));
      } else {
        setAnalysisResult(null);
        const errorMsg = response.error_message || 'Unknown error occurred';
        setError(errorMsg);
        console.error('❌ Analysis failed:', errorMsg);
      }
      
    } catch (error: any) {
      console.error('Error processing request:', error);
      setError(error?.message || 'Failed to process request. Please try again.');
      setAnalysisResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Enhanced Header */}
      <div className="bg-white/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  QualiLens
                </h1>
                <p className="text-sm text-gray-600">AI-Powered Research Quality Analysis</p>
              </div>
            </div>
            {analysisResult && (
              <button
                onClick={exportResults}
                className="hidden sm:flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-md hover:shadow-lg"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>Export</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        {isLoading ? (
          /* Loading Progress Bar */
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="w-full max-w-4xl">
              <EnhancedProgressBar
                isLoading={isLoading}
                fileSize={attachedFile?.size || 0}
                processingType={processingType}
                estimatedTime={estimatedTime}
                onComplete={() => {
                  console.log('Processing completed!');
                }}
              />
            </div>
          </div>
        ) : !attachedFile || !analysisResult ? (
          /* Enhanced Upload Interface */
          <div className="flex items-center justify-center min-h-[60vh] py-8">
            <div className="w-full max-w-3xl">
              <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 sm:p-10 border border-gray-200/50">
                {/* Error Display */}
                {error && (
                  <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="text-sm text-red-700">{error}</p>
                      <button
                        onClick={() => setError(null)}
                        className="ml-auto text-red-500 hover:text-red-700"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Enhanced Search Input */}
                  <div className="relative">
                    <div className="flex items-center space-x-3">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Ask a question about your research or upload a document..."
                          className="w-full px-5 py-4 pr-12 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all text-lg bg-white shadow-sm hover:shadow-md"
                          disabled={isLoading}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              handleSubmit(e as any);
                            }
                          }}
                        />
                        <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                        </div>
                      </div>
                      
                      {/* File Upload Button */}
                      <label className="flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 rounded-2xl cursor-pointer transition-all shadow-lg hover:shadow-xl transform hover:scale-105">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf,.doc,.docx,.txt"
                          onChange={handleFileUpload}
                          className="sr-only"
                          disabled={isLoading}
                        />
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </label>
                    </div>
                  </div>

                  {/* Drag and Drop Zone */}
                  <div
                    ref={dropZoneRef}
                    onDragEnter={handleDragEnter}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
                      isDragging
                        ? 'border-blue-500 bg-blue-50 scale-[1.02]'
                        : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex flex-col items-center space-y-4">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                        isDragging ? 'bg-blue-100 scale-110' : 'bg-gray-100'
                      }`}>
                        <svg className={`w-8 h-8 ${isDragging ? 'text-blue-600' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-lg font-semibold text-gray-700">
                          {isDragging ? 'Drop your file here' : 'Drag and drop your document here'}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          or click the upload button above
                        </p>
                        <p className="text-xs text-gray-400 mt-2">
                          Supports PDF, Word documents, and text files
                        </p>
                      </div>
                    </div>
                  </div>


                  {/* Enhanced Attached File Display */}
                  {attachedFile && (
                    <div className={`flex items-center justify-between border-2 rounded-2xl p-4 transition-all ${
                      attachedFile.size > 3 * 1024 * 1024 
                        ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-300 shadow-md' 
                        : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300 shadow-md'
                    }`}>
                      <div className="flex items-center space-x-4">
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                          attachedFile.size > 3 * 1024 * 1024 ? 'bg-yellow-100' : 'bg-blue-100'
                        }`}>
                          <svg className={`w-6 h-6 ${attachedFile.size > 3 * 1024 * 1024 ? 'text-yellow-600' : 'text-blue-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900 truncate">{attachedFile.name}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <p className="text-xs text-gray-600">
                              {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                            </p>
                            {attachedFile.size > 3 * 1024 * 1024 && (
                              <span className="px-2 py-0.5 text-xs font-medium bg-yellow-200 text-yellow-800 rounded-full">
                                Large file
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={removeFile}
                        className="ml-4 p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        disabled={isLoading}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  )}

                  {/* Enhanced Submit Button */}
                  <button
                    type="submit"
                    disabled={(!query.trim() && !attachedFile) || isLoading}
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-2xl font-semibold hover:from-blue-700 hover:to-indigo-700 focus:ring-4 focus:ring-blue-300 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-3">
                        <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>
                          {processingType === 'parallel_processing' ? 'Parallel Processing...' :
                           processingType === 'detailed_analysis' ? 'Detailed Analysis...' :
                           processingType === 'upload' ? 'Uploading...' : 'Processing...'}
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center space-x-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                        </svg>
                        <span>Analyze Document</span>
                      </div>
                    )}
                  </button>
                </form>

                {/* Enhanced Help Text */}
                <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-700">Upload Documents</p>
                    <p className="text-xs text-gray-500 mt-1">PDF, Word, or Text files</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-700">AI Analysis</p>
                    <p className="text-xs text-gray-500 mt-1">Comprehensive quality assessment</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-gray-700">Get Insights</p>
                    <p className="text-xs text-gray-500 mt-1">Detailed quality metrics</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Enhanced Results Display */
          <div className="space-y-6">
            {/* Action Bar */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-4 border border-gray-200/50">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Analysis Complete</h2>
                    <p className="text-sm text-gray-600">{attachedFile?.name || 'Query Results'}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={exportResults}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="hidden sm:inline">Export</span>
                  </button>
                  <button
                    onClick={() => {
                      removeFile();
                      setQuery('');
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-lg transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="hidden sm:inline">Clear</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Paper Display - 2/3 of screen */}
              <div className="lg:col-span-2">
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden border border-gray-200/50 h-[calc(100vh-280px)]">
                  <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800">Document Viewer</h3>
                      </div>
                      {attachedFile && (
                        <span className="text-xs text-gray-500">
                          {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="h-[calc(100%-73px)]">
                    {pdfContent && (
                      <div className="w-full h-full">
                        {attachedFile && attachedFile.size > 3 * 1024 * 1024 ? (
                          <div className="flex flex-col items-center justify-center h-full bg-gradient-to-br from-gray-50 to-gray-100">
                            <div className="text-center p-8">
                              <div className="w-20 h-20 bg-yellow-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <svg className="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                              </div>
                              <h3 className="text-xl font-semibold text-gray-900 mb-2">Large PDF File</h3>
                              <p className="text-sm text-gray-600 mb-6 max-w-md mx-auto">
                                This PDF is too large to display inline. Download it to view the full document.
                              </p>
                              <a
                                href={pdfContent}
                                download={attachedFile.name}
                                className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl"
                              >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <span>Download PDF</span>
                              </a>
                            </div>
                          </div>
                        ) : (
                          <iframe
                            src={pdfContent}
                            className="w-full h-full border-0"
                            title="PDF Viewer"
                          />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Scoring and Analysis - 1/3 of screen */}
              <div className="lg:col-span-1 flex flex-col space-y-6">
                {/* Enhanced Quality Score Display */}
                <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-gray-200/50">
                  <CircularScoreDisplay data={analysisResult} />
                </div>

                {/* Scrollable Analysis Sections */}
                <div className="flex-1 bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden border border-gray-200/50">
                  <ScrollableAnalysisSections data={analysisResult} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}