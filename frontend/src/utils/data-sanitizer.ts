/**
 * Data sanitization utilities to prevent React rendering errors
 * by converting objects to safe string representations
 */

export function sanitizeData(data: any): any {
  if (data === null || data === undefined) {
    return data;
  }

  if (typeof data === 'string' || typeof data === 'number' || typeof data === 'boolean') {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map(item => sanitizeData(item));
  }

  if (typeof data === 'object') {
    const sanitized: any = {};
    
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'object' && value !== null) {
        // For complex objects, create a readable string representation
        if (Array.isArray(value)) {
          sanitized[key] = value.map(item => 
            typeof item === 'object' && item !== null 
              ? JSON.stringify(item) 
              : item
          );
        } else {
          // For nested objects, try to extract meaningful text or stringify
          const textValue = extractTextFromObject(value);
          sanitized[key] = textValue || JSON.stringify(value);
        }
      } else {
        sanitized[key] = value;
      }
    }
    
    return sanitized;
  }

  return String(data);
}

/**
 * Extract meaningful text from complex objects
 */
function extractTextFromObject(obj: any): string | null {
  if (typeof obj !== 'object' || obj === null) {
    return null;
  }

  // Try common text properties first
  const textProperties = [
    'text', 'description', 'content', 'message', 'summary', 
    'rationale', 'explanation', 'details', 'note', 'comment',
    'value', 'name', 'title', 'label'
  ];

  for (const prop of textProperties) {
    if (obj[prop] && typeof obj[prop] === 'string') {
      return obj[prop];
    }
  }

  // If no text property found, try to get the first string value
  for (const value of Object.values(obj)) {
    if (typeof value === 'string' && value.trim().length > 0) {
      return value;
    }
  }

  // If still no text found, return null to fall back to JSON.stringify
  return null;
}

/**
 * Sanitize analysis result data specifically for React rendering
 */
export function sanitizeAnalysisResult(data: any): any {
  if (!data || typeof data !== 'object') {
    return data;
  }

  const sanitized = { ...data };

  // Sanitize arrays that might contain objects
  const arrayFields = [
    'tools_used', 'key_points', 'detected_biases', 'limitations', 
    'confounding_factors', 'methodological_strengths', 'methodological_weaknesses',
    'statistical_tests_used', 'statistical_concerns', 'statistical_recommendations',
    'reproducibility_barriers', 'research_gaps', 'future_directions',
    'unaddressed_questions', 'methodological_gaps', 'theoretical_gaps',
    'citation_gaps', 'quality_strengths', 'quality_weaknesses', 'quality_recommendations'
  ];

  for (const field of arrayFields) {
    if (sanitized[field] && Array.isArray(sanitized[field])) {
      sanitized[field] = sanitized[field].map((item: any) => {
        if (typeof item === 'object' && item !== null) {
          // Try to extract meaningful text first
          const text = extractTextFromObject(item);
          if (text) {
            return text;
          }
          // Fall back to JSON string if no text found
          return JSON.stringify(item);
        }
        return item;
      });
    }
  }

  // Sanitize object fields that might contain complex nested objects
  const objectFields = [
    'sample_characteristics', 'test_appropriateness', 'data_availability', 
    'code_availability', 'citation_quality', 'reference_analysis', 
    'bibliometric_indicators', 'quality_breakdown'
  ];

  for (const field of objectFields) {
    if (sanitized[field] && typeof sanitized[field] === 'object') {
      sanitized[field] = sanitizeData(sanitized[field]);
    }
  }

  return sanitized;
}
