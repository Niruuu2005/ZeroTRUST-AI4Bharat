import { Request, Response, NextFunction } from 'express';
import { z, ZodSchema } from 'zod';

export function validateBody<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (result.success) {
      req.body = result.data;
      next();
      return;
    }
    const zodError = result.error as z.ZodError;
    res.status(400).json({
      error: 'Validation failed',
      details: zodError.flatten(),
    });
  };
}
