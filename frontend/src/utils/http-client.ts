export interface ApiError {
    error: string;
    message?: string;
    field?: string;
  }
  
  export interface ApiResponse<T = any> {
    data: T;
    message?: string;
  }
  
  export class HttpError extends Error {
    constructor(
      public status: number,
      public message: string,
      public originalError?: any
    ) {
      super(message);
      this.name = 'HttpError';
    }
  }
  
  export class BaseHttpClient {
    private baseUrl: string;
    private defaultHeaders: Record<string, string>;
  
    constructor(baseUrl: string) {
      this.baseUrl = baseUrl;
      this.defaultHeaders = {
        'Content-Type': 'application/json',
      };
    }
  
    private async request<T>(
      endpoint: string,
      options: RequestInit = {}
    ): Promise<T> {
      const url = `${this.baseUrl}${endpoint}`;
      const headers = { ...this.defaultHeaders, ...options.headers };
  
      try {
        const response = await fetch(url, {
          ...options,
          headers,
        });
  
        if (!response.ok) {
          let errorData: ApiError;
          try {
            errorData = await response.json();
          } catch {
            errorData = {
              error: 'Request failed',
              message: `HTTP ${response.status}: ${response.statusText}`,
            };
          }
  
          throw new HttpError(
            response.status,
            errorData.message || errorData.error || `HTTP ${response.status}`,
            errorData
          );
        }
  
        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return await response.json();
        }
  
        return {} as T;
      } catch (error) {
        if (error instanceof HttpError) {
          throw error;
        }
  
        // Network or other errors
        throw new HttpError(
          0,
          error instanceof Error ? error.message : 'Network error occurred',
          error
        );
      }
    }
  
    protected async get<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
      return this.request<T>(endpoint, {
        method: 'GET',
        headers,
      });
    }
  
    protected async post<T>(
      endpoint: string, 
      data?: any, 
      headers?: Record<string, string>
    ): Promise<T> {
      return this.request<T>(endpoint, {
        method: 'POST',
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });
    }
  
    protected async put<T>(
      endpoint: string, 
      data?: any, 
      headers?: Record<string, string>
    ): Promise<T> {
      return this.request<T>(endpoint, {
        method: 'PUT',
        headers,
        body: data ? JSON.stringify(data) : undefined,
      });
    }
  
    protected async delete<T>(endpoint: string, headers?: Record<string, string>): Promise<T> {
      return this.request<T>(endpoint, {
        method: 'DELETE',
        headers,
      });
    }
  
    protected setAuthHeader(token: string): void {
      this.defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
  
    protected removeAuthHeader(): void {
      delete this.defaultHeaders['Authorization'];
    }
  
    protected getBaseUrl(): string {
      return this.baseUrl;
    }
  }
  