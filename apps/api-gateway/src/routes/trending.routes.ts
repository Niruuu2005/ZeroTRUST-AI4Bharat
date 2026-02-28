import { Router } from 'express';
import { Prisma } from '@prisma/client';
import { prisma } from '../config/database';
import { logger } from '../utils/logger';

const router = Router();

const DEFAULT_LIMIT = 20;
const DEFAULT_DAYS = 7;
const MAX_LIMIT = 100;

type TrendingRow = {
  claimHash: string;
  claimText: string;
  count: bigint;
  lastSeen: Date;
  sampleId: string | null;
  category: string | null;
  credibilityScore: number | null;
};

// GET /api/v1/trending — Trending claims by verification count (Diagram 2: Trending Fake News)
router.get('/', async (req, res) => {
  const limit = Math.min(
    parseInt(req.query.limit as string, 10) || DEFAULT_LIMIT,
    MAX_LIMIT
  );
  const days = Math.min(Math.max(parseInt(req.query.days as string, 10) || DEFAULT_DAYS, 1), 90);

  try {
    const since = new Date();
    since.setDate(since.getDate() - days);

    const raw = await prisma.$queryRaw<TrendingRow[]>(
      Prisma.sql`
      SELECT v."claimHash", v."claimText",
             COUNT(*)::bigint AS "count",
             MAX(v."createdAt") AS "lastSeen",
             (array_agg(v.id ORDER BY v."createdAt" DESC))[1] AS "sampleId",
             (array_agg(v.category ORDER BY v."createdAt" DESC))[1] AS "category",
             (array_agg(v."credibilityScore" ORDER BY v."createdAt" DESC))[1] AS "credibilityScore"
      FROM verifications v
      WHERE v."createdAt" >= ${since}
      GROUP BY v."claimHash", v."claimText"
      ORDER BY COUNT(*) DESC
      LIMIT ${limit}
    `
    );

    const items = raw.map((row) => ({
      claimHash: row.claimHash,
      claimText: row.claimText,
      count: Number(row.count),
      lastSeen: row.lastSeen,
      sampleVerificationId: row.sampleId ?? undefined,
      category: row.category ?? undefined,
      credibilityScore: row.credibilityScore ?? undefined,
    }));

    res.json({
      items,
      windowDays: days,
      limit,
    });
  } catch (error: any) {
    logger.error('Trending failed', { error: error.message });
    res.status(500).json({ error: 'Failed to retrieve trending claims' });
  }
});

export { router as trendingRoutes };
