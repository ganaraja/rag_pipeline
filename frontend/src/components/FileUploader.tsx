import React, { useState } from "react";
import { uploadDocument } from "../services/api";
import { UploadResponse } from "../types";

export interface FileUploaderProps {
  selectedCollection: string | null;
  onUploadComplete?: (stats: UploadResponse) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  selectedCollection,
  onUploadComplete,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const SUPPORTED_FORMATS = [
    ".pdf",
    ".doc",
    ".docx",
    ".md",
    ".markdown",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
  ];

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const validateFile = (): string | null => {
    if (!selectedFile) {
      return "Please select a file to upload";
    }

    if (!selectedCollection) {
      return "Please select a collection first";
    }

    // Check file format
    const fileExtension = selectedFile.name
      .toLowerCase()
      .substring(selectedFile.name.lastIndexOf("."));
    const fileType = selectedFile.type.toLowerCase();

    const isValidFormat =
      SUPPORTED_FORMATS.includes(fileExtension) ||
      SUPPORTED_FORMATS.includes(fileType);

    if (!isValidFormat) {
      return "Unsupported file format. Please upload PDF, Word, or Markdown files.";
    }

    return null;
  };

  const handleUpload = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate
    const validationError = validateFile();
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    setUploading(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response = await uploadDocument(selectedFile!, selectedCollection!);

      if (response.success) {
        const message = `Upload successful! Created ${response.chunks_created} chunks in ${response.processing_time.toFixed(2)}s`;
        setSuccessMessage(message);
        setSelectedFile(null);

        // Reset file input
        const fileInput = document.getElementById(
          "file-input",
        ) as HTMLInputElement;
        if (fileInput) {
          fileInput.value = "";
        }

        // Notify parent
        if (onUploadComplete) {
          onUploadComplete(response);
        }
      } else {
        setErrorMessage(response.message || "Upload failed");
      }
    } catch (err: any) {
      const message = err.message || "Failed to upload document";
      setErrorMessage(message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-uploader">
      <form onSubmit={handleUpload}>
        <div className="file-input-container">
          <label htmlFor="file-input">Select file:</label>
          <input
            id="file-input"
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
            accept=".pdf,.doc,.docx,.md,.markdown"
          />
          {selectedFile && (
            <div className="selected-filename" role="status">
              Selected: {selectedFile.name}
            </div>
          )}
        </div>

        <button type="submit" disabled={uploading || !selectedFile}>
          {uploading ? "Uploading..." : "Upload Document"}
        </button>
      </form>

      {uploading && (
        <div className="upload-progress" role="status">
          <div className="progress-indicator">Processing document...</div>
        </div>
      )}

      {successMessage && (
        <div className="success-message" role="status">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="error-message" role="alert">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
