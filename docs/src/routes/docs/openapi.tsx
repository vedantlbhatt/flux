import { createFileRoute } from '@tanstack/react-router';
import { createServerFn } from '@tanstack/react-start';
import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { DocsBody, DocsPage, DocsTitle } from 'fumadocs-ui/layouts/docs/page';
import { source } from '@/lib/source';
import { baseOptions } from '@/lib/layout.shared';
import { ApiReferenceScalar } from '@/components/api-reference-scalar';
import { Suspense } from 'react';

const getDocsLayoutData = createServerFn({ method: 'GET' }).handler(async () => {
  const pageTree = await source.serializePageTree(source.getPageTree());
  return { pageTree };
});

export const Route = createFileRoute('/docs/openapi')({
  component: OpenApiPage,
  loader: async () => {
    const { pageTree } = await getDocsLayoutData();
    return { pageTree };
  },
});

function OpenApiPage() {
  const { pageTree } = Route.useLoaderData();

  return (
    <DocsLayout {...baseOptions()} tree={pageTree}>
      <Suspense fallback={<div className="p-8">Loading API reference…</div>}>
        <DocsPage full>
          <DocsTitle>API Reference</DocsTitle>
          <DocsBody>
            <p className="mb-6 text-[var(--fdocs-muted-foreground)]">
              Interactive OpenAPI reference with try-it-out and optional
              environment switching. Powered by{' '}
              <a
                href="https://scalar.com"
                target="_blank"
                rel="noreferrer"
                className="underline"
              >
                Scalar
              </a>
              .
            </p>
            <ApiReferenceScalar />
          </DocsBody>
        </DocsPage>
      </Suspense>
    </DocsLayout>
  );
}
