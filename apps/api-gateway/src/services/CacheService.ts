import crypto from 'crypto';
import { redis } from '../config/redis';
import { prisma } from '../config/database';
import { logger } from '../utils/logger';

// AWS SDK is optional for local dev — DynamoDB calls are gracefully skipped if unavailable
let dynamo: any = null;
let marshall: any = null;
let unmarshall: any = null;

async function loadDynamo() {
  try {
    const sdk = await import('@aws-sdk/client-dynamodb');
    const util = await import('@aws-sdk/util-dynamodb');
    dynamo = new sdk.DynamoDBClient({ region: process.env.AWS_REGION ?? 'us-east-1' });
    marshall = util.marshall;
    unmarshall = util.unmarshall;
  } catch {
    logger.warn('DynamoDB SDK not available — Tier 2 cache disabled');
  }
}
loadDynamo();

const DYNAMO_TABLE = 'zerotrust-claim-verifications';
const REDIS_TTL = 3600;          // 1 hour  (Tier 1)
const DYNAMO_TTL = 86400;        // 24 hours (Tier 2)
const PG_CACHE_WINDOW_MS = 30 * 24 * 60 * 60 * 1000; // 30 days (Tier 3 / CloudFront equivalent)

const STOP_WORDS = new Set([
  'a','an','the','is','are','was','were','be','been','being',
  'have','has','had','do','does','did','will','would','could',
  'should','may','might','shall','can','of','in','at','by','for',
  'with','about','as','from','that','this','it','its','to','and','or',
]);

export function buildCacheKey(content: string, type: string): string {
  const normalized = content
    .toLowerCase()
    .trim()
    .replace(/<[^>]+>/g, '')
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .split(' ')
    .filter(w => w.length > 0 && !STOP_WORDS.has(w))
    .sort()
    .join(' ');
  return crypto
    .createHash('sha256')
    .update(`${normalized}:${type}`)
    .digest('hex')
    .slice(0, 32);
}

// ── Tier 1: Redis ───────────────────────────────────────────────────
export async function getRedis(key: string): Promise<any | null> {
  try {
    const val = await redis.get(`verify:${key}`);
    return val ? JSON.parse(val) : null;
  } catch (err: any) {
    logger.warn('Redis GET failed', { key, error: err.message });
    return null;
  }
}

export async function setRedis(key: string, value: any, ttlSeconds = REDIS_TTL): Promise<void> {
  try {
    await redis.setex(`verify:${key}`, ttlSeconds, JSON.stringify(value));
  } catch (err: any) {
    logger.warn('Redis SET failed', { key, error: err.message });
  }
}

// ── Tier 2: DynamoDB ────────────────────────────────────────────────
export async function getDynamo(key: string): Promise<any | null> {
  if (!dynamo) return null;
  try {
    const { GetItemCommand } = await import('@aws-sdk/client-dynamodb');
    const result = await dynamo.send(new GetItemCommand({
      TableName: DYNAMO_TABLE,
      Key: marshall({ claim_hash: key }),
    }));
    if (!result.Item) return null;
    const item = unmarshall(result.Item);
    if (item.ttl < Math.floor(Date.now() / 1000)) return null;
    return JSON.parse(item.result_json);
  } catch (err: any) {
    logger.warn('DynamoDB GET failed', { key, error: err.message });
    return null;
  }
}

export async function setDynamo(key: string, value: any): Promise<void> {
  if (!dynamo) return;
  try {
    const { PutItemCommand } = await import('@aws-sdk/client-dynamodb');
    await dynamo.send(new PutItemCommand({
      TableName: DYNAMO_TABLE,
      Item: marshall({
        claim_hash: key,
        created_at: new Date().toISOString(),
        result_json: JSON.stringify(value),
        ttl: Math.floor(Date.now() / 1000) + DYNAMO_TTL,
      }),
    }));
  } catch (err: any) {
    logger.warn('DynamoDB PUT failed', { key, error: err.message });
  }
}

// ── Tier 3: PostgreSQL (last 30 days — CloudFront proxy) ────────────
export async function getPgCache(key: string): Promise<any | null> {
  try {
    return await prisma.verification.findFirst({
      where: {
        claimHash: key,
        createdAt: { gte: new Date(Date.now() - PG_CACHE_WINDOW_MS) },
      },
      orderBy: { createdAt: 'desc' },
    });
  } catch (err: any) {
    logger.warn('PG cache GET failed', { key, error: err.message });
    return null;
  }
}
