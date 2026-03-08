import { z } from 'zod';
import { sanitizeInput } from './verify.schema';

const MAX_CONTENT_TYPE_LENGTH = 128;
const MAX_EXTENSION_LENGTH = 16;
const MAX_KEY_LENGTH = 512;

// Schema for presigned URL request
export const presignBodySchema = z.object({
  contentType: z
    .string()
    .min(1, 'Content type is required')
    .max(MAX_CONTENT_TYPE_LENGTH, `Content type exceeds maximum length of ${MAX_CONTENT_TYPE_LENGTH} characters`)
    .regex(/^[a-zA-Z0-9\-\/]+$/, 'Invalid content type format')
    .transform(sanitizeInput),
  extension: z
    .string()
    .max(MAX_EXTENSION_LENGTH, `Extension exceeds maximum length of ${MAX_EXTENSION_LENGTH} characters`)
    .regex(/^[a-zA-Z0-9]+$/, 'Extension must contain only alphanumeric characters')
    .optional()
    .transform(val => val ? sanitizeInput(val) : val),
  key: z
    .string()
    .max(MAX_KEY_LENGTH, `Key exceeds maximum length of ${MAX_KEY_LENGTH} characters`)
    .regex(/^[a-zA-Z0-9\-_\/\.]+$/, 'Key contains invalid characters')
    .optional()
    .transform(val => val ? sanitizeInput(val) : val),
});

export type PresignBody = z.infer<typeof presignBodySchema>;
