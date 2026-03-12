import React, { useState } from "react";
import { createCollection } from "../services/api";

export interface CollectionCreatorProps {
  onCollectionCreated: (collectionName: string) => void;
}

export const CollectionCreator: React.FC<CollectionCreatorProps> = ({
  onCollectionCreated,
}) => {
  const [showInput, setShowInput] = useState<boolean>(false);
  const [collectionName, setCollectionName] = useState<string>("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [creating, setCreating] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const validateCollectionName = (name: string): string | null => {
    if (!name || name.trim() === "") {
      return "Collection name cannot be empty";
    }

    // Qdrant naming requirements: alphanumeric, hyphens, underscores
    const qdrantNamePattern = /^[a-zA-Z0-9_-]+$/;
    if (!qdrantNamePattern.test(name)) {
      return "Collection name must contain only letters, numbers, hyphens, and underscores";
    }

    if (name.length > 255) {
      return "Collection name must be 255 characters or less";
    }

    return null;
  };

  const handleCreateClick = () => {
    setShowInput(true);
    setValidationError(null);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const handleCancel = () => {
    setShowInput(false);
    setCollectionName("");
    setValidationError(null);
    setSuccessMessage(null);
    setErrorMessage(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate collection name
    const error = validateCollectionName(collectionName);
    if (error) {
      setValidationError(error);
      return;
    }

    setValidationError(null);
    setCreating(true);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const response = await createCollection(collectionName);

      if (response.success) {
        setSuccessMessage(
          `Collection "${collectionName}" created successfully`,
        );
        setShowInput(false);
        setCollectionName("");
        onCollectionCreated(collectionName);
      } else {
        setErrorMessage(response.message || "Failed to create collection");
      }
    } catch (err: any) {
      const message = err.message || "Failed to create collection";
      setErrorMessage(message);
    } finally {
      setCreating(false);
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setCollectionName(event.target.value);
    setValidationError(null);
  };

  return (
    <div className="collection-creator">
      {!showInput ? (
        <button onClick={handleCreateClick} disabled={creating}>
          Create Collection
        </button>
      ) : (
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={collectionName}
            onChange={handleInputChange}
            placeholder="Enter collection name"
            disabled={creating}
            autoFocus
          />
          <button type="submit" disabled={creating}>
            {creating ? "Creating..." : "Submit"}
          </button>
          <button type="button" onClick={handleCancel} disabled={creating}>
            Cancel
          </button>
        </form>
      )}

      {validationError && (
        <div className="validation-error" role="alert">
          {validationError}
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
