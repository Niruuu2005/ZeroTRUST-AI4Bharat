import { Request, Response, NextFunction } from 'express';
import { z, ZodSchema, ZodTypeAny } from 'zod';
import { logger } from '../utils/logger';

/**
 * Validation middleware that validates request body against a Zod schema
 * Returns 400 with descriptive errors on validation failure (requirement 1.4)
 * Does not expose internal system details in error messages
 */
export function validateBody<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    
    if (result.success) {
      // Replace body with validated and sanitized data
      req.body = result.data;
      next();
      return;
    }
    
    const zodError = result.error as z.ZodError;
    
    // Log validation failure with correlation ID for debugging
    const correlationId = req.headers['x-correlation-id'] as string || 'unknown';
    logger.warn('Input validation failed', {
      correlationId,
      path: req.path,
      errors: zodError.errors,
    });
    
    // Format errors in a user-friendly way without exposing internal details
    const formattedErrors = zodError.errors.map(err => ({
      field: err.path.join('.'),
      message: err.message,
    }));
    
    res.status(400).json({
      error: 'Validation failed',
      message: 'The request contains invalid or malformed data',
      details: formattedErrors,
    });
  };
}

/**
 * Validation middleware for query parameters
 */
export function validateQuery<T extends ZodTypeAny>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.query);
    
    if (result.success) {
      req.query = result.data as any;
      next();
      return;
    }
    
    const zodError = result.error as z.ZodError;
    
    const correlationId = req.headers['x-correlation-id'] as string || 'unknown';
    logger.warn('Query validation failed', {
      correlationId,
      path: req.path,
      errors: zodError.errors,
    });
    
    const formattedErrors = zodError.errors.map(err => ({
      field: err.path.join('.'),
      message: err.message,
    }));
    
    res.status(400).json({
      error: 'Validation failed',
      message: 'The request contains invalid query parameters',
      details: formattedErrors,
    });
  };
}

/**
 * Validation middleware for URL parameters
 */
export function validateParams<T extends ZodTypeAny>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.params);
    
    if (result.success) {
      req.params = result.data as any;
      next();
      return;
    }
    
    const zodError = result.error as z.ZodError;
    
    const correlationId = req.headers['x-correlation-id'] as string || 'unknown';
    logger.warn('Params validation failed', {
      correlationId,
      path: req.path,
      errors: zodError.errors,
    });
    
    const formattedErrors = zodError.errors.map(err => ({
      field: err.path.join('.'),
      message: err.message,
    }));
    
    res.status(400).json({
      error: 'Validation failed',
      message: 'The request contains invalid URL parameters',
      details: formattedErrors,
    });
  };
}
