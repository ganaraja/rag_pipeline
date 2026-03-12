// Mock axios before importing the service
const mockAxiosInstance = {
  get: jest.fn(),
  post: jest.fn(),
  delete: jest.fn(),
};

jest.mock('axios', () => ({
  __esModule: true,
  default: {
    create: jest.fn(() => mockAxiosInstance),
    isAxiosError: jest.fn(),
  },
}));

import axios from 'axios';
import {
  listCollections,
  createCollection,
  deleteCollection,
  uploadDocument,
  queryDocuments,
  APIError,
} from '../../src/services/api';

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Service', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  describe('listCollections', () => {
    it('should fetch and return list of collections', async () => {
      const mockCollections = ['collection1', 'collection2', 'collection3'];
      mockAxiosInstance.get.mockResolvedValue({ data: mockCollections });

      const result = await listCollections();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/collections');
      expect(result).toEqual(mockCollections);
    });

    it('should return empty array when no collections exist', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: [] });

      const result = await listCollections();

      expect(result).toEqual([]);
    });

    it('should throw APIError when request fails', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(listCollections()).rejects.toThrow(APIError);
    });

    it('should throw APIError with network error message', async () => {
      const networkError = {
        request: {},
        message: 'Network Error',
      };
      mockAxiosInstance.get.mockRejectedValue(networkError);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(listCollections()).rejects.toThrow(
        'No response from server. Please check your connection.'
      );
    });
  });

  describe('createCollection', () => {
    it('should create a collection successfully', async () => {
      const collectionName = 'test-collection';
      const mockResponse = {
        success: true,
        collection_name: collectionName,
        message: 'Collection created successfully',
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await createCollection(collectionName);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/collections',
        { collection_name: collectionName }
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw APIError when collection name is invalid', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Invalid collection name' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(createCollection('invalid name!')).rejects.toThrow(APIError);
    });

    it('should throw APIError when collection already exists', async () => {
      const errorResponse = {
        response: {
          status: 409,
          data: { detail: 'Collection already exists' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(createCollection('existing-collection')).rejects.toThrow(
        APIError
      );
    });
  });

  describe('deleteCollection', () => {
    it('should delete a collection successfully', async () => {
      const collectionName = 'test-collection';
      const mockResponse = {
        success: true,
        message: 'Collection deleted successfully',
      };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      const result = await deleteCollection(collectionName);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        `/api/collections/${collectionName}`
      );
      expect(result).toEqual(mockResponse);
    });

    it('should encode collection name in URL', async () => {
      const collectionName = 'test collection with spaces';
      const mockResponse = { success: true };
      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      await deleteCollection(collectionName);

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        `/api/collections/${encodeURIComponent(collectionName)}`
      );
    });

    it('should throw APIError when collection does not exist', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: { detail: 'Collection not found' },
        },
      };
      mockAxiosInstance.delete.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(deleteCollection('nonexistent')).rejects.toThrow(APIError);
    });
  });

  describe('uploadDocument', () => {
    it('should upload a document successfully', async () => {
      const file = new File(['test content'], 'test.pdf', {
        type: 'application/pdf',
      });
      const collectionName = 'test-collection';
      const mockResponse = {
        success: true,
        chunks_created: 10,
        processing_time: 2.5,
        message: 'Document uploaded successfully',
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await uploadDocument(file, collectionName);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 120000,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should include file and collection_name in FormData', async () => {
      const file = new File(['test content'], 'test.pdf');
      const collectionName = 'test-collection';
      mockAxiosInstance.post.mockResolvedValue({
        data: { success: true, chunks_created: 5, processing_time: 1.0 },
      });

      await uploadDocument(file, collectionName);

      const formDataCall = mockAxiosInstance.post.mock.calls[0][1];
      expect(formDataCall).toBeInstanceOf(FormData);
    });

    it('should throw APIError when file format is invalid', async () => {
      const file = new File(['test'], 'test.invalid');
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Invalid file format' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(uploadDocument(file, 'collection')).rejects.toThrow(
        APIError
      );
    });

    it('should throw APIError when collection does not exist', async () => {
      const file = new File(['test'], 'test.pdf');
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Collection does not exist' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(uploadDocument(file, 'nonexistent')).rejects.toThrow(
        APIError
      );
    });
  });

  describe('queryDocuments', () => {
    it('should query documents successfully', async () => {
      const query = 'What is RAG?';
      const collectionName = 'test-collection';
      const mockResponse = {
        answer: 'RAG stands for Retrieval-Augmented Generation...',
        sources: [
          {
            id: 1,
            text: 'RAG is a technique...',
            score: 0.95,
            metadata: {},
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.2,
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await queryDocuments(query, collectionName);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/query',
        {
          query,
          collection_name: collectionName,
        },
        expect.objectContaining({
          timeout: 60000,
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle empty query results', async () => {
      const mockResponse = {
        answer: 'No relevant documents found.',
        sources: [],
        retrieval_time: 0.3,
        generation_time: 0.5,
      };
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await queryDocuments('obscure query', 'collection');

      expect(result.sources).toEqual([]);
    });

    it('should throw APIError when query is invalid', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Query cannot be empty' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(queryDocuments('', 'collection')).rejects.toThrow(APIError);
    });

    it('should throw APIError when collection does not exist', async () => {
      const errorResponse = {
        response: {
          status: 404,
          data: { detail: 'Collection not found' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(
        queryDocuments('test query', 'nonexistent')
      ).rejects.toThrow(APIError);
    });

    it('should throw APIError when LLM server is unavailable', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { detail: 'LLM server connection failed' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      await expect(queryDocuments('test', 'collection')).rejects.toThrow(
        APIError
      );
    });
  });

  describe('APIError', () => {
    it('should create APIError with message only', () => {
      const error = new APIError('Test error');

      expect(error.message).toBe('Test error');
      expect(error.name).toBe('APIError');
      expect(error.statusCode).toBeUndefined();
      expect(error.details).toBeUndefined();
    });

    it('should create APIError with status code and details', () => {
      const details = { field: 'value' };
      const error = new APIError('Test error', 400, details);

      expect(error.message).toBe('Test error');
      expect(error.statusCode).toBe(400);
      expect(error.details).toEqual(details);
    });
  });

  describe('Error handling', () => {
    it('should handle errors with detail field', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: { detail: 'Detailed error message' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      try {
        await listCollections();
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Detailed error message');
        expect((error as APIError).statusCode).toBe(400);
      }
    });

    it('should handle errors with message field', async () => {
      const errorResponse = {
        response: {
          status: 500,
          data: { message: 'Server error message' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      try {
        await listCollections();
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe('Server error message');
      }
    });

    it('should handle errors without detail or message', async () => {
      const errorResponse = {
        response: {
          status: 503,
          data: {},
        },
      };
      mockAxiosInstance.get.mockRejectedValue(errorResponse);
      mockedAxios.isAxiosError = jest.fn(() => true);

      try {
        await listCollections();
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe(
          'Request failed with status 503'
        );
      }
    });

    it('should handle request setup errors', async () => {
      const setupError = {
        message: 'Invalid URL',
      };
      mockAxiosInstance.get.mockRejectedValue(setupError);
      mockedAxios.isAxiosError = jest.fn(() => true);

      try {
        await listCollections();
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toContain('Request setup failed');
      }
    });

    it('should handle unknown error types', async () => {
      const unknownError = new Error('Unknown error');
      mockAxiosInstance.get.mockRejectedValue(unknownError);
      mockedAxios.isAxiosError = jest.fn(() => false);

      try {
        await listCollections();
        fail('Should have thrown an error');
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect((error as APIError).message).toBe(
          'An unexpected error occurred'
        );
      }
    });
  });
});
