import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.middleware';
import { validateQuery } from '../middleware/validate.middleware';
import { historyQuerySchema } from '../validators';
import { VerificationService } from '../services/VerificationService';
import { logger } from '../utils/logger';

const router = Router();
const verificationService = new VerificationService();

// GET /api/v1/history — Get user's verification history
router.get('/', authMiddleware, validateQuery(historyQuerySchema), async (req, res) => {
  const userId = req.user!.sub;
  const { page, limit } = req.query as any;
  
  try {
    const result = await verificationService.getHistory(userId, page, limit);
    res.json(result);
  } catch (error: any) {
    logger.error('Get history failed', { error: error.message, userId });
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

export { router as historyRoutes };
