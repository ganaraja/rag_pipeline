import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollectionDeleter } from "../../src/components/CollectionDeleter";
import * as api from "../../src/services/api";

// Mock the API module
jest.mock("../../src/services/api");

describe("CollectionDeleter", () => {
  const mockOnCollectionDeleted = jest.fn();
  const mockedDeleteCollection = api.deleteCollection as jest.MockedFunction<
    typeof api.deleteCollection
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render delete button", () => {
    render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    expect(screen.getByText("Delete Collection")).toBeInTheDocument();
  });

  it("should disable delete button when no collection is selected", () => {
    render(
      <CollectionDeleter
        selectedCollection={null}
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    const deleteButton = screen.getByText("Delete Collection");
    expect(deleteButton).toBeDisabled();
  });

  it("should show error when trying to delete with no collection selected", async () => {
    // Start with a collection selected, then change to null
    const { rerender } = render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Click delete button while collection is selected
    await userEvent.click(screen.getByText("Delete Collection"));

    // Now change to no collection while confirmation is showing
    rerender(
      <CollectionDeleter
        selectedCollection={null}
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Try to confirm deletion with no collection
    const confirmButton = screen.getByText("Confirm");
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText("No collection selected")).toBeInTheDocument();
    expect(mockedDeleteCollection).not.toHaveBeenCalled();
  });

  it("should show confirmation dialog when delete is clicked", async () => {
    render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    const deleteButton = screen.getByText("Delete Collection");
    await userEvent.click(deleteButton);

    expect(
      screen.getByText("Are you sure you want to delete the collection?"),
    ).toBeInTheDocument();
    expect(screen.getByText("Confirm")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("should successfully delete collection on confirmation", async () => {
    const collectionName = "test-collection";
    mockedDeleteCollection.mockResolvedValue({
      success: true,
      message: "Collection deleted",
    });

    render(
      <CollectionDeleter
        selectedCollection={collectionName}
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Click delete button
    await userEvent.click(screen.getByText("Delete Collection"));

    // Confirm deletion
    const confirmButton = screen.getByText("Confirm");
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    expect(
      screen.getByText(`Collection "${collectionName}" deleted successfully`),
    ).toBeInTheDocument();
    expect(mockedDeleteCollection).toHaveBeenCalledWith(collectionName);
    expect(mockOnCollectionDeleted).toHaveBeenCalled();

    // Confirmation dialog should be hidden
    expect(
      screen.queryByText("Are you sure you want to delete the collection?"),
    ).not.toBeInTheDocument();
  });

  it("should display error message on deletion failure", async () => {
    const errorMessage = "Failed to delete collection";
    mockedDeleteCollection.mockRejectedValue(new Error(errorMessage));

    render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Click delete button
    await userEvent.click(screen.getByText("Delete Collection"));

    // Confirm deletion
    const confirmButton = screen.getByText("Confirm");
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(mockOnCollectionDeleted).not.toHaveBeenCalled();
  });

  it("should cancel deletion and hide confirmation dialog", async () => {
    render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Click delete button
    await userEvent.click(screen.getByText("Delete Collection"));

    // Cancel deletion
    const cancelButton = screen.getByText("Cancel");
    await userEvent.click(cancelButton);

    // Confirmation dialog should be hidden
    expect(
      screen.queryByText("Are you sure you want to delete the collection?"),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Delete Collection")).toBeInTheDocument();
    expect(mockedDeleteCollection).not.toHaveBeenCalled();
    expect(mockOnCollectionDeleted).not.toHaveBeenCalled();
  });

  it("should disable buttons while deleting", async () => {
    mockedDeleteCollection.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(
      <CollectionDeleter
        selectedCollection="test-collection"
        onCollectionDeleted={mockOnCollectionDeleted}
      />,
    );

    // Click delete button
    await userEvent.click(screen.getByText("Delete Collection"));

    // Click confirm
    const confirmButton = screen.getByText("Confirm");
    await userEvent.click(confirmButton);

    await waitFor(() => {
      expect(screen.getByText("Deleting...")).toBeInTheDocument();
    });

    // Both buttons should be disabled
    expect(screen.getByText("Deleting...")).toBeDisabled();
    expect(screen.getByText("Cancel")).toBeDisabled();
  });
});
