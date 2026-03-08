import { Router } from 'express';
import { PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { v4 as uuidv4 } from 'uuid';
import { validateBody } from '../middleware/validate.middleware';
import { presignBodySchema } from '../validators';
import { logger } from '../utils/logger';

const router = Router();

const BUCKET = process.env.S3_MEDIA_BUCKET;
const REGION = process.env.AWS_REGION ?? process.env.AWS_DEFAULT_REGION ?? 'us-east-1';
const PRESIGN_EXPIRES_IN = 900; // 15 minutes

// POST /api/v1/media/presign — Get presigned URL for S3 upload (Diagram 4)
router.post('/presign', validateBody(presignBodySchema), async (req, res) => {
  if (!BUCKET) {
    res.status(503).json({
      error: 'Media upload not configured',
      message: 'Set S3_MEDIA_BUCKET and AWS credentials to enable presigned uploads.',
    });
    return;
  }

  const { contentType, extension, key: providedKey } = req.body;
  const ext = extension ?? contentType.split('/').pop()?.replace(/^x-/, '') ?? 'bin';
  const key = providedKey ?? `uploads/${uuidv4()}.${ext}`;

  try {
    const client = new S3Client({ region: REGION });
    const command = new PutObjectCommand({
      Bucket: BUCKET,
      Key: key,
      ContentType: contentType,
    });
    const uploadUrl = await getSignedUrl(client, command, { expiresIn: PRESIGN_EXPIRES_IN });
    logger.info('Presign issued', { key, contentType });
    res.json({
      uploadUrl,
      key,
      expiresIn: PRESIGN_EXPIRES_IN,
    });
  } catch (error: any) {
    logger.error('Presign failed', { error: error.message, key });
    res.status(500).json({ error: 'Failed to generate upload URL', message: error.message });
  }
});

export { router as mediaRoutes };
