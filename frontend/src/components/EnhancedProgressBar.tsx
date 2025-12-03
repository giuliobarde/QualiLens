'use client';

import { useState, useEffect, useRef } from 'react';
import { agentService } from '@/utils/agent-service';

interface EnhancedProgressBarProps {
  isLoading: boolean;
  fileSize: number;
  processingType: 'upload' | 'analysis' | 'detailed_analysis' | 'parallel_processing';
  estimatedTime?: number;
  requestId?: string;
  onComplete: () => void;
}

interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  completed: boolean;
  active: boolean;
}

interface BackendProgress {
  request_id: string;
  stage: string;
  stage_name: string;
  progress: number;
  estimated_time_remaining?: number;
  estimated_total_time?: number;
  message: string;
  start_time: string;
  last_update: string;
  metadata?: Record<string, any>;
}

// Map backend stages to frontend step IDs
const STAGE_TO_STEP_ID: Record<string, string> = {
  'initializing': 'initializing',
  'classifying': 'classification',
  'agent_selection': 'agent_selection',
  'pdf_parsing': 'pdf_parsing',
  'llm_analysis': 'llm_analysis',
  'tool_execution': 'tool_execution',
  'evidence_collection': 'evidence_collection',
  'scoring': 'scoring',
  'compiling': 'compilation',
  'complete': 'complete',
  'error': 'error'
};

export default function EnhancedProgressBar({
  isLoading,
  fileSize,
  processingType,
  estimatedTime,
  requestId,
  onComplete
}: EnhancedProgressBarProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [backendProgress, setBackendProgress] = useState<BackendProgress | null>(null);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const hasCompletedRef = useRef(false);

  // Define processing steps based on backend flow
  const getProcessingSteps = (): ProcessingStep[] => {
    const baseSteps: ProcessingStep[] = [
      {
        id: 'initializing',
        name: 'Initializing',
        description: 'Preparing analysis system',
        completed: false,
        active: false
      },
      {
        id: 'classification',
        name: 'Classifying Query',
        description: 'Determining the type of analysis needed',
        completed: false,
        active: false
      },
      {
        id: 'agent_selection',
        name: 'Selecting Agent',
        description: 'Choosing the best agent for your request',
        completed: false,
        active: false
      }
    ];

    if (processingType === 'upload' || processingType === 'analysis' || processingType === 'detailed_analysis') {
      baseSteps.push(
        {
          id: 'pdf_parsing',
          name: 'Parsing PDF',
          description: 'Extracting text and metadata from document',
          completed: false,
          active: false
        },
        {
          id: 'llm_analysis',
          name: 'LLM Analysis',
          description: 'Running comprehensive analysis with multiple AI tools',
          completed: false,
          active: false
        },
        {
          id: 'evidence_collection',
          name: 'Collecting Evidence',
          description: 'Gathering evidence and calculating scores',
          completed: false,
          active: false
        },
        {
          id: 'scoring',
          name: 'Calculating Scores',
          description: 'Evaluating research quality',
          completed: false,
          active: false
        },
        {
          id: 'compilation',
          name: 'Compiling Results',
          description: 'Finalizing analysis results',
          completed: false,
          active: false
        }
      );
    } else {
      baseSteps.push(
        {
          id: 'tool_execution',
          name: 'Processing',
          description: 'Running analysis tools',
          completed: false,
          active: false
        }
      );
    }

    return baseSteps;
  };

  const [steps, setSteps] = useState<ProcessingStep[]>(getProcessingSteps());

  // Poll for progress updates
  useEffect(() => {
    if (isLoading && requestId) {
      // Start polling immediately
      const pollProgress = async () => {
        try {
          const progressData = await agentService.getProgress(requestId);
          setBackendProgress(progressData);
          
          // Update progress percentage
          if (progressData.progress !== undefined) {
            setProgress(progressData.progress);
          }
          
          // Update estimated time remaining
          if (progressData.estimated_time_remaining !== undefined && progressData.estimated_time_remaining !== null) {
            setEstimatedTimeRemaining(progressData.estimated_time_remaining);
          }
          
          // Update steps based on backend stage
          const currentStage = progressData.stage;
          const stepId = STAGE_TO_STEP_ID[currentStage] || currentStage;
          
          setSteps(prevSteps => {
            const updatedSteps = prevSteps.map((step, index) => {
              const stepIndex = prevSteps.findIndex(s => s.id === stepId);
              
              if (stepIndex === -1) {
                // Stage not in our steps, keep as is
                return step;
              }
              
              return {
                ...step,
                active: step.id === stepId && progressData.stage !== 'complete' && progressData.stage !== 'error',
                completed: index < stepIndex || (step.id === stepId && progressData.stage === 'complete')
              };
            });
            
            // Update current step based on updated steps
            const activeStepIndex = updatedSteps.findIndex(s => s.id === stepId);
            if (activeStepIndex !== -1) {
              setCurrentStep(activeStepIndex);
            }
            
            return updatedSteps;
          });
          
          // Check if complete
          if (progressData.stage === 'complete' && !hasCompletedRef.current) {
            hasCompletedRef.current = true;
            setProgress(100);
            // Stop polling
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
            // Call onComplete after a short delay
            setTimeout(() => {
              onComplete();
            }, 500);
          } else if (progressData.stage === 'error') {
            // Stop polling on error
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        } catch (error) {
          console.error('Error polling progress:', error);
          // Continue polling even on error (might be temporary)
        }
      };
      
      // Poll immediately, then every 500ms
      pollProgress();
      pollingIntervalRef.current = setInterval(pollProgress, 500);
      
      return () => {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    } else if (!isLoading) {
      // Stop polling when not loading
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }
  }, [isLoading, requestId, onComplete]);

  // Reset when loading starts
  useEffect(() => {
    if (isLoading) {
      hasCompletedRef.current = false;
      setProgress(0);
      setCurrentStep(0);
      setBackendProgress(null);
      setEstimatedTimeRemaining(null);
      setSteps(getProcessingSteps());
    }
  }, [isLoading, processingType, fileSize]);

  const getProgressMessage = () => {
    if (backendProgress?.stage_name) {
      return backendProgress.stage_name;
    }
    if (steps.length === 0) return 'Initializing...';
    const currentStepData = steps[currentStep];
    return currentStepData ? currentStepData.name : 'Processing...';
  };

  const getProgressDescription = () => {
    if (backendProgress?.message) {
      return backendProgress.message;
    }
    if (steps.length === 0) return 'Preparing analysis...';
    const currentStepData = steps[currentStep];
    return currentStepData ? currentStepData.description : 'Processing your request...';
  };

  const getEstimatedTime = () => {
    // Use backend estimate if available
    if (estimatedTimeRemaining !== null && estimatedTimeRemaining !== undefined) {
      const minutes = Math.floor(estimatedTimeRemaining / 60);
      const seconds = Math.floor(estimatedTimeRemaining % 60);
      if (minutes > 0) {
        return `Estimated time remaining: ${minutes}m ${seconds}s`;
      }
      return `Estimated time remaining: ${seconds}s`;
    }
    
    // Fallback to prop estimate
    if (estimatedTime) {
      return `Estimated time: ${estimatedTime}s`;
    }
    
    // Fallback to calculated estimate
    return 'Calculating estimated time...';
  };

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <div className="text-center">
        <div className="mb-6">
          <div className="w-16 h-16 mx-auto mb-4">
            <svg className="animate-spin w-16 h-16 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">
            {getProgressMessage()}
          </h3>
          <p className="text-gray-600 mb-4">
            {getProgressDescription()}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            {getEstimatedTime()}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        {/* Processing Steps */}
        <div className="space-y-3">
          {steps.map((step, index) => (
            <div 
              key={step.id}
              className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-300 ${
                step.active 
                  ? 'bg-blue-50 border border-blue-200' 
                  : step.completed 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                step.completed 
                  ? 'bg-green-500 text-white' 
                  : step.active 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-300 text-gray-600'
              }`}>
                {step.completed ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : step.active ? (
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <span className="text-xs font-medium">{index + 1}</span>
                )}
              </div>
              <div className="flex-1 text-left">
                <p className={`text-sm font-medium ${
                  step.active ? 'text-blue-800' : step.completed ? 'text-green-800' : 'text-gray-600'
                }`}>
                  {step.name}
                </p>
                <p className={`text-xs ${
                  step.active ? 'text-blue-600' : step.completed ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* File Info */}
        {fileSize > 0 && (
          <div className="mt-6 text-sm text-gray-500">
            File size: {(fileSize / 1024 / 1024).toFixed(2)} MB
          </div>
        )}
      </div>
    </div>
  );
}
