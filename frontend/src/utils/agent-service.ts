import { BaseHttpClient } from '@/utils/http-client';

const API_BASE_URL = 'http://localhost:5002';

export interface AgentQueryRequest {
  query: string;
  user_context?: {
    filters?: Record<string, any>;
    preferences?: Record<string, any>;
  };
}

export interface AgentClassification {
  query_type?: string;
  confidence?: number;
  suggested_tool?: string;
  extracted_parameters?: {
    query?: string;
    filters?: {
      statuses?: string[];
      phases?: string[];
      studyTypes?: string[];
      providers?: string[];
    };
    other_params?: Record<string, any>;
  };
  reasoning?: string;
}

export interface AgentQueryResponse {
  success: boolean;
  result?: any;
  tool_used?: string;
  classification?: AgentClassification;
  error_message?: string;
  execution_time_ms: number;
  timestamp: string;
}

export interface AgentStatus {
  agent_initialized: boolean;
  available_tools: string[];
  execution_stats: {
    total_queries: number;
    successful_queries: number;
    failed_queries: number;
    average_execution_time: number;
  };
  search_tool_status?: {
    trial_engine: string;
    paper_engine: string;
    config: {
      default_semantic_weight: number;
      max_top_k: number;
      enable_caching: boolean;
    };
  };
  timestamp: string;
}

export interface AgentTool {
  name: string;
  description: string;
  category: string;
  examples: string[];
  parameters: {
    required: string[];
    optional: string[];
    search_type_options?: string[];
    search_type_default?: string;
  };
}

export interface AgentToolsResponse {
  tools: AgentTool[];
  total_tools: number;
  timestamp: string;
}

export class AgentService extends BaseHttpClient {
  constructor() {
    super(API_BASE_URL);
  }


  /**
   * Send a query to the agent system
   */
  async queryAgent(request: AgentQueryRequest, requestId?: string): Promise<AgentQueryResponse> {
    try {
      const requestWithId = { ...request, request_id: requestId };
      return await this.post<AgentQueryResponse>('/api/agent/query', requestWithId);
    } catch (error) {
      console.error('Agent query API error:', error);
      throw error;
    }
  }

  /**
   * Get the status of the agent system
   */
  async getAgentStatus(): Promise<AgentStatus> {
    try {
      return await this.get<AgentStatus>('/api/agent/status');
    } catch (error) {
      console.error('Agent status API error:', error);
      throw error;
    }
  }

  /**
   * Get information about available agent tools
   */
  async getAgentTools(): Promise<AgentToolsResponse> {
    try {
      return await this.get<AgentToolsResponse>('/api/agent/tools');
    } catch (error) {
      console.error('Agent tools API error:', error);
      throw error;
    }
  }

  /**
   * Clear agent system caches
   */
  async clearAgentCache(): Promise<{ success: boolean; message: string; timestamp: string }> {
    try {
      return await this.post<{ success: boolean; message: string; timestamp: string }>('/api/agent/clear-cache', {});
    } catch (error) {
      console.error('Clear agent cache API error:', error);
      throw error;
    }
  }

  /**
   * Process a natural language query and get paper analysis results
   */
  async processPaperAnalysisQuery(
    query: string, 
  ): Promise<AgentQueryResponse> {
    return this.queryAgent({
      query
    });
  }

  /**
   * Upload a file for analysis
   */
  async uploadFile(file: File, requestId?: string): Promise<AgentQueryResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (requestId) {
        formData.append('request_id', requestId);
      }
      
      console.log(`Uploading file to ${API_BASE_URL}/api/agent/upload`);
      console.log(`File name: ${file.name}, size: ${file.size} bytes, requestId: ${requestId}`);
      
      const response = await fetch(`${API_BASE_URL}/api/agent/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
      });

      console.log(`Upload response status: ${response.status}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Upload failed with status ${response.status}:`, errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      return result;
    } catch (error) {
      console.error('File upload API error:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the backend is running on port 5002.`);
      }
      throw error;
    }
  }

  /**
   * Upload a file for analysis with custom rubric weights
   */
  async uploadFileWithWeights(formData: FormData, requestId?: string): Promise<AgentQueryResponse> {
    try {
      if (requestId) {
        formData.append('request_id', requestId);
      }
      
      console.log(`Uploading file to ${API_BASE_URL}/api/agent/upload`);
      console.log(`RequestId: ${requestId}`);
      
      const response = await fetch(`${API_BASE_URL}/api/agent/upload`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
      });

      console.log(`Upload response status: ${response.status}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Upload failed with status ${response.status}:`, errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      return result;
    } catch (error) {
      console.error('File upload API error:', error);
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        throw new Error(`Cannot connect to backend server at ${API_BASE_URL}. Please ensure the backend is running on port 5002.`);
      }
      throw error;
    }
  }

  /**
   * Get progress for a request
   */
  async getProgress(requestId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/progress?request_id=${requestId}`);
      if (!response.ok) {
        // 404 means progress not found yet (request might not have started)
        // Return null instead of throwing to allow polling to continue
        if (response.status === 404) {
          console.log(`Progress not found for request_id: ${requestId} (request may not have started yet)`);
          return null;
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      // Only log non-404 errors
      if (error instanceof Error && !error.message.includes('404')) {
        console.error('Get progress API error:', error);
      }
      // Return null for any error to allow polling to continue
      return null;
    }
  }
}

// Export singleton instance
export const agentService = new AgentService();
