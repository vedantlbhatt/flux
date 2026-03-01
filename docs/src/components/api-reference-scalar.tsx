'use client';

import { ApiReferenceReact } from '@scalar/api-reference-react';
import '@scalar/api-reference-react/style.css';

const apiBaseUrl =
  typeof import.meta !== 'undefined' && import.meta.env?.VITE_FLUX_API_URL
    ? String(import.meta.env.VITE_FLUX_API_URL).replace(/\/$/, '')
    : 'http://localhost:8000';

const specUrl = `${apiBaseUrl}/openapi.json`;

/** Sandbox environments: users can switch and try the API against different bases (e.g. local vs deployed). */
const servers = [
  { url: apiBaseUrl, description: 'Local' },
  { url: 'https://api.flux.example', description: 'Production (example)' },
];

/**
 * Interactive OpenAPI reference powered by Scalar.
 * - Try-it-out (sandbox) for every endpoint
 * - Environment switcher in the UI (Local / Production) for interactive calls
 * - Same idea as https://www.fumadocs.dev/docs/openapi (Scalar Galaxy)
 */
export function ApiReferenceScalar() {
  return (
    <div className="fdocs-api-reference not-prose min-h-[80vh] w-full rounded-lg border border-[var(--fdocs-border)] bg-[var(--fdocs-background)]">
      <ApiReferenceReact
        configuration={{
          url: specUrl,
          theme: 'default',
          layout: 'modern',
          darkMode: true,
          hideSidebar: false,
          hideModels: false,
          hideDownloadButton: false,
          withDefaultCredentials: false,
          servers,
        }}
      />
    </div>
  );
}
