import React, {
  useEffect,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";
import { listCollections } from "../services/api";

export interface CollectionManagerProps {
  onCollectionChange: (collectionName: string | null) => void;
}

export interface CollectionManagerRef {
  refresh: () => void;
}

export const CollectionManager = forwardRef<
  CollectionManagerRef,
  CollectionManagerProps
>(({ onCollectionChange }, ref) => {
  const [collections, setCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(
    null,
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCollections = async () => {
    setLoading(true);
    setError(null);

    try {
      const fetchedCollections = await listCollections();
      setCollections(fetchedCollections);

      // Set default collection if available
      if (fetchedCollections.length > 0 && !selectedCollection) {
        const defaultCollection = fetchedCollections[0];
        setSelectedCollection(defaultCollection);
        onCollectionChange(defaultCollection);
      } else if (fetchedCollections.length === 0) {
        setSelectedCollection(null);
        onCollectionChange(null);
      }
    } catch (err: any) {
      const errorMessage = err.message || "Failed to fetch collections";
      setError(errorMessage);
      setCollections([]);
      setSelectedCollection(null);
      onCollectionChange(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCollections();
  }, []);

  // Expose refresh method to parent
  useImperativeHandle(ref, () => ({
    refresh: fetchCollections,
  }));

  const handleCollectionChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const value = event.target.value;
    const newSelection = value === "" ? null : value;
    setSelectedCollection(newSelection);
    onCollectionChange(newSelection);
  };

  if (loading) {
    return <div>Loading collections...</div>;
  }

  return (
    <div className="collection-manager">
      <label htmlFor="collection-select">Collection:</label>
      <select
        id="collection-select"
        value={selectedCollection || ""}
        onChange={handleCollectionChange}
        disabled={collections.length === 0}
      >
        {collections.length === 0 ? (
          <option value="">None</option>
        ) : (
          <>
            <option value="">Select a collection</option>
            {collections.map((collection) => (
              <option key={collection} value={collection}>
                {collection}
              </option>
            ))}
          </>
        )}
      </select>

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
    </div>
  );
});

CollectionManager.displayName = "CollectionManager";
