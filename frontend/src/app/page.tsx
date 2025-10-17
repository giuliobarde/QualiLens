'use client';

import { useState, useRef, useEffect } from 'react';
import { agentService } from '@/utils/agent-service';
import QualityScoreDisplay from '@/components/QualityScoreDisplay';
import ScrollableAnalysisSections from '@/components/ScrollableAnalysisSections';
import EnhancedProgressBar from '@/components/EnhancedProgressBar';

export default function Home() {
  const [query, setQuery] = useState('');
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [pdfContent, setPdfContent] = useState<string | null>(null);
  const [processingType, setProcessingType] = useState<'upload' | 'analysis' | 'detailed_analysis' | 'parallel_processing'>('analysis');
  const [analysisLevel] = useState<'comprehensive'>('comprehensive');
  const [estimatedTime, setEstimatedTime] = useState<number | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cleanup object URLs on component unmount
  useEffect(() => {
    return () => {
      if (pdfContent && pdfContent.startsWith('blob:')) {
        URL.revokeObjectURL(pdfContent);
      }
    };
  }, [pdfContent]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
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
        // Use object URL for large files to avoid memory issues with base64
        const objectUrl = URL.createObjectURL(file);
        setPdfContent(objectUrl);
      } else {
        // Use base64 for smaller files
        const reader = new FileReader();
        reader.onload = (e) => {
          const result = e.target?.result as string;
          setPdfContent(result);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  const removeFile = () => {
    // Clean up object URL if it exists
    if (pdfContent && pdfContent.startsWith('blob:')) {
      URL.revokeObjectURL(pdfContent);
    }
    setAttachedFile(null);
    setPdfContent(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
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
        console.error('❌ Analysis failed:', response.error_message || 'Unknown error');
        alert(`Analysis failed: ${response.error_message || 'Unknown error'}`);
      }
      
    } catch (error) {
      console.error('Error processing request:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">QualiLens</h1>
              <p className="text-sm text-gray-600">Research document analysis and insights</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
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
          /* Upload Interface */
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="w-full max-w-2xl">
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Search Input */}
                  <div className="relative">
                    <div className="flex items-center space-x-3">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                          placeholder="Ask a question about your research..."
                          className="w-full px-4 py-4 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors text-lg"
                          disabled={isLoading}
                        />
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                          </svg>
                        </div>
                      </div>
                      
                      {/* File Upload Button */}
                      <label className="flex items-center justify-center w-12 h-12 bg-gray-100 hover:bg-gray-200 rounded-xl cursor-pointer transition-colors">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf,.doc,.docx,.txt"
                          onChange={handleFileUpload}
                          className="sr-only"
                          disabled={isLoading}
                        />
                        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                        </svg>
                      </label>
                    </div>
                  </div>


                  {/* Attached File Display */}
                  {attachedFile && (
                    <div className={`flex items-center justify-between border rounded-xl p-4 ${
                      attachedFile.size > 3 * 1024 * 1024 
                        ? 'bg-yellow-50 border-yellow-200' 
                        : 'bg-blue-50 border-blue-200'
                    }`}>
                      <div className="flex items-center space-x-3">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <div>
                          <p className="text-sm font-medium text-blue-900">{attachedFile.name}</p>
                          <p className="text-xs text-blue-600">
                            {(attachedFile.size / 1024 / 1024).toFixed(2)} MB
                            {attachedFile.size > 3 * 1024 * 1024 && (
                              <span className="ml-2 text-yellow-600 font-medium">
                                (Large file - optimized display)
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={removeFile}
                        className="text-blue-600 hover:text-blue-800 transition-colors"
                        disabled={isLoading}
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  )}

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={(!query.trim() && !attachedFile) || isLoading}
                    className="w-full bg-blue-600 text-white py-4 px-6 rounded-xl font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center space-x-2">
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
                      'Analyze'
                    )}
                  </button>
                </form>

                {/* Help Text */}
                <div className="mt-6 text-center">
                  <p className="text-sm text-gray-500">
                    Upload PDFs, Word documents, or text files to analyze their content
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Results Display - New Layout */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-200px)]">
            {/* Paper Display - 2/3 of screen */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-lg overflow-hidden h-full">
                <div className="bg-gray-50 px-4 py-3 border-b">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-800">Document</h3>
                    <button
                      onClick={removeFile}
                      className="text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
                <div className="h-[calc(100%-60px)]">
                  {pdfContent && (
                    <div className="w-full h-full">
                      {attachedFile && attachedFile.size > 3 * 1024 * 1024 ? (
                        // For large files, show a message with download option
                        <div className="flex flex-col items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                          <svg className="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <h3 className="text-lg font-medium text-gray-900 mb-2">Large PDF File</h3>
                          <p className="text-sm text-gray-600 mb-4 text-center max-w-md">
                            This PDF is too large to display inline. Download it to view the full document.
                          </p>
                          <a
                            href={pdfContent}
                            download={attachedFile.name}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                          >
                            Download PDF
                          </a>
                        </div>
                      ) : (
                        // For smaller files, use iframe
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
              {/* Quality Score Display */}
              <div className="bg-white rounded-lg shadow-lg p-6">
                <QualityScoreDisplay data={analysisResult} />
              </div>

              {/* Scrollable Analysis Sections */}
              <div className="flex-1 bg-white rounded-lg shadow-lg overflow-hidden">
                <ScrollableAnalysisSections data={analysisResult} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}