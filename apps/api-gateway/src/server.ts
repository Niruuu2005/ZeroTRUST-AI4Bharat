import path from 'path';
import { config as loadEnv } from 'dotenv';

// Load .env.local from repo root when running from apps/api-gateway/src
const rootDir = path.resolve(__dirname, '../../..');
loadEnv({ path: path.join(rootDir, '.env.local') });
loadEnv({ path: path.join(rootDir, '.env') });
loadEnv(); // app-level .env

import app from './app';
import { logger } from './utils/logger';
import { redis } from './config/redis';
import { prisma } from './config/database';

const PORT = parseInt(process.env.PORT ?? '3000', 10);

async function main() {
  // Verify DB connection
  await prisma.$connect();
  logger.info('PostgreSQL connected');

  // Verify Redis connection
  await redis.ping();
  logger.info('Redis connected');

  const server = app.listen(PORT, () => {
    logger.info(`API Gateway running on port ${PORT} [${process.env.NODE_ENV}]`);
  });

  // Graceful shutdown
  const shutdown = async (signal: string) => {
    logger.info(`${signal} received — shutting down`);
    server.close(async () => {
      await prisma.$disconnect();
      await redis.quit();
      logger.info('Graceful shutdown complete');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

main().catch(err => {
  logger.error('Startup error', { error: err.message });
  process.exit(1);
});
