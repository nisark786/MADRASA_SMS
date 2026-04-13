import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * Optimized Image Component with Lazy Loading
 * 
 * Features:
 * - Lazy loading with Intersection Observer
 * - Placeholder support
 * - Error handling with fallback
 * - Responsive sizing
 * - Tracks loading state
 */
function OptimizedImage({ 
  src, 
  alt, 
  placeholder = null,
  fallback = null,
  width,
  height,
  className = '',
  onLoad,
  onError,
  ...props 
}) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [imageSrc, setImageSrc] = useState(placeholder || null);
  const imgRef = useRef(null);

  useEffect(() => {
    // Check if Intersection Observer is supported
    if (!('IntersectionObserver' in window)) {
      // Fallback for unsupported browsers
      setImageSrc(src);
      return;
    }

    // Create intersection observer for lazy loading
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setImageSrc(src);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        root: null,
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01,
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current);
      }
    };
  }, [src]);

  const handleLoad = () => {
    setIsLoaded(true);
    if (onLoad) onLoad();
  };

  const handleError = () => {
    setIsError(true);
    setImageSrc(fallback || null);
    if (onError) onError();
  };

  return (
    <div
      className={`relative overflow-hidden bg-gray-200 ${className}`}
      style={{
        aspectRatio: width && height ? `${width}/${height}` : 'auto',
      }}
    >
      {/* Placeholder while loading */}
      {!isLoaded && imageSrc && (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-200 to-gray-300 animate-pulse" />
      )}

      {/* Main image */}
      {imageSrc && !isError && (
        <img
          ref={imgRef}
          src={imageSrc}
          alt={alt}
          width={width}
          height={height}
          loading="lazy"
          decoding="async"
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={handleLoad}
          onError={handleError}
          {...props}
        />
      )}

      {/* Error fallback */}
      {isError && fallback === null && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <span className="text-gray-400 text-sm">Image not available</span>
        </div>
      )}

      {/* Fallback image */}
      {isError && fallback && (
        <img
          src={fallback}
          alt={alt}
          width={width}
          height={height}
          className="w-full h-full object-cover"
          {...props}
        />
      )}
    </div>
  );
}

OptimizedImage.propTypes = {
  src: PropTypes.string.isRequired,
  alt: PropTypes.string.isRequired,
  placeholder: PropTypes.string,
  fallback: PropTypes.string,
  width: PropTypes.number,
  height: PropTypes.number,
  className: PropTypes.string,
  onLoad: PropTypes.func,
  onError: PropTypes.func,
};

export default OptimizedImage;
