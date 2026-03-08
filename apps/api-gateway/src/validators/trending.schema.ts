import { z } from 'zod';

const MIN_LIMIT = 1;
const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 20;
const MIN_DAYS = 1;
const MAX_DAYS = 90;
const DEFAULT_DAYS = 7;

// Schema for trending query parameters
export const trendingQuerySchema = z.object({
  limit: z
    .string()
    .optional()
    .transform(val => val ? parseInt(val, 10) : DEFAULT_LIMIT)
    .refine(val => !isNaN(val) && val >= MIN_LIMIT && val <= MAX_LIMIT, {
      message: `Limit must be a number between ${MIN_LIMIT} and ${MAX_LIMIT}`,
    }),
  days: z
    .string()
    .optional()
    .transform(val => val ? parseInt(val, 10) : DEFAULT_DAYS)
    .refine(val => !isNaN(val) && val >= MIN_DAYS && val <= MAX_DAYS, {
      message: `Days must be a number between ${MIN_DAYS} and ${MAX_DAYS}`,
    }),
});

export type TrendingQuery = z.infer<typeof trendingQuerySchema>;
