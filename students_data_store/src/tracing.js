import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { registerInstrumentations } from '@opentelemetry/instrumentation';

import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const provider = new WebTracerProvider({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'students-frontend',
  }),
});

// Configure the exporter to send traces to Jaeger (OTLP HTTP port 4318)
const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces',
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));

provider.register();

// Register automatic instrumentations (Fetch, XHR, User Interactions)
registerInstrumentations({
  instrumentations: [
    getWebAutoInstrumentations({
      // load custom configuration for instrumentations
      '@opentelemetry/instrumentation-fetch': {
        propagateTraceHeaderCorsUrls: [
          /http:\/\/localhost:8000\.*/, // Propagate traces to our backend
        ],
      },
    }),
  ],
});

export default provider;
