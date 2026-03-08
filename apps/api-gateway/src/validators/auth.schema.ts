import { z } from 'zod';
import { sanitizeInput } from './verify.schema';

const MAX_EMAIL_LENGTH = 255;
const MAX_PASSWORD_LENGTH = 128;

const emailSchema = z
  .string()
  .email('Invalid email format')
  .max(MAX_EMAIL_LENGTH, `Email exceeds maximum length of ${MAX_EMAIL_LENGTH} characters`)
  .transform(sanitizeInput);

export const registerBodySchema = z.object({
  email: emailSchema,
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .max(MAX_PASSWORD_LENGTH, `Password exceeds maximum length of ${MAX_PASSWORD_LENGTH} characters`),
});

export const loginBodySchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'Password is required'),
});

export const refreshBodySchema = z.object({
  refreshToken: z.string().min(1, 'refreshToken is required').transform(sanitizeInput),
});

export type RegisterBody = z.infer<typeof registerBodySchema>;
export type LoginBody = z.infer<typeof loginBodySchema>;
export type RefreshBody = z.infer<typeof refreshBodySchema>;
