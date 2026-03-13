import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileUploader } from "../../src/components/FileUploader";
import * as api from "../../src/services/api";

// Mock the API module
jest.mock("../../src/services/api");

describe("FileUploader", () => {
  const mockOnUploadComplete = jest.fn();
  const mockedUploadDocument = api.uploadDocument as jest.MockedFunction<
    typeof api.uploadDocument
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createMockFile = (
    name: string,
    type: string,
    size: number = 1024,
  ): File => {
    const file = new File(["test content"], name, { type });
    Object.defineProperty(file, "size", { value: size });
    return file;
  };

  it("should render file input and upload button", () => {
    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    expect(screen.getByLabelText("Select file:")).toBeInTheDocument();
    expect(screen.getByText("Upload Document")).toBeInTheDocument();
  });

  it("should display selected filename when file is selected", async () => {
    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    await waitFor(() => {
      expect(
        screen.getByText(/Selected: test-document.pdf/),
      ).toBeInTheDocument();
    });
  });

  it("should display validation error when no file is selected", async () => {
    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const uploadButton = screen.getByText("Upload Document");

    // Button should be disabled when no file is selected
    expect(uploadButton).toBeDisabled();
    expect(mockedUploadDocument).not.toHaveBeenCalled();
  });

  it("should display validation error when no collection is selected", async () => {
    render(
      <FileUploader
        selectedCollection={null}
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Please select a collection first"),
    ).toBeInTheDocument();
    expect(mockedUploadDocument).not.toHaveBeenCalled();
  });

  it("should display validation error for unsupported file format", async () => {
    // Don't mock the upload function for this test - it shouldn't be called
    mockedUploadDocument.mockRejectedValue(new Error("Should not be called"));

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    // Create a file with unsupported extension
    const file = createMockFile(
      "test-document.xyz",
      "application/octet-stream",
    );
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    // Manually set the files property to bypass accept attribute
    Object.defineProperty(fileInput, "files", {
      value: [file],
      writable: false,
    });

    // Trigger change event
    const changeEvent = new Event("change", { bubbles: true });
    fileInput.dispatchEvent(changeEvent);

    await waitFor(() => {
      expect(
        screen.getByText(/Selected: test-document.xyz/),
      ).toBeInTheDocument();
    });

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(/Unsupported file format/)).toBeInTheDocument();
    expect(mockedUploadDocument).not.toHaveBeenCalled();
  });

  it("should successfully upload PDF file", async () => {
    mockedUploadDocument.mockResolvedValue({
      success: true,
      chunks_created: 42,
      processing_time: 3.5,
    });

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Upload successful! Created 42 chunks in 3.50s/),
    ).toBeInTheDocument();
    expect(mockedUploadDocument).toHaveBeenCalledWith(file, "test-collection");
    expect(mockOnUploadComplete).toHaveBeenCalledWith({
      success: true,
      chunks_created: 42,
      processing_time: 3.5,
    });
  });

  it("should successfully upload Word document", async () => {
    mockedUploadDocument.mockResolvedValue({
      success: true,
      chunks_created: 15,
      processing_time: 2.1,
    });

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile(
      "test-document.docx",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    );
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Upload successful! Created 15 chunks in 2.10s/),
    ).toBeInTheDocument();
    expect(mockedUploadDocument).toHaveBeenCalledWith(file, "test-collection");
  });

  it("should successfully upload Markdown file", async () => {
    mockedUploadDocument.mockResolvedValue({
      success: true,
      chunks_created: 8,
      processing_time: 1.2,
    });

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.md", "text/markdown");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Upload successful! Created 8 chunks in 1.20s/),
    ).toBeInTheDocument();
    expect(mockedUploadDocument).toHaveBeenCalledWith(file, "test-collection");
  });

  it("should display progress indicator during upload", async () => {
    // Create a promise that we can control
    let resolveUpload: (value: any) => void;
    const uploadPromise = new Promise((resolve) => {
      resolveUpload = resolve;
    });
    mockedUploadDocument.mockReturnValue(uploadPromise as any);

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    // Progress indicator should be visible
    await waitFor(() => {
      expect(screen.getByText("Uploading...")).toBeInTheDocument();
      expect(screen.getByText("Processing document...")).toBeInTheDocument();
    });

    // Resolve the upload
    resolveUpload!({
      success: true,
      chunks_created: 10,
      processing_time: 1.0,
    });

    // Progress indicator should disappear
    await waitFor(() => {
      expect(screen.queryByText("Uploading...")).not.toBeInTheDocument();
    });
  });

  it("should display error message on upload failure", async () => {
    const errorMessage = "Failed to process document";
    mockedUploadDocument.mockRejectedValue(new Error(errorMessage));

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(mockOnUploadComplete).not.toHaveBeenCalled();
  });

  it("should reset file input after successful upload", async () => {
    mockedUploadDocument.mockResolvedValue({
      success: true,
      chunks_created: 10,
      processing_time: 1.5,
    });

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    expect(screen.getByText(/Selected: test-document.pdf/)).toBeInTheDocument();

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    // File input should be reset
    await waitFor(() => {
      expect(
        screen.queryByText(/Selected: test-document.pdf/),
      ).not.toBeInTheDocument();
    });
  });

  it("should disable upload button when no file is selected", () => {
    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const uploadButton = screen.getByText("Upload Document");
    expect(uploadButton).toBeDisabled();
  });

  it("should disable controls during upload", async () => {
    // Create a promise that we can control
    let resolveUpload: (value: any) => void;
    const uploadPromise = new Promise((resolve) => {
      resolveUpload = resolve;
    });
    mockedUploadDocument.mockReturnValue(uploadPromise as any);

    render(
      <FileUploader
        selectedCollection="test-collection"
        onUploadComplete={mockOnUploadComplete}
      />,
    );

    const file = createMockFile("test-document.pdf", "application/pdf");
    const fileInput = screen.getByLabelText("Select file:") as HTMLInputElement;

    await userEvent.upload(fileInput, file);

    const uploadButton = screen.getByText("Upload Document");
    await userEvent.click(uploadButton);

    // Controls should be disabled during upload
    await waitFor(() => {
      expect(fileInput).toBeDisabled();
      expect(screen.getByText("Uploading...")).toBeDisabled();
    });

    // Resolve the upload
    resolveUpload!({
      success: true,
      chunks_created: 10,
      processing_time: 1.0,
    });

    // Controls should be enabled again
    await waitFor(() => {
      expect(fileInput).not.toBeDisabled();
    });
  });
});
