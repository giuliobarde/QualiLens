'use client';

import React from 'react';

interface SafeRendererProps {
  data: any;
  className?: string;
}

export default function SafeRenderer({ data, className = '' }: SafeRendererProps) {
  const renderValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    
    if (Array.isArray(value)) {
      return value.map(item => renderValue(item)).join(', ');
    }
    
    if (typeof value === 'object') {
      // Try to extract meaningful text from object
      const textFields = ['text', 'description', 'content', 'message', 'value', 'name', 'title'];
      for (const field of textFields) {
        if (value[field] && typeof value[field] === 'string') {
          return value[field];
        }
      }
      
      // If no text field found, return a simple representation
      return `[Object with ${Object.keys(value).length} properties]`;
    }
    
    return String(value);
  };

  return (
    <span className={className}>
      {renderValue(data)}
    </span>
  );
}
