import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatInterface } from "../../src/components/ChatInterface";
import * as api from "../../src/services/api";

// Mock the API module
jest.mock("../../src/services/api");

describe("ChatInterface", () => {
  const mockedQueryDocuments = api.queryDocuments as jest.MockedFunction<
    typeof api.queryDocuments
  >;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Message Display", () => {
    it("should render empty state when no messages", () => {
      render(<ChatInterface selectedCollection="test-collection" />);

      expect(
        screen.getByText(/Start a conversation by asking a question/),
      ).toBeInTheDocument();
    });

    it("should display user message after submission", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "What is RAG?");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText("What is RAG?")).toBeInTheDocument();
      });
    });

    it("should display assistant message after response", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "RAG stands for Retrieval-Augmented Generation",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "What is RAG?");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(
          screen.getByText("RAG stands for Retrieval-Augmented Generation"),
        ).toBeInTheDocument();
      });
    });

    it("should display timestamps for messages", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        // Timestamps should be in format like "10:30 AM"
        const timestamps = screen.getAllByText(/\d{1,2}:\d{2}/);
        expect(timestamps.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Input and Send Functionality", () => {
    it("should render input field and send button", () => {
      render(<ChatInterface selectedCollection="test-collection" />);

      expect(screen.getByLabelText("Chat input")).toBeInTheDocument();
      expect(screen.getByLabelText("Send message")).toBeInTheDocument();
    });

    it("should update input value when typing", async () => {
      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input") as HTMLInputElement;

      await userEvent.type(input, "Test query");

      expect(input.value).toBe("Test query");
    });

    it("should clear input after sending message", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input") as HTMLInputElement;
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(input.value).toBe("");
      });
    });

    it("should not submit empty message", async () => {
      render(<ChatInterface selectedCollection="test-collection" />);

      const sendButton = screen.getByLabelText("Send message");

      expect(sendButton).toBeDisabled();
      expect(mockedQueryDocuments).not.toHaveBeenCalled();
    });

    it("should not submit whitespace-only message", async () => {
      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "   ");

      // Button should still be disabled for whitespace
      expect(sendButton).toBeDisabled();
    });

    it("should call queryDocuments with correct parameters", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "What is RAG?");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(mockedQueryDocuments).toHaveBeenCalledWith(
          "What is RAG?",
          "test-collection",
        );
      });
    });
  });

  describe("Loading State", () => {
    it("should display loading indicator during query processing", async () => {
      let resolveQuery: (value: any) => void;
      const queryPromise = new Promise((resolve) => {
        resolveQuery = resolve;
      });
      mockedQueryDocuments.mockReturnValue(queryPromise as any);

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText("Thinking...")).toBeInTheDocument();
      });

      // Resolve the query
      resolveQuery!({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      await waitFor(() => {
        expect(screen.queryByText("Thinking...")).not.toBeInTheDocument();
      });
    });

    it("should disable input during processing", async () => {
      let resolveQuery: (value: any) => void;
      const queryPromise = new Promise((resolve) => {
        resolveQuery = resolve;
      });
      mockedQueryDocuments.mockReturnValue(queryPromise as any);

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(input).toBeDisabled();
        expect(sendButton).toBeDisabled();
      });

      // Resolve the query
      resolveQuery!({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
    });

    it("should change send button text during loading", async () => {
      let resolveQuery: (value: any) => void;
      const queryPromise = new Promise((resolve) => {
        resolveQuery = resolve;
      });
      mockedQueryDocuments.mockReturnValue(queryPromise as any);

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      let sendButton = screen.getByLabelText("Send message");

      expect(sendButton).toHaveTextContent("Send");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        sendButton = screen.getByLabelText("Send message");
        expect(sendButton).toHaveTextContent("...");
      });

      // Resolve the query
      resolveQuery!({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      await waitFor(() => {
        sendButton = screen.getByLabelText("Send message");
        expect(sendButton).toHaveTextContent("Send");
      });
    });
  });

  describe("Auto-scroll Behavior", () => {
    it("should auto-scroll to latest message", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      // Mock scrollIntoView
      const mockScrollIntoView = jest.fn();
      Element.prototype.scrollIntoView = mockScrollIntoView;

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(mockScrollIntoView).toHaveBeenCalled();
      });
    });
  });

  describe("Source Chunk Display", () => {
    it("should display sources toggle when sources are available", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [
          {
            id: 1,
            text: "Source chunk text",
            score: 0.95,
            metadata: {},
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/Sources \(1\)/)).toBeInTheDocument();
      });
    });

    it("should expand sources when toggle is clicked", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [
          {
            id: 1,
            text: "Source chunk text",
            score: 0.95,
            metadata: {},
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/Sources \(1\)/)).toBeInTheDocument();
      });

      const sourcesToggle = screen.getByText(/Sources \(1\)/);
      await userEvent.click(sourcesToggle);

      await waitFor(() => {
        expect(screen.getByText("Source chunk text")).toBeInTheDocument();
        expect(screen.getByText(/Score: 0.950/)).toBeInTheDocument();
      });
    });

    it("should collapse sources when toggle is clicked again", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [
          {
            id: 1,
            text: "Source chunk text",
            score: 0.95,
            metadata: {},
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/Sources \(1\)/)).toBeInTheDocument();
      });

      const sourcesToggle = screen.getByText(/Sources \(1\)/);

      // Expand
      await userEvent.click(sourcesToggle);
      await waitFor(() => {
        expect(screen.getByText("Source chunk text")).toBeInTheDocument();
      });

      // Collapse
      await userEvent.click(sourcesToggle);
      await waitFor(() => {
        expect(screen.queryByText("Source chunk text")).not.toBeInTheDocument();
      });
    });

    it("should display multiple sources", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [
          {
            id: 1,
            text: "First source",
            score: 0.95,
            metadata: {},
          },
          {
            id: 2,
            text: "Second source",
            score: 0.85,
            metadata: {},
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/Sources \(2\)/)).toBeInTheDocument();
      });

      const sourcesToggle = screen.getByText(/Sources \(2\)/);
      await userEvent.click(sourcesToggle);

      await waitFor(() => {
        expect(screen.getByText("First source")).toBeInTheDocument();
        expect(screen.getByText("Second source")).toBeInTheDocument();
        expect(screen.getByText("Source 1")).toBeInTheDocument();
        expect(screen.getByText("Source 2")).toBeInTheDocument();
      });
    });

    it("should display source metadata", async () => {
      mockedQueryDocuments.mockResolvedValue({
        answer: "Test answer",
        sources: [
          {
            id: 1,
            text: "Source chunk text",
            score: 0.95,
            metadata: {
              document_name: "test.pdf",
              page: 5,
            },
          },
        ],
        retrieval_time: 0.5,
        generation_time: 1.0,
      });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/Sources \(1\)/)).toBeInTheDocument();
      });

      const sourcesToggle = screen.getByText(/Sources \(1\)/);
      await userEvent.click(sourcesToggle);

      await waitFor(() => {
        expect(screen.getByText(/document_name: test.pdf/)).toBeInTheDocument();
        expect(screen.getByText(/page: 5/)).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling", () => {
    it("should display error message when query fails", async () => {
      const errorMessage = "Failed to retrieve documents";
      mockedQueryDocuments.mockRejectedValue(new Error(errorMessage));

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByRole("alert")).toBeInTheDocument();
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });

    it("should display error in chat when query fails", async () => {
      const errorMessage = "Connection timeout";
      mockedQueryDocuments.mockRejectedValue(new Error(errorMessage));

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      await userEvent.type(input, "Test query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Error: Connection timeout/),
        ).toBeInTheDocument();
      });
    });

    it("should show error when no collection is selected", async () => {
      render(<ChatInterface selectedCollection={null} />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      // Input should be disabled
      expect(input).toBeDisabled();
      expect(sendButton).toBeDisabled();

      expect(
        screen.getByPlaceholderText("Select a collection to start chatting"),
      ).toBeInTheDocument();
    });

    it("should display error when submitting without collection", async () => {
      render(<ChatInterface selectedCollection={null} />);

      const input = screen.getByLabelText("Chat input");

      // Input is disabled, so we can't type
      expect(input).toBeDisabled();
      expect(mockedQueryDocuments).not.toHaveBeenCalled();
    });
  });

  describe("Multiple Messages", () => {
    it("should display multiple conversation turns", async () => {
      mockedQueryDocuments
        .mockResolvedValueOnce({
          answer: "First answer",
          sources: [],
          retrieval_time: 0.5,
          generation_time: 1.0,
        })
        .mockResolvedValueOnce({
          answer: "Second answer",
          sources: [],
          retrieval_time: 0.5,
          generation_time: 1.0,
        });

      render(<ChatInterface selectedCollection="test-collection" />);

      const input = screen.getByLabelText("Chat input");
      const sendButton = screen.getByLabelText("Send message");

      // First message
      await userEvent.type(input, "First query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText("First query")).toBeInTheDocument();
        expect(screen.getByText("First answer")).toBeInTheDocument();
      });

      // Second message
      await userEvent.type(input, "Second query");
      await userEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText("Second query")).toBeInTheDocument();
        expect(screen.getByText("Second answer")).toBeInTheDocument();
      });

      // All messages should be visible
      expect(screen.getByText("First query")).toBeInTheDocument();
      expect(screen.getByText("First answer")).toBeInTheDocument();
      expect(screen.getByText("Second query")).toBeInTheDocument();
      expect(screen.getByText("Second answer")).toBeInTheDocument();
    });
  });
});
