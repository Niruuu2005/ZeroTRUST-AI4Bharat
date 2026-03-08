import { z } from 'zod';

// Schema for UUID parameters (e.g., verification ID)
export const uuidParamSchema = z.object({
  id: z
    .string()
    .uuid('Invalid ID format - must be a valid UUID'),
});

export type UuidParam = z.infer<typeof uuidParamSchema>;
