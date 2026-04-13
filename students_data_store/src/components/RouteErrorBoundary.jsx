import React from 'react';
import PropTypes from 'prop-types';

/**
 * Route Error Boundary Component
 * 
 * A lightweight wrapper for individual route-level error boundaries.
 * Catches errors in specific routes without affecting the entire app.
 */
class RouteErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`Route Error (${this.props.routeName || 'Unknown')}):`, error);
    console.error('Error info:', errorInfo);
    this.setState({ error });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 p-4">
          <div className="text-center max-w-md">
            <h1 className="text-2xl font-bold text-red-600 mb-2">Page Error</h1>
            <p className="text-gray-700 mb-4">
              Failed to load {this.props.routeName || 'this page'}. Please try again.
            </p>
            <button
              onClick={this.handleReset}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

RouteErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  routeName: PropTypes.string,
};

export default RouteErrorBoundary;
