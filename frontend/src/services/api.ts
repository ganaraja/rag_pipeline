import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  CreateCollectionRequest,
  CreateCollectionResponse,
  DeleteCollectionResponse,
  UploadResponse,
  QueryRequest,
  QueryResponse,
} from '../types';
import { API_CONFIG } from '../config/api.config';

/**
 * API Error class for handling backend errors
 */
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Axios client instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Error handler for API requests
 */
const handleAPIError = (error: unknown): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    
    if (axiosError.response) {
      // Server responded with error status
      const message = 
        axiosError.response.data?.detail || 
        axiosError.response.data?.message || 
        `Request failed with status ${axiosError.response.status}`;
      
      throw new APIError(
        message,
        axiosError.response.status,
        axiosError.response.data
      );
    } else if (axiosError.request) {
      // Request made but no response received
      throw new APIError(
        'No response from server. Please check your connection.',
        undefined,
        { originalError: axiosError.message }
      );
    } else {
      // Error setting up request
      throw new APIError(
        `Request setup failed: ${axiosError.message}`,
        undefined,
        { originalError: axiosError.message }
      );
    }
  }
  
  // Unknown error type
  throw new APIError(
    'An unexpected error occurred',
    undefined,
    { originalError: error }
  );
};

/**
 * List all collections from the backend
 * 
 * @returns Promise<string[]> - Array of collection names
 * @throws APIError - If the request fails
 */
export const listCollections = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get<string[]>('/api/collections');
    return response.data;
  } catch (error) {
    return handleAPIError(error);
  }
};

/**
 * Create a new collection
 * 
 * @param collectionName - Name of the collection to create
 * @returns Promise<CreateCollectionResponse> - Response with success status
 * @throws APIError - If the request fails
 */
export const createCollection = async (
  collectionName: string
): Promise<CreateCollectionResponse> => {
  try {
    const request: CreateCollectionRequest = {
      collection_name: collectionName,
    };
    
    const response = await apiClient.post<CreateCollectionResponse>(
      '/api/collections',
      request
    );
    
    return response.data;
  } catch (error) {
    return handleAPIError(error);
  }
};

/**
 * Delete a collection
 * 
 * @param collectionName - Name of the collection to delete
 * @returns Promise<DeleteCollectionResponse> - Response with success status
 * @throws APIError - If the request fails
 */
export const deleteCollection = async (
  collectionName: string
): Promise<DeleteCollectionResponse> => {
  try {
    const response = await apiClient.delete<DeleteCollectionResponse>(
      `/api/collections/${encodeURIComponent(collectionName)}`
    );
    
    return response.data;
  } catch (error) {
    return handleAPIError(error);
  }
};

/**
 * Upload a document to a collection
 * 
 * @param file - File to upload
 * @param collectionName - Target collection name
 * @returns Promise<UploadResponse> - Response with processing statistics
 * @throws APIError - If the request fails
 */
export const uploadDocument = async (
  file: File,
  collectionName: string
): Promise<UploadResponse> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('collection_name', collectionName);
    
    const response = await apiClient.post<UploadResponse>(
      '/api/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: API_CONFIG.uploadTimeout,
      }
    );
    
    return response.data;
  } catch (error) {
    return handleAPIError(error);
  }
};

/**
 * Query documents in a collection
 * 
 * @param query - Query text
 * @param collectionName - Collection to query
 * @returns Promise<QueryResponse> - Response with answer and sources
 * @throws APIError - If the request fails
 */
export const queryDocuments = async (
  query: string,
  collectionName: string
): Promise<QueryResponse> => {
  try {
    const request: QueryRequest = {
      query,
      collection_name: collectionName,
    };
    
    const response = await apiClient.post<QueryResponse>(
      '/api/query',
      request,
      {
        timeout: API_CONFIG.queryTimeout,
      }
    );
    
    return response.data;
  } catch (error) {
    return handleAPIError(error);
  }
};

/**
 * Export the axios client for advanced usage
 */
export { apiClient };
