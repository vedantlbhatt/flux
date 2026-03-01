import { createOpenAPI } from 'fumadocs-openapi/server';
import type { Document } from 'fumadocs-openapi';
import fluxOpenAPI from '../../openapi/flux.openapi.json';

const fluxSchema = fluxOpenAPI as unknown as Document;

export const openapi = createOpenAPI({
  input: () => ({
    flux: fluxSchema,
  }),
});
