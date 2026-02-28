import { rateLimit } from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';
import { redis } from '../config/redis';
import { Request, Response } from 'express';

export const publicRateLimit = rateLimit({
  store: new RedisStore({
    // @ts-expect-error - RedisStore types are not perfect
    sendCommand: (...args: string[]) => redis.call(...args),
    prefix: 'rl:pub:',
  }),
  windowMs: 60 * 1000, // 1 minute
  max: parseInt(process.env.RATE_LIMIT_PUBLIC ?? '20'),
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_req: Request, res: Response) => {
    res.status(429).json({
      error: 'Rate limit exceeded. Try again in 60 seconds.',
    });
  },
});

const TIER_DAILY_LIMITS = {
  free: 100,
  pro: 5000,
  enterprise: 999999,
};

export function userRateLimit(req: any, res: any, next: any) {
  const tier = (req.user?.tier ?? 'free') as keyof typeof TIER_DAILY_LIMITS;
  
  return rateLimit({
    store: new RedisStore({
      // @ts-expect-error - RedisStore types
      sendCommand: (...args: string[]) => redis.call(...args),
      prefix: `rl:${req.user?.id ?? 'anon'}:`,
    }),
    windowMs: 24 * 60 * 60 * 1000, // 24 hours
    max: TIER_DAILY_LIMITS[tier],
    handler: (_req: Request, res: Response) => {
      res.status(429).json({
        error: `Daily limit of ${TIER_DAILY_LIMITS[tier]} requests reached`,
      });
    },
  })(req, res, next);
}
