'use client';

import React from 'react';

interface SafeRendererProps {
  data: any;
  className?: string;
}

export default function SafeRenderer({ data, className = '' }: SafeRendererProps) {
  const parseJSONString = (str: string): any => {
    // Check if string looks like JSON
    const trimmed = str.trim();
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || 
        (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try {
        return JSON.parse(str);
      } catch (e) {
        // If parsing fails, return original string
        return str;
      }
    }
    return str;
  };

  const extractTextFromObject = (obj: any): string => {
    // Priority order for extracting text from objects
    const textFields = ['summary', 'text', 'description', 'content', 'message', 'value', 'name', 'title', 'rationale'];
    
    for (const field of textFields) {
      if (obj[field]) {
        if (typeof obj[field] === 'string') {
          return obj[field];
        } else if (typeof obj[field] === 'object') {
          const nested = extractTextFromObject(obj[field]);
          if (nested && nested !== 'N/A') return nested;
        }
      }
    }
    
    // If object has a single string property, use it
    const keys = Object.keys(obj);
    if (keys.length === 1 && typeof obj[keys[0]] === 'string') {
      return obj[keys[0]];
    }
    
    return null;
  };

  const renderValue = (value: any): string => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    if (typeof value === 'string') {
      // Try to parse as JSON first
      const parsed = parseJSONString(value);
      if (parsed !== value && typeof parsed === 'object') {
        // It was JSON, extract text from it
        const extracted = extractTextFromObject(parsed);
        if (extracted) return extracted;
        // If extraction failed, try to stringify nicely
        return JSON.stringify(parsed, null, 2);
      }
      return value;
    }
    
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    
    if (Array.isArray(value)) {
      return value.map(item => renderValue(item)).join(', ');
    }
    
    if (typeof value === 'object') {
      // Try to extract meaningful text from object
      const extracted = extractTextFromObject(value);
      if (extracted) return extracted;
      
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
