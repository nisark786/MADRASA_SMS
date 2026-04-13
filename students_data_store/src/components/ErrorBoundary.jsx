import React, { Component } from 'react';
import PropTypes from 'prop-types';

/**
 * Error Boundary Component
 * 
 * Catches React component errors and displays a user-friendly error page
 * instead of letting the app crash completely.
 * 
 * Features:
 * - Catches errors in child components
 * - Shows helpful error UI with details in dev mode
 * - Logs errors to console for debugging
 * - Provides option to retry/reset error state
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error Boundary caught an error:', error);
    console.error('Error info:', errorInfo);
    
    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Optional: Log to error tracking service
    if (window.__logError) {
      window.__logError({
        error: error.toString(),
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
      });
    }
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
      const isDev = process.env.NODE_ENV === 'development';
      const { error, errorInfo, errorCount } = this.state;

      return (
        <div className="flex h-screen w-full items-center justify-center bg-gradient-to-br from-red-50 to-pink-50">
          <div className="max-w-lg w-full mx-auto p-8 bg-white rounded-lg shadow-lg border border-red-200">
            {/* Header */}
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-red-600"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-red-900">Something went wrong</h1>
            </div>

            {/* Message */}
            <p className="text-gray-700 mb-6">
              The application encountered an unexpected error. Our team has been notified.
              {errorCount > 1 && (
                <span className="block text-sm text-red-600 mt-2 font-semibold">
                  (Error #{errorCount} - This error occurred {errorCount} times)
                </span>
              )}
            </p>

            {/* Error Details (Dev Only) */}
            {isDev && error && (
              <div className="mb-6 p-4 bg-gray-100 rounded border border-gray-300">
                <h2 className="font-bold text-gray-900 mb-2 text-sm">Error Details (Dev Mode):</h2>
                <div className="text-xs text-gray-700 font-mono overflow-auto max-h-40 bg-white p-3 rounded border border-gray-200">
                  <p className="font-bold text-red-600 mb-2">{error.toString()}</p>
                  {errorInfo && errorInfo.componentStack && (
                    <details>
                      <summary className="cursor-pointer font-bold text-gray-800 mb-2">
                        Component Stack Trace
                      </summary>
                      <pre className="whitespace-pre-wrap break-words text-gray-700">
                        {errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 px-4 py-2 bg-indigo-600 text-white font-medium rounded hover:bg-indigo-700 transition-colors"
              >
                Try Again
              </button>
              <a
                href="/dashboard"
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 font-medium rounded hover:bg-gray-300 transition-colors text-center"
              >
                Go to Dashboard
              </a>
            </div>

            {/* Additional Info */}
            <p className="text-xs text-gray-500 mt-4 text-center">
              If this problem persists, please contact support with error code: {this.state.errorCount}
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ErrorBoundary;
