import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CollectionManager } from "../../src/components/CollectionManager";
import * as api from "../../src/services/api";

// Mock the API module
jest.mock("../../src/services/api");

describe("CollectionManager", () => {
  const mockOnCollectionChange = jest.fn();
  const mockedListCollections = api.listCollections as jest.MockedFunction<
    typeof api.listCollections
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render loading state initially", () => {
    mockedListCollections.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    expect(screen.getByText("Loading collections...")).toBeInTheDocument();
  });

  it('should display "None" when no collections exist', async () => {
    mockedListCollections.mockResolvedValue([]);

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select).toBeDisabled();
    expect(screen.getByText("None")).toBeInTheDocument();
    expect(mockOnCollectionChange).toHaveBeenCalledWith(null);
  });

  it("should display collections and select default", async () => {
    const collections = ["collection1", "collection2", "collection3"];
    mockedListCollections.mockResolvedValue(collections);

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select).not.toBeDisabled();

    // Check that all collections are in the dropdown
    collections.forEach((collection) => {
      expect(screen.getByText(collection)).toBeInTheDocument();
    });

    // Check that first collection is selected by default
    expect(select.value).toBe("collection1");
    expect(mockOnCollectionChange).toHaveBeenCalledWith("collection1");
  });

  it("should handle collection selection change", async () => {
    const collections = ["collection1", "collection2"];
    mockedListCollections.mockResolvedValue(collections);

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;

    // Change selection
    await userEvent.selectOptions(select, "collection2");

    expect(select.value).toBe("collection2");
    expect(mockOnCollectionChange).toHaveBeenCalledWith("collection2");
  });

  it("should display error message on fetch failure", async () => {
    const errorMessage = "Failed to fetch collections";
    mockedListCollections.mockRejectedValue(new Error(errorMessage));

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(mockOnCollectionChange).toHaveBeenCalledWith(null);
  });

  it("should handle empty string selection", async () => {
    const collections = ["collection1", "collection2"];
    mockedListCollections.mockResolvedValue(collections);

    render(<CollectionManager onCollectionChange={mockOnCollectionChange} />);

    await waitFor(() => {
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    const select = screen.getByRole("combobox") as HTMLSelectElement;

    // Select empty option
    await userEvent.selectOptions(select, "");

    expect(select.value).toBe("");
    expect(mockOnCollectionChange).toHaveBeenCalledWith(null);
  });
});
