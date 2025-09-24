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
  async queryAgent(request: AgentQueryRequest): Promise<AgentQueryResponse> {
    try {
      return await this.post<AgentQueryResponse>('/api/agent/query', request);
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
  async uploadFile(file: File): Promise<AgentQueryResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/api/agent/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('File upload API error:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const agentService = new AgentService();
