import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';
import { redis } from '../config/redis';

export interface JWTPayload {
  sub: string;
  email: string;
  tier: 'free' | 'pro' | 'enterprise';
  jti: string;
}

declare global {
  namespace Express {
    interface Request {
      user?: JWTPayload;
    }
  }
}

function extractToken(req: Request): string | null {
  const header = req.headers.authorization;
  if (header?.startsWith('Bearer ')) return header.slice(7);
  return null;
}

async function verifyJWT(token: string): Promise<JWTPayload | null> {
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload;
    const revoked = await redis.exists(`blocked:jti:${payload.jti}`);
    if (revoked) return null;
    return payload;
  } catch {
    return null;
  }
}

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const token = extractToken(req);
  if (!token) {
    res.status(401).json({ error: 'Authentication required' });
    return;
  }
  const payload = await verifyJWT(token);
  if (!payload) {
    res.status(401).json({ error: 'Invalid or expired token' });
    return;
  }
  req.user = payload;
  next();
}

export async function optionalAuth(req: Request, _res: Response, next: NextFunction) {
  const token = extractToken(req);
  if (token) {
    const payload = await verifyJWT(token);
    if (payload) req.user = payload;
  }
  next();
}
