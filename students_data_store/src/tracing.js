import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { registerInstrumentations } from '@opentelemetry/instrumentation';

import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const JAEGER_URL = import.meta.env.VITE_JAEGER_URL || (import.meta.env.DEV ? 'http://localhost:4318/v1/traces' : null);

let provider = null;

if (JAEGER_URL) {
  provider = new WebTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'students-frontend',
    }),
  });

  const exporter = new OTLPTraceExporter({
    url: JAEGER_URL,
  });

  provider.addSpanProcessor(new BatchSpanProcessor(exporter));
  provider.register();

  registerInstrumentations({
    instrumentations: [
      getWebAutoInstrumentations({
        '@opentelemetry/instrumentation-fetch': {
          propagateTraceHeaderCorsUrls: [
            /http:\/\/localhost:8000\.*/, 
            /https:\/\/.*\.tracestack\.online\.*/
          ],
        },
      }),
    ],
  });
}

export default provider;
