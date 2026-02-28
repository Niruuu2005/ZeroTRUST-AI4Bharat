import { z } from 'zod';

const claimTypeEnum = z.enum(['text', 'url', 'image', 'video', 'audio']);

export const verifyBodySchema = z.object({
  content: z
    .string()
    .min(10, 'content must be at least 10 characters')
    .max(10000, 'content must be at most 10000 characters'),
  type: claimTypeEnum,
  source: z.string().max(64).optional(),
});

export type VerifyBody = z.infer<typeof verifyBodySchema>;
