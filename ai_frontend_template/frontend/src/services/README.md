# API Service Layer

This directory contains the API service layer for communicating with the backend.

## Files

- `api.ts` - Main API service with axios client and all API functions
- `../config/api.config.ts` - API configuration (base URL, timeouts)

## Usage

```typescript
import {
  listCollections,
  createCollection,
  deleteCollection,
  uploadDocument,
  queryDocuments,
  APIError,
} from "./services/api";

// List all collections
try {
  const collections = await listCollections();
  console.log("Collections:", collections);
} catch (error) {
  if (error instanceof APIError) {
    console.error("API Error:", error.message, error.statusCode);
  }
}

// Create a collection
try {
  const response = await createCollection("my-collection");
  console.log("Created:", response.collection_name);
} catch (error) {
  // Handle error
}

// Delete a collection
try {
  const response = await deleteCollection("my-collection");
  console.log("Deleted successfully");
} catch (error) {
  // Handle error
}

// Upload a document
try {
  const file = new File(["content"], "document.pdf");
  const response = await uploadDocument(file, "my-collection");
  console.log(
    `Created ${response.chunks_created} chunks in ${response.processing_time}s`,
  );
} catch (error) {
  // Handle error
}

// Query documents
try {
  const response = await queryDocuments("What is RAG?", "my-collection");
  console.log("Answer:", response.answer);
  console.log("Sources:", response.sources);
} catch (error) {
  // Handle error
}
```

## Error Handling

All API functions throw `APIError` on failure. The error includes:

- `message`: Human-readable error message
- `statusCode`: HTTP status code (if available)
- `details`: Additional error details from the server

## Configuration

Edit `src/config/api.config.ts` to change:

- `baseURL`: Backend API base URL (default: http://localhost:8000)
- `timeout`: Default request timeout (default: 30s)
- `uploadTimeout`: File upload timeout (default: 2 minutes)
- `queryTimeout`: Query processing timeout (default: 1 minute)

## Testing

Tests are located in `tests/services/api.test.ts`. Run with:

```bash
npm test -- tests/services/api.test.ts
```
