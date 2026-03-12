import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollectionCreator } from "../../src/components/CollectionCreator";
import * as api from "../../src/services/api";

// Mock the API module
jest.mock("../../src/services/api");

describe("CollectionCreator", () => {
  const mockOnCollectionCreated = jest.fn();
  const mockedCreateCollection = api.createCollection as jest.MockedFunction<
    typeof api.createCollection
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render create button initially", () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    expect(screen.getByText("Create Collection")).toBeInTheDocument();
  });

  it("should show input field when create button is clicked", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    const createButton = screen.getByText("Create Collection");
    await userEvent.click(createButton);

    expect(
      screen.getByPlaceholderText("Enter collection name"),
    ).toBeInTheDocument();
    expect(screen.getByText("Submit")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("should display validation error for empty collection name", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Collection name cannot be empty"),
    ).toBeInTheDocument();
    expect(mockedCreateCollection).not.toHaveBeenCalled();
  });

  it("should display validation error for invalid characters", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const input = screen.getByPlaceholderText("Enter collection name");
    await userEvent.type(input, "invalid name!@#");

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        /must contain only letters, numbers, hyphens, and underscores/,
      ),
    ).toBeInTheDocument();
    expect(mockedCreateCollection).not.toHaveBeenCalled();
  });

  it("should display validation error for name too long", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const input = screen.getByPlaceholderText("Enter collection name");
    const longName = "a".repeat(256);
    await userEvent.type(input, longName);

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/must be 255 characters or less/),
    ).toBeInTheDocument();
    expect(mockedCreateCollection).not.toHaveBeenCalled();
  });

  it("should successfully create collection with valid name", async () => {
    const collectionName = "test-collection_123";
    mockedCreateCollection.mockResolvedValue({
      success: true,
      collection_name: collectionName,
    });

    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const input = screen.getByPlaceholderText("Enter collection name");
    await userEvent.type(input, collectionName);

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    expect(
      screen.getByText(`Collection "${collectionName}" created successfully`),
    ).toBeInTheDocument();
    expect(mockedCreateCollection).toHaveBeenCalledWith(collectionName);
    expect(mockOnCollectionCreated).toHaveBeenCalledWith(collectionName);

    // Input should be hidden after success
    expect(
      screen.queryByPlaceholderText("Enter collection name"),
    ).not.toBeInTheDocument();
  });

  it("should display error message on creation failure", async () => {
    const errorMessage = "Collection already exists";
    mockedCreateCollection.mockRejectedValue(new Error(errorMessage));

    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const input = screen.getByPlaceholderText("Enter collection name");
    await userEvent.type(input, "test-collection");

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(mockOnCollectionCreated).not.toHaveBeenCalled();
  });

  it("should cancel and reset form", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const input = screen.getByPlaceholderText("Enter collection name");
    await userEvent.type(input, "test-collection");

    const cancelButton = screen.getByText("Cancel");
    await userEvent.click(cancelButton);

    // Should return to initial state
    expect(screen.getByText("Create Collection")).toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText("Enter collection name"),
    ).not.toBeInTheDocument();
    expect(mockedCreateCollection).not.toHaveBeenCalled();
  });

  it("should clear validation error when typing", async () => {
    render(<CollectionCreator onCollectionCreated={mockOnCollectionCreated} />);

    await userEvent.click(screen.getByText("Create Collection"));

    const submitButton = screen.getByText("Submit");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Enter collection name");
    await userEvent.type(input, "test");

    // Validation error should be cleared
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
