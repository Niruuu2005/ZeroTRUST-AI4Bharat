import { z } from 'zod';

const claimTypeEnum = z.enum(['text', 'url', 'image', 'video', 'audio']);

// Maximum length constants per requirements 1.5
const MAX_CLAIM_LENGTH = 10000;
const MAX_URL_LENGTH = 500;
const MAX_SOURCE_LENGTH = 64;

// Sanitization function to prevent LLM injection attacks (requirement 1.2)
function sanitizeInput(input: string): string {
  return input
    // Remove or escape special characters that could be used for injection
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
    .replace(/\\/g, '\\\\') // Escape backslashes
    .replace(/`/g, '\\`') // Escape backticks
    .trim();
}

// Custom refinement for claim text validation
const claimTextSchema = z
  .string()
  .min(10, 'Claim text must be at least 10 characters')
  .max(MAX_CLAIM_LENGTH, `Claim text exceeds maximum length of ${MAX_CLAIM_LENGTH} characters`)
  .transform(sanitizeInput);

// Custom refinement for URL validation
const urlSchema = z
  .string()
  .max(MAX_URL_LENGTH, `URL exceeds maximum length of ${MAX_URL_LENGTH} characters`)
  .url('Invalid URL format')
  .transform(sanitizeInput);

// Main verification body schema with conditional validation based on type
export const verifyBodySchema = z.object({
  content: z.string(),
  type: claimTypeEnum,
  source: z.string().max(MAX_SOURCE_LENGTH).optional(),
}).superRefine((data, ctx) => {
  // Apply different validation rules based on type (requirement 1.1, 1.5)
  if (data.type === 'text') {
    const result = claimTextSchema.safeParse(data.content);
    if (!result.success) {
      result.error.issues.forEach(issue => {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['content'],
          message: issue.message,
        });
      });
    } else {
      data.content = result.data;
    }
  } else if (data.type === 'url') {
    const result = urlSchema.safeParse(data.content);
    if (!result.success) {
      result.error.issues.forEach(issue => {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['content'],
          message: issue.message,
        });
      });
    } else {
      data.content = result.data;
    }
  } else {
    // For media types (image, video, audio), validate as URL
    const result = urlSchema.safeParse(data.content);
    if (!result.success) {
      result.error.issues.forEach(issue => {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['content'],
          message: issue.message,
        });
      });
    } else {
      data.content = result.data;
    }
  }
  
  // Sanitize source if provided
  if (data.source) {
    data.source = sanitizeInput(data.source);
  }
});

export type VerifyBody = z.infer<typeof verifyBodySchema>;

// Export sanitization function for use in other validators
export { sanitizeInput };
