import { z } from 'zod';

const MIN_PAGE = 1;
const MIN_LIMIT = 1;
const MAX_LIMIT = 100; // Per requirement 13.5
const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 50; // Per requirement 13.1

// Schema for history query parameters with pagination
export const historyQuerySchema = z.object({
  page: z
    .string()
    .optional()
    .transform(val => val ? parseInt(val, 10) : DEFAULT_PAGE)
    .refine(val => !isNaN(val) && val >= MIN_PAGE, {
      message: `Page must be a number greater than or equal to ${MIN_PAGE}`,
    }),
  limit: z
    .string()
    .optional()
    .transform(val => val ? parseInt(val, 10) : DEFAULT_LIMIT)
    .refine(val => !isNaN(val) && val >= MIN_LIMIT && val <= MAX_LIMIT, {
      message: `Limit must be a number between ${MIN_LIMIT} and ${MAX_LIMIT}`,
    }),
});

export type HistoryQuery = z.infer<typeof historyQuerySchema>;
