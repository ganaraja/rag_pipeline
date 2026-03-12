# Collection Management Components

This document describes the collection management components implemented for the RAG Full-Stack Application admin interface.

## Components Implemented

### 1. CollectionManager (Task 15.1)

**Location:** `src/components/CollectionManager.tsx`

**Purpose:** Displays a dropdown combo box for viewing and selecting Qdrant collections.

**Features:**

- Fetches collections from API on component mount
- Displays "None" when no collections exist
- Automatically selects the first collection as default
- Handles collection change events via callback
- Displays error messages for fetch failures
- Exposes a `refresh()` method via ref for parent components to trigger re-fetch

**Props:**

- `onCollectionChange: (collectionName: string | null) => void` - Callback when selection changes

**Ref Methods:**

- `refresh: () => void` - Refreshes the collection list from the API

**Tests:** `tests/components/CollectionManager.test.tsx` (6 tests)

---

### 2. CollectionCreator (Task 15.3)

**Location:** `src/components/CollectionCreator.tsx`

**Purpose:** Provides UI for creating new collections with validation.

**Features:**

- "Create Collection" button that reveals input form
- Input field for collection name with validation
- Validates against Qdrant naming requirements:
  - Non-empty
  - Only alphanumeric, hyphens, and underscores
  - Maximum 255 characters
- Calls API to create collection
- Displays success/error messages
- Triggers parent refresh callback on success
- Cancel button to hide input form

**Props:**

- `onCollectionCreated: (collectionName: string) => void` - Callback when collection is created

**Tests:** `tests/components/CollectionCreator.test.tsx` (9 tests)

---

### 3. CollectionDeleter (Task 15.5)

**Location:** `src/components/CollectionDeleter.tsx`

**Purpose:** Provides UI for deleting collections with confirmation.

**Features:**

- "Delete Collection" button (disabled when no collection selected)
- Displays error when attempting to delete with no selection
- Shows confirmation dialog: "Are you sure you want to delete the collection?"
- Calls API to delete collection on confirmation
- Displays success/error messages
- Triggers parent refresh callback on success
- Cancel button to abort deletion

**Props:**

- `selectedCollection: string | null` - Currently selected collection
- `onCollectionDeleted: () => void` - Callback when collection is deleted

**Tests:** `tests/components/CollectionDeleter.test.tsx` (8 tests)

---

## Integration Example

See `src/App.tsx` for a complete integration example showing how these components work together:

```typescript
import React, { useState, useRef } from "react";
import {
  CollectionManager,
  CollectionManagerRef,
  CollectionCreator,
  CollectionDeleter,
} from "./components";

const App: React.FC = () => {
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const collectionManagerRef = useRef<CollectionManagerRef>(null);

  const handleCollectionChange = (collectionName: string | null) => {
    setSelectedCollection(collectionName);
  };

  const handleCollectionCreated = (_collectionName: string) => {
    // Refresh the collection list
    if (collectionManagerRef.current) {
      collectionManagerRef.current.refresh();
    }
  };

  const handleCollectionDeleted = () => {
    // Refresh the collection list
    if (collectionManagerRef.current) {
      collectionManagerRef.current.refresh();
    }
  };

  return (
    <div>
      <CollectionManager
        ref={collectionManagerRef}
        onCollectionChange={handleCollectionChange}
      />

      <CollectionCreator
        onCollectionCreated={handleCollectionCreated}
      />

      <CollectionDeleter
        selectedCollection={selectedCollection}
        onCollectionDeleted={handleCollectionDeleted}
      />
    </div>
  );
};
```

## Test Coverage

All components have comprehensive test coverage using React Testing Library:

- **CollectionManager:** 6 tests covering loading, empty state, collection display, selection, and error handling
- **CollectionCreator:** 9 tests covering button display, input validation, creation flow, error handling, and cancellation
- **CollectionDeleter:** 8 tests covering button states, confirmation dialog, deletion flow, error handling, and cancellation

**Total:** 23 tests, all passing

## Requirements Satisfied

These components satisfy the following requirements from the spec:

- **Requirement 2.1-2.5:** Admin Interface - Collection Management Display
- **Requirement 3.1-3.7:** Admin Interface - Collection Creation
- **Requirement 4.1-4.7:** Admin Interface - Collection Deletion
- **Requirement 1.2:** Testing infrastructure with Jest and React Testing Library
- **Requirement 1.4:** Test updates for all code changes

## API Integration

All components use the API service layer (`src/services/api.ts`) which provides:

- `listCollections()` - Fetch all collections
- `createCollection(name)` - Create a new collection
- `deleteCollection(name)` - Delete a collection

The API service handles error cases and provides consistent error messages through the `APIError` class.

## Build Configuration

The project includes a separate TypeScript configuration for builds (`tsconfig.build.json`) that excludes test files, ensuring clean production builds.

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test:watch

# Run tests with coverage
npm test:coverage

# Run only collection management tests
npm test -- --testPathPattern="CollectionManager|CollectionCreator|CollectionDeleter"
```

## Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```
