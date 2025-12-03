'use client';

import React from 'react';

interface ReproducibilitySummaryData {
  has_open_data?: boolean;
  has_code_repository?: boolean;
  has_preregistration?: boolean;
  has_supplementary_materials?: boolean;
  data_repositories?: string[];
  code_repositories?: string[];
  preregistration_numbers?: string[];
  supplementary_material_links?: string[];
  confidence_score?: number;
}

interface ReproducibilitySummaryProps {
  data: ReproducibilitySummaryData;
  className?: string;
}

export default function ReproducibilitySummary({ data, className = '' }: ReproducibilitySummaryProps) {
  const formatUrl = (url: string): string => {
    // Clean up common prefixes
    let cleaned = url.trim();
    // Remove common prefixes if they're not part of the URL
    cleaned = cleaned.replace(/^(?:data\s+available\s+at|code\s+available\s+at|source\s+code\s+at)\s+/i, '');
    // Ensure it starts with http if it's a URL
    if (!cleaned.match(/^https?:\/\//i) && cleaned.match(/^[a-z0-9.-]+\.[a-z]{2,}/i)) {
      cleaned = 'https://' + cleaned;
    }
    return cleaned;
  };

  const isValidUrl = (url: string): boolean => {
    try {
      const formatted = formatUrl(url);
      new URL(formatted);
      return true;
    } catch {
      return false;
    }
  };

  const IndicatorItem = ({ 
    label, 
    present, 
    items, 
    icon 
  }: { 
    label: string; 
    present: boolean; 
    items?: string[]; 
    icon: React.ReactNode;
  }) => (
    <div className="flex items-start space-x-3 p-3 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors">
      <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
        present ? 'bg-green-100' : 'bg-gray-100'
      }`}>
        {present ? (
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-1">
          {icon}
          <span className={`font-semibold text-sm ${
            present ? 'text-gray-900' : 'text-gray-500'
          }`}>
            {label}
          </span>
        </div>
        {present && items && items.length > 0 && (
          <div className="mt-2 space-y-1">
            {items.map((item, index) => {
              const formattedUrl = formatUrl(item);
              const isValid = isValidUrl(formattedUrl);
              return (
                <div key={index} className="text-xs">
                  {isValid ? (
                    <a
                      href={formattedUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                    >
                      {item.length > 60 ? item.substring(0, 60) + '...' : item}
                      <svg className="w-3 h-3 inline-block ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ) : (
                    <span className="text-gray-700 break-all">{item}</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header with Confidence Score */}
      {data.confidence_score !== undefined && (
        <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-4 rounded-lg border border-indigo-200">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-indigo-900 mb-1">Reproducibility Confidence</h4>
              <p className="text-xs text-indigo-700">
                Based on detected indicators in the paper
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-indigo-600">
                {Math.round(data.confidence_score * 100)}%
              </div>
              <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                <div
                  className={`h-2 rounded-full ${
                    data.confidence_score >= 0.7 ? 'bg-green-500' :
                    data.confidence_score >= 0.5 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${data.confidence_score * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Indicators Grid */}
      <div className="space-y-2">
        <h4 className="font-semibold text-gray-800 mb-3 text-sm uppercase tracking-wide">
          Reproducibility Indicators
        </h4>
        
        <IndicatorItem
          label="Open Data Availability"
          present={data.has_open_data || false}
          items={data.data_repositories}
          icon={
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          }
        />

        <IndicatorItem
          label="Code Repository"
          present={data.has_code_repository || false}
          items={data.code_repositories}
          icon={
            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          }
        />

        <IndicatorItem
          label="Pre-registration"
          present={data.has_preregistration || false}
          items={data.preregistration_numbers}
          icon={
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <IndicatorItem
          label="Supplementary Materials"
          present={data.has_supplementary_materials || false}
          items={data.supplementary_material_links}
          icon={
            <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-3 pt-2">
        <div className="bg-gray-50 p-3 rounded-lg text-center border border-gray-200">
          <div className="text-2xl font-bold text-gray-800">
            {(data.has_open_data ? 1 : 0) + (data.has_code_repository ? 1 : 0) + (data.has_preregistration ? 1 : 0) + (data.has_supplementary_materials ? 1 : 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">Indicators Found</div>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg text-center border border-gray-200">
          <div className="text-2xl font-bold text-gray-800">
            {(data.data_repositories?.length || 0) + (data.code_repositories?.length || 0) + (data.preregistration_numbers?.length || 0) + (data.supplementary_material_links?.length || 0)}
          </div>
          <div className="text-xs text-gray-600 mt-1">Total Links/IDs</div>
        </div>
      </div>
    </div>
  );
}

