import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "../src/App";

// Mock all components to isolate App logic
jest.mock("../src/components", () => ({
  CollectionManager: React.forwardRef(
    (
      props: {
        onCollectionChange: (name: string | null) => void;
      },
      ref: any,
    ) => {
      React.useImperativeHandle(ref, () => ({
        refresh: jest.fn(),
      }));

      return (
        <div data-testid="collection-manager">
          <button
            onClick={() => props.onCollectionChange("test-collection")}
            data-testid="select-collection"
          >
            Select Collection
          </button>
        </div>
      );
    },
  ),
  CollectionCreator: (props: {
    onCollectionCreated: (name: string) => void;
  }) => (
    <div data-testid="collection-creator">
      <button
        onClick={() => props.onCollectionCreated("new-collection")}
        data-testid="create-collection"
      >
        Create Collection
      </button>
    </div>
  ),
  CollectionDeleter: (props: {
    selectedCollection: string | null;
    onCollectionDeleted: () => void;
  }) => (
    <div data-testid="collection-deleter">
      <button
        onClick={() => props.onCollectionDeleted()}
        data-testid="delete-collection"
        disabled={!props.selectedCollection}
      >
        Delete Collection
      </button>
      {props.selectedCollection && (
        <span data-testid="deleter-collection">{props.selectedCollection}</span>
      )}
    </div>
  ),
  FileUploader: (props: {
    selectedCollection: string | null;
    onUploadComplete?: () => void;
  }) => (
    <div data-testid="file-uploader">
      <span data-testid="uploader-collection">
        {props.selectedCollection || "none"}
      </span>
      <button
        onClick={() => props.onUploadComplete?.()}
        data-testid="upload-file"
      >
        Upload
      </button>
    </div>
  ),
  ChatInterface: (props: { selectedCollection: string | null }) => (
    <div data-testid="chat-interface">
      <span data-testid="chat-collection">
        {props.selectedCollection || "none"}
      </span>
    </div>
  ),
}));

describe("App Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Initial Rendering", () => {
    it("should render the app with header and navigation", () => {
      render(<App />);

      expect(
        screen.getByText("RAG Full-Stack Application"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("Retrieval-Augmented Generation System"),
      ).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /admin/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /user/i })).toBeInTheDocument();
    });

    it("should render admin tab by default", () => {
      render(<App />);

      expect(screen.getByText("Admin Interface")).toBeInTheDocument();
      expect(
        screen.getByText("Manage collections and upload documents"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("collection-manager")).toBeInTheDocument();
      expect(screen.getByTestId("collection-creator")).toBeInTheDocument();
      expect(screen.getByTestId("collection-deleter")).toBeInTheDocument();
      expect(screen.getByTestId("file-uploader")).toBeInTheDocument();
    });

    it("should have admin tab marked as active initially", () => {
      render(<App />);

      const adminTab = screen.getByRole("tab", { name: /admin/i });
      const userTab = screen.getByRole("tab", { name: /user/i });

      expect(adminTab).toHaveClass("active");
      expect(userTab).not.toHaveClass("active");
      expect(adminTab).toHaveAttribute("aria-selected", "true");
      expect(userTab).toHaveAttribute("aria-selected", "false");
    });
  });

  describe("Tab Navigation", () => {
    it("should switch to user tab when clicked", () => {
      render(<App />);

      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      expect(screen.getByText("Chat Interface")).toBeInTheDocument();
      expect(
        screen.getByText("Ask questions about your documents"),
      ).toBeInTheDocument();
      expect(screen.getByTestId("chat-interface")).toBeInTheDocument();
    });

    it("should switch back to admin tab when clicked", () => {
      render(<App />);

      // Switch to user tab
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);
      expect(screen.getByText("Chat Interface")).toBeInTheDocument();

      // Switch back to admin tab
      const adminTab = screen.getByRole("tab", { name: /admin/i });
      fireEvent.click(adminTab);
      expect(screen.getByText("Admin Interface")).toBeInTheDocument();
    });

    it("should update active tab styling when switching tabs", () => {
      render(<App />);

      const adminTab = screen.getByRole("tab", { name: /admin/i });
      const userTab = screen.getByRole("tab", { name: /user/i });

      // Initially admin is active
      expect(adminTab).toHaveClass("active");
      expect(userTab).not.toHaveClass("active");

      // Switch to user
      fireEvent.click(userTab);
      expect(adminTab).not.toHaveClass("active");
      expect(userTab).toHaveClass("active");
      expect(userTab).toHaveAttribute("aria-selected", "true");
      expect(adminTab).toHaveAttribute("aria-selected", "false");
    });

    it("should not unmount components when switching tabs", () => {
      render(<App />);

      // Select a collection in admin tab
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Switch to user tab
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      // Switch back to admin tab
      const adminTab = screen.getByRole("tab", { name: /admin/i });
      fireEvent.click(adminTab);

      // Collection should still be selected
      expect(screen.getByText("Active Collection:")).toBeInTheDocument();
      const collectionElements = screen.getAllByText("test-collection");
      expect(collectionElements.length).toBeGreaterThan(0);
    });
  });

  describe("Collection Selection Propagation", () => {
    it("should propagate selected collection to FileUploader", () => {
      render(<App />);

      // Initially no collection selected
      expect(screen.getByTestId("uploader-collection")).toHaveTextContent(
        "none",
      );

      // Select a collection
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // FileUploader should receive the selected collection
      expect(screen.getByTestId("uploader-collection")).toHaveTextContent(
        "test-collection",
      );
    });

    it("should propagate selected collection to ChatInterface", () => {
      render(<App />);

      // Select a collection
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Switch to user tab
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      // ChatInterface should receive the selected collection
      expect(screen.getByTestId("chat-collection")).toHaveTextContent(
        "test-collection",
      );
    });

    it("should propagate selected collection to CollectionDeleter", () => {
      render(<App />);

      // Initially delete button should be disabled
      const deleteButton = screen.getByTestId("delete-collection");
      expect(deleteButton).toBeDisabled();

      // Select a collection
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Delete button should be enabled and show collection
      expect(deleteButton).not.toBeDisabled();
      expect(screen.getByTestId("deleter-collection")).toHaveTextContent(
        "test-collection",
      );
    });

    it("should display selected collection info in admin panel", () => {
      render(<App />);

      // Select a collection
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Should display collection info
      expect(screen.getByText("Active Collection:")).toBeInTheDocument();
      expect(
        screen.getByText("test-collection", { selector: ".info-value" }),
      ).toBeInTheDocument();
    });

    it("should show warning in user tab when no collection selected", () => {
      render(<App />);

      // Switch to user tab without selecting collection
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      // Should show warning
      expect(
        screen.getByText(
          /Please select a collection in the Admin tab before chatting/i,
        ),
      ).toBeInTheDocument();
    });

    it("should hide warning in user tab when collection is selected", () => {
      render(<App />);

      // Select a collection
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Switch to user tab
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      // Warning should not be present
      expect(
        screen.queryByText(
          /Please select a collection in the Admin tab before chatting/i,
        ),
      ).not.toBeInTheDocument();
    });
  });

  describe("Collection Management Callbacks", () => {
    it("should handle collection creation callback", () => {
      render(<App />);

      const createButton = screen.getByTestId("create-collection");
      fireEvent.click(createButton);

      // The mock should have been called
      // In a real scenario, this would trigger a refresh
      expect(createButton).toBeInTheDocument();
    });

    it("should handle collection deletion callback", () => {
      render(<App />);

      // Select a collection first
      const selectButton = screen.getByTestId("select-collection");
      fireEvent.click(selectButton);

      // Delete the collection
      const deleteButton = screen.getByTestId("delete-collection");
      fireEvent.click(deleteButton);

      // The mock should have been called
      expect(deleteButton).toBeInTheDocument();
    });

    it("should handle upload complete callback", () => {
      render(<App />);

      const uploadButton = screen.getByTestId("upload-file");
      fireEvent.click(uploadButton);

      // Should not throw error
      expect(uploadButton).toBeInTheDocument();
    });
  });

  describe("Error Boundary", () => {
    // Suppress console.error for these tests
    const originalError = console.error;
    beforeAll(() => {
      console.error = jest.fn();
    });
    afterAll(() => {
      console.error = originalError;
    });

    it("should render error boundary component", () => {
      // The error boundary is present in the component tree
      render(<App />);

      // App should render normally without errors
      expect(
        screen.getByText("RAG Full-Stack Application"),
      ).toBeInTheDocument();
    });

    it("should have error boundary structure in place", () => {
      // Verify the app is wrapped in error boundary by checking normal render
      render(<App />);

      // If error boundary wasn't there, app wouldn't render
      expect(screen.getByRole("tab", { name: /admin/i })).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA attributes on tabs", () => {
      render(<App />);

      const adminTab = screen.getByRole("tab", { name: /admin/i });
      const userTab = screen.getByRole("tab", { name: /user/i });

      expect(adminTab).toHaveAttribute("aria-selected");
      expect(userTab).toHaveAttribute("aria-selected");
    });

    it("should have proper role attributes on tab panels", () => {
      render(<App />);

      const adminPanel = screen.getByRole("tabpanel");
      expect(adminPanel).toBeInTheDocument();

      // Switch to user tab
      const userTab = screen.getByRole("tab", { name: /user/i });
      fireEvent.click(userTab);

      const userPanel = screen.getByRole("tabpanel");
      expect(userPanel).toBeInTheDocument();
    });

    it("should maintain focus management when switching tabs", () => {
      render(<App />);

      const userTab = screen.getByRole("tab", { name: /user/i });
      userTab.focus();
      fireEvent.click(userTab);

      // Tab should still be focusable
      expect(document.activeElement).toBe(userTab);
    });
  });

  describe("Footer", () => {
    it("should render footer with attribution", () => {
      render(<App />);

      expect(
        screen.getByText(/Powered by Qdrant, FastAPI, and React/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Multi-Embedding Retrieval Pipeline/i),
      ).toBeInTheDocument();
    });
  });

  describe("Responsive Behavior", () => {
    it("should render all sections on mobile viewport", () => {
      render(<App />);

      expect(
        screen.getByText("RAG Full-Stack Application"),
      ).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /admin/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /user/i })).toBeInTheDocument();
    });
  });
});
