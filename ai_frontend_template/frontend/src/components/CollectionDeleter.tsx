import React, { useState } from "react";
import { deleteCollection } from "../services/api";

export interface CollectionDeleterProps {
  selectedCollection: string | null;
  onCollectionDeleted: () => void;
}

export const CollectionDeleter: React.FC<CollectionDeleterProps> = ({
  selectedCollection,
  onCollectionDeleted,
}) => {
  const [showConfirmation, setShowConfirmation] = useState<boolean>(false);
  const [deleting, setDeleting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDeleteClick = () => {
    setSuccessMessage(null);
    setErrorMessage(null);

    if (!selectedCollection) {
      setErrorMessage("No collection selected");
      return;
    }

    setShowConfirmation(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedCollection) {
      setErrorMessage("No collection selected");
      setShowConfirmation(false);
      return;
    }

    setDeleting(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await deleteCollection(selectedCollection);

      if (response.success) {
        setSuccessMessage(
          `Collection "${selectedCollection}" deleted successfully`,
        );
        setShowConfirmation(false);
        onCollectionDeleted();
      } else {
        setErrorMessage(response.message || "Failed to delete collection");
        setShowConfirmation(false);
      }
    } catch (err: any) {
      const message = err.message || "Failed to delete collection";
      setErrorMessage(message);
      setShowConfirmation(false);
    } finally {
      setDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setShowConfirmation(false);
    setErrorMessage(null);
  };

  return (
    <div className="collection-deleter">
      {!showConfirmation ? (
        <button
          onClick={handleDeleteClick}
          disabled={deleting || !selectedCollection}
        >
          Delete Collection
        </button>
      ) : (
        <div className="confirmation-dialog">
          <p>Are you sure you want to delete the collection?</p>
          <button onClick={handleConfirmDelete} disabled={deleting}>
            {deleting ? "Deleting..." : "Confirm"}
          </button>
          <button onClick={handleCancelDelete} disabled={deleting}>
            Cancel
          </button>
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
