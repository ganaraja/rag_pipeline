import React, { useState, useEffect, useRef } from "react";
import { queryDocuments } from "../services/api";
import { Message, SourceChunk } from "../types";
import styles from "./ChatInterface.module.css";

export interface ChatInterfaceProps {
  selectedCollection: string | null;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  selectedCollection,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(
    new Set(),
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleSourceExpansion = (messageId: string) => {
    setExpandedSources((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    const trimmedQuery = inputValue.trim();
    if (!trimmedQuery) {
      return;
    }

    if (!selectedCollection) {
      setErrorMessage("Please select a collection first");
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: "user",
      content: trimmedQuery,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setLoading(true);
    setErrorMessage(null);

    try {
      const response = await queryDocuments(trimmedQuery, selectedCollection);

      // Add assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        type: "assistant",
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const message = err.message || "Failed to get response";
      setErrorMessage(message);

      // Add error message to chat
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        type: "assistant",
        content: `Error: ${message}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);
  };

  const formatTimestamp = (date: Date): string => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.emptyState}>
            <p>
              Start a conversation by asking a question about your documents.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`${styles.messageWrapper} ${
              message.type === "user"
                ? styles.userMessageWrapper
                : styles.assistantMessageWrapper
            }`}
          >
            <div
              className={`${styles.messageBubble} ${
                message.type === "user"
                  ? styles.userMessage
                  : styles.assistantMessage
              }`}
            >
              <div className={styles.messageContent}>{message.content}</div>
              <div className={styles.messageTimestamp}>
                {formatTimestamp(message.timestamp)}
              </div>
            </div>

            {message.sources && message.sources.length > 0 && (
              <div className={styles.sourcesContainer}>
                <button
                  className={styles.sourcesToggle}
                  onClick={() => toggleSourceExpansion(message.id)}
                  aria-expanded={expandedSources.has(message.id)}
                >
                  {expandedSources.has(message.id) ? "▼" : "▶"} Sources (
                  {message.sources.length})
                </button>

                {expandedSources.has(message.id) && (
                  <div className={styles.sourcesList}>
                    {message.sources.map((source, index) => (
                      <div key={index} className={styles.sourceCard}>
                        <div className={styles.sourceHeader}>
                          <span className={styles.sourceNumber}>
                            Source {index + 1}
                          </span>
                          <span className={styles.sourceScore}>
                            Score: {source.score.toFixed(3)}
                          </span>
                        </div>
                        <div className={styles.sourceText}>{source.text}</div>
                        {source.metadata &&
                          Object.keys(source.metadata).length > 0 && (
                            <div className={styles.sourceMetadata}>
                              {Object.entries(source.metadata).map(
                                ([key, value]) => (
                                  <span
                                    key={key}
                                    className={styles.metadataTag}
                                  >
                                    {key}: {String(value)}
                                  </span>
                                ),
                              )}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className={styles.loadingIndicator}>
            <div className={styles.loadingDots}>
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className={styles.inputForm}>
        {errorMessage && (
          <div className={styles.errorBanner} role="alert">
            {errorMessage}
          </div>
        )}

        <div className={styles.inputContainer}>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={
              selectedCollection
                ? "Ask a question about your documents..."
                : "Select a collection to start chatting"
            }
            disabled={loading || !selectedCollection}
            className={styles.input}
            aria-label="Chat input"
          />
          <button
            type="submit"
            disabled={loading || !inputValue.trim() || !selectedCollection}
            className={styles.sendButton}
            aria-label="Send message"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
};
