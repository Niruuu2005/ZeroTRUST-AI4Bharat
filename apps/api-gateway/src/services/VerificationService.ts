import axios from 'axios';
import { prisma } from '../config/database';
import { logger } from '../utils/logger';
import {
  buildCacheKey, getRedis, setRedis,
  getDynamo, setDynamo, getPgCache,
} from './CacheService';

const VE_URL = process.env.VERIFICATION_ENGINE_URL ?? 'http://localhost:8000';
const MEDIA_URL = process.env.MEDIA_ENGINE_URL ?? 'http://localhost:8001';
const S3_MEDIA_BUCKET = process.env.S3_MEDIA_BUCKET;
const AWS_REGION = process.env.AWS_REGION ?? process.env.AWS_DEFAULT_REGION ?? 'us-east-1';

const MEDIA_TYPES = ['image', 'video', 'audio'];

function inferContentType(type: string, content: string): string {
  const ext = content.includes('.') ? content.split('.').pop()?.toLowerCase() : '';
  if (type === 'image') return ext ? `image/${ext === 'jpg' || ext === 'jpeg' ? 'jpeg' : ext === 'png' ? 'png' : 'gif'}` : 'image/jpeg';
  if (type === 'video') return ext ? `video/${ext === 'mp4' ? 'mp4' : ext === 'webm' ? 'webm' : 'mp4'}` : 'video/mp4';
  if (type === 'audio') return ext ? `audio/${ext === 'mp3' ? 'mpeg' : ext === 'wav' ? 'wav' : 'mpeg'}` : 'audio/mpeg';
  return 'application/octet-stream';
}

function buildMediaUrl(content: string): string {
  if (content.startsWith('s3://') || content.startsWith('http://') || content.startsWith('https://')) return content;
  if (S3_MEDIA_BUCKET) return `https://${S3_MEDIA_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${content}`;
  return content;
}

export class VerificationService {
  async verify(
    content: string,
    type: string,
    source: string,
    userId: string,
  ) {
    const key = buildCacheKey(content, type);

    // ── Tier 1: Redis ────────────────────────────────────────
    const t1 = await getRedis(key);
    if (t1) {
      logger.info('Cache HIT: Redis', { key });
      return { ...t1, cached: true, cache_tier: 'redis' };
    }

    // ── Tier 2: DynamoDB ─────────────────────────────────────
    const t2 = await getDynamo(key);
    if (t2) {
      logger.info('Cache HIT: DynamoDB', { key });
      await setRedis(key, t2, 1800); // promote L2 → L1
      return { ...t2, cached: true, cache_tier: 'dynamodb' };
    }

    // ── Tier 3: PostgreSQL (last 30 days) ────────────────────
    const t3 = await getPgCache(key);
    if (t3) {
      logger.info('Cache HIT: PostgreSQL', { key });
      const result = this.serializeVerification(t3);
      await Promise.allSettled([setRedis(key, result, 1800), setDynamo(key, result)]);
      return { ...result, cached: true, cache_tier: 'cloudfront' };
    }

    // ── Full verification ─────────────────────────────────────
    const useMedia = MEDIA_TYPES.includes(type);
    if (useMedia) {
      logger.info('Cache MISS — invoking media-analysis', { key });
    } else {
      logger.info('Cache MISS — invoking verification engine', { key });
    }
    const result = useMedia
      ? await this.callMediaAnalysis(content, type, userId)
      : await this.callVerificationEngine(content, type, source, userId);

    // Write all tiers (non-blocking)
    await Promise.allSettled([
      setRedis(key, result, 3600),
      setDynamo(key, result),
      prisma.verification.create({
        data: {
          id: result.id ?? undefined,
          claimHash: key,
          claimText: content,
          claimType: type,
          credibilityScore: result.credibility_score,
          category: result.category,
          confidence: result.confidence,
          sourcesConsulted: result.sources_consulted ?? 0,
          agentConsensus: result.agent_consensus ?? null,
          evidenceSummary: result.evidence_summary ?? {},
          sources: result.sources ?? [],
          agentVerdicts: result.agent_verdicts ?? {},
          limitations: result.limitations ?? [],
          recommendation: result.recommendation ?? null,
          processingTime: result.processing_time ?? null,
          cached: false,
          sourcePlatform: source,
          userId: userId !== 'anonymous' ? userId : null,
        },
      }),
    ]);

    return { ...result, cached: false };
  }

  async getById(id: string) {
    return prisma.verification.findUnique({ where: { id } });
  }

  async getHistory(userId: string, page: number, limit: number) {
    const skip = (page - 1) * limit;
    const [items, total] = await Promise.all([
      prisma.verification.findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
        skip, take: limit,
      }),
      prisma.verification.count({ where: { userId } }),
    ]);
    return { items, total, page, limit, pages: Math.ceil(total / limit) };
  }

  private async callVerificationEngine(
    content: string, type: string, source: string, userId: string,
  ): Promise<any> {
    try {
      const { data } = await axios.post(`${VE_URL}/verify`, {
        content, type, source, user_id: userId,
      }, { timeout: 120_000 }); // 2 min — Bedrock multi-agent pipeline can take 30-60s
      return data;
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? err.response?.data?.error ?? err.message ?? err.code ?? 'Unknown error';
      const hint = err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND'
        ? ` (verification-engine not reachable at ${VE_URL})`
        : '';
      throw new Error(String(msg) + hint);
    }
  }

  private async callMediaAnalysis(content: string, type: string, _userId: string): Promise<any> {
    const url = buildMediaUrl(content);
    const contentType = inferContentType(type, content);
    try {
      const { data } = await axios.post(
        `${MEDIA_URL}/analyze`,
        { url, contentType },
        { timeout: 300_000 },
      );
      return data;
    } catch (err: any) {
      const msg = err.response?.data?.detail ?? err.response?.data?.error ?? err.message ?? err.code ?? 'Unknown error';
      const hint = err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND'
        ? ` (media-analysis not reachable at ${MEDIA_URL})`
        : '';
      throw new Error(String(msg) + hint);
    }
  }

  private serializeVerification(row: any) {
    return {
      id: row.id,
      credibility_score: row.credibilityScore,
      category: row.category,
      confidence: row.confidence,
      sources_consulted: row.sourcesConsulted,
      agent_consensus: row.agentConsensus,
      evidence_summary: row.evidenceSummary,
      sources: row.sources,
      agent_verdicts: row.agentVerdicts,
      limitations: row.limitations,
      recommendation: row.recommendation,
      processing_time: row.processingTime,
      created_at: row.createdAt?.toISOString(),
    };
  }
}
