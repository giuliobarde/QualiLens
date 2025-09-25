'use client';

import { useState, useEffect } from 'react';

interface EnhancedProgressBarProps {
  isLoading: boolean;
  fileSize: number;
  processingType: 'upload' | 'analysis' | 'detailed_analysis' | 'parallel_processing';
  estimatedTime?: number;
  onComplete: () => void;
}

interface ProcessingStep {
  id: string;
  name: string;
  description: string;
  duration: number; // in milliseconds
  completed: boolean;
  active: boolean;
}

export default function EnhancedProgressBar({
  isLoading,
  fileSize,
  processingType,
  estimatedTime,
  onComplete
}: EnhancedProgressBarProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  // Define processing steps based on backend flow
  const getProcessingSteps = (): ProcessingStep[] => {
    const baseSteps: ProcessingStep[] = [
      {
        id: 'classification',
        name: 'Classifying Query',
        description: 'Determining the type of analysis needed',
        duration: 1000,
        completed: false,
        active: false
      },
      {
        id: 'agent_selection',
        name: 'Selecting Agent',
        description: 'Choosing the best agent for your request',
        duration: 500,
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
          duration: Math.max(2000, fileSize / (1024 * 1024) * 1000), // Scale with file size
          completed: false,
          active: false
        },
        {
          id: 'paper_analysis',
          name: 'Analyzing Content',
          description: 'Using AI to extract research insights',
          duration: processingType === 'detailed_analysis' ? 8000 : 4000,
          completed: false,
          active: false
        }
      );

      if (processingType === 'detailed_analysis') {
        baseSteps.push(
          {
            id: 'section_analysis',
            name: 'Section Analysis',
            description: 'Analyzing methodology, results, and conclusions',
            duration: 3000,
            completed: false,
            active: false
          },
          {
            id: 'quality_assessment',
            name: 'Quality Assessment',
            description: 'Evaluating research quality and methodology',
            duration: 2000,
            completed: false,
            active: false
          }
        );
      }

      baseSteps.push({
        id: 'compilation',
        name: 'Compiling Results',
        description: 'Combining all analysis results',
        duration: 1000,
        completed: false,
        active: false
      });
    } else {
      // For parallel processing or other types
      baseSteps.push(
        {
          id: 'parallel_processing',
          name: 'Parallel Processing',
          description: 'Processing multiple components simultaneously',
          duration: Math.max(3000, fileSize / (1024 * 1024) * 500),
          completed: false,
          active: false
        }
      );
    }

    return baseSteps;
  };

  const [steps, setSteps] = useState<ProcessingStep[]>([]);

  useEffect(() => {
    if (isLoading) {
      const newSteps = getProcessingSteps();
      setSteps(newSteps);
      setCurrentStep(0);
      setProgress(0);
      startProcessing(newSteps);
    }
  }, [isLoading, processingType, fileSize]);

  const startProcessing = async (processingSteps: ProcessingStep[]) => {
    for (let i = 0; i < processingSteps.length; i++) {
      // Update current step
      setCurrentStep(i);
      setSteps(prev => prev.map((step, index) => ({
        ...step,
        active: index === i,
        completed: index < i
      })));

      // Simulate step duration
      const stepDuration = processingSteps[i].duration;
      const stepProgress = 100 / processingSteps.length;
      
      // Animate progress for this step
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + (stepProgress / (stepDuration / 100));
          return Math.min(newProgress, ((i + 1) / processingSteps.length) * 100);
        });
      }, 100);

      await new Promise(resolve => setTimeout(resolve, stepDuration));
      clearInterval(progressInterval);

      // Mark step as completed
      setSteps(prev => prev.map((step, index) => ({
        ...step,
        completed: index <= i,
        active: false
      })));
    }

    // Processing complete
    setProgress(100);
    setTimeout(() => {
      onComplete();
    }, 500);
  };

  const getProgressMessage = () => {
    if (steps.length === 0) return 'Initializing...';
    
    const currentStepData = steps[currentStep];
    return currentStepData ? currentStepData.name : 'Processing...';
  };

  const getProgressDescription = () => {
    if (steps.length === 0) return 'Preparing analysis...';
    
    const currentStepData = steps[currentStep];
    return currentStepData ? currentStepData.description : 'Processing your request...';
  };

  const getEstimatedTime = () => {
    if (estimatedTime) {
      return `Estimated time: ${estimatedTime}s`;
    }
    
    const totalDuration = steps.reduce((sum, step) => sum + step.duration, 0);
    return `Estimated time: ${Math.ceil(totalDuration / 1000)}s`;
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
