// Collection models
export interface Collection {
  name: string;
}

export interface CreateCollectionRequest {
  collection_name: string;
}

export interface CreateCollectionResponse {
  success: boolean;
  collection_name: string;
  message?: string;
}

export interface DeleteCollectionResponse {
  success: boolean;
  message?: string;
}

// Upload models
export interface UploadRequest {
  file: File;
  collection_name: string;
}

export interface UploadResponse {
  success: boolean;
  chunks_created: number;
  processing_time: number;
  message?: string;
}

// Query models
export interface QueryRequest {
  query: string;
  collection_name: string;
}

export interface QueryResponse {
  answer: string;
  sources: SourceChunk[];
  retrieval_time: number;
  generation_time: number;
}

export interface SourceChunk {
  id: number;
  text: string;
  score: number;
  metadata: Record<string, any>;
}

// Message models for chat interface
export interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: SourceChunk[];
}
