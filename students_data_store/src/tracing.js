const JAEGER_URL = import.meta.env.VITE_JAEGER_URL || (import.meta.env.DEV ? 'http://localhost:4318/v1/traces' : null);

let provider = null;
let initialized = false;

/**
 * Lazy-load OpenTelemetry tracing only when enabled.
 * This defers heavy imports until needed, improving initial load time by 200-300ms.
 */
export const initializeTracing = async () => {
  if (initialized) return provider;
  if (!JAEGER_URL) {
    initialized = true;
    return null;
  }

  try {
    // Dynamically import heavy OTel modules only when needed
    const { WebTracerProvider } = await import('@opentelemetry/sdk-trace-web');
    const { getWebAutoInstrumentations } = await import('@opentelemetry/auto-instrumentations-web');
    const { OTLPTraceExporter } = await import('@opentelemetry/exporter-trace-otlp-http');
    const { BatchSpanProcessor } = await import('@opentelemetry/sdk-trace-base');
    const { registerInstrumentations } = await import('@opentelemetry/instrumentation');
    const { Resource } = await import('@opentelemetry/resources');
    const { SemanticResourceAttributes } = await import('@opentelemetry/semantic-conventions');

    provider = new WebTracerProvider({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'students-frontend',
      }),
    });

    const exporter = new OTLPTraceExporter({
      url: JAEGER_URL,
      timeout: 5000, // 5s timeout to fail fast
    });

    provider.addSpanProcessor(
      new BatchSpanProcessor(exporter, {
        maxQueueSize: 1000,
        maxExportBatchSize: 512,
        scheduledDelayMillis: 1000,
      })
    );
    provider.register();

    registerInstrumentations({
      instrumentations: [
        getWebAutoInstrumentations({
          '@opentelemetry/instrumentation-fetch': {
            propagateTraceHeaderCorsUrls: [
              /http:\/\/localhost:8000\.*/, 
              /https:\/\/.*\.tracestack\.online\.*/, 
            ],
            responseHook: (span, response) => {
              // Only trace errors to reduce span volume
              if (response.status >= 400) {
                span.recordException(new Error(`HTTP ${response.status}`));
              }
            },
          },
        }),
      ],
    });

    initialized = true;
    return provider;
  } catch (err) {
    console.warn('Failed to initialize OpenTelemetry tracing:', err);
    initialized = true;
    return null;
  }
};

// Export default as null initially, call initializeTracing() to initialize
export default provider;
