import React, {
  useState,
  useRef,
  Component,
  ErrorInfo,
  ReactNode,
} from "react";
import {
  CollectionManager,
  CollectionManagerRef,
  CollectionCreator,
  CollectionDeleter,
  FileUploader,
  ChatInterface,
} from "./components";
import "./App.css";

// Error Boundary Component
interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <h1>⚠️ Something went wrong</h1>
            <p>An unexpected error occurred in the application.</p>
            {this.state.error && (
              <details className="error-details">
                <summary>Error details</summary>
                <pre>{this.state.error.toString()}</pre>
                {this.state.errorInfo && (
                  <pre>{this.state.errorInfo.componentStack}</pre>
                )}
              </details>
            )}
            <button onClick={this.handleReset} className="reset-button">
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Main App Component
type TabType = "admin" | "user";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>("admin");
  const [selectedCollection, setSelectedCollection] = useState<string | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
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

  const handleUploadComplete = () => {
    // Optional: Show notification or update UI
    setIsLoading(false);
  };

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
  };

  return (
    <ErrorBoundary>
      <div className="app">
        <header className="app-header">
          <h1>RAG Full-Stack Application</h1>
          <p className="app-subtitle">Retrieval-Augmented Generation System</p>
        </header>

        <nav className="tab-navigation">
          <button
            className={`tab-button ${activeTab === "admin" ? "active" : ""}`}
            onClick={() => handleTabChange("admin")}
            aria-selected={activeTab === "admin"}
            role="tab"
          >
            Admin
          </button>
          <button
            className={`tab-button ${activeTab === "user" ? "active" : ""}`}
            onClick={() => handleTabChange("user")}
            aria-selected={activeTab === "user"}
            role="tab"
          >
            User
          </button>
        </nav>

        <main className="app-content">
          {activeTab === "admin" && (
            <div className="admin-panel" role="tabpanel">
              <h2>Admin Interface</h2>
              <p className="panel-description">
                Manage collections and upload documents
              </p>

              <section className="collection-section">
                <h3>Collection Management</h3>
                <div className="collection-controls">
                  <div className="collection-selector">
                    <CollectionManager
                      ref={collectionManagerRef}
                      onCollectionChange={handleCollectionChange}
                    />
                  </div>

                  <div className="collection-actions">
                    <CollectionCreator
                      onCollectionCreated={handleCollectionCreated}
                    />
                    <CollectionDeleter
                      selectedCollection={selectedCollection}
                      onCollectionDeleted={handleCollectionDeleted}
                    />
                  </div>
                </div>

                {selectedCollection && (
                  <div className="selected-collection-info">
                    <span className="info-label">Active Collection:</span>
                    <span className="info-value">{selectedCollection}</span>
                  </div>
                )}
              </section>

              <section className="upload-section">
                <h3>Document Upload</h3>
                {isLoading && (
                  <div className="loading-overlay">
                    <div className="spinner"></div>
                    <p>Processing...</p>
                  </div>
                )}
                <FileUploader
                  selectedCollection={selectedCollection}
                  onUploadComplete={handleUploadComplete}
                />
              </section>
            </div>
          )}

          {activeTab === "user" && (
            <div className="user-panel" role="tabpanel">
              <h2>Chat Interface</h2>
              <p className="panel-description">
                Ask questions about your documents
              </p>

              {!selectedCollection && (
                <div className="no-collection-warning">
                  <p>
                    ⚠️ Please select a collection in the Admin tab before
                    chatting.
                  </p>
                </div>
              )}

              <div className="chat-section">
                <ChatInterface selectedCollection={selectedCollection} />
              </div>
            </div>
          )}
        </main>

        <footer className="app-footer">
          <p>
            Powered by Qdrant, FastAPI, and React | Multi-Embedding Retrieval
            Pipeline
          </p>
        </footer>
      </div>
    </ErrorBoundary>
  );
};

export default App;
