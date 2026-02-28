import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.middleware';
import { VerificationService } from '../services/VerificationService';
import { logger } from '../utils/logger';

const router = Router();
const verificationService = new VerificationService();

// GET /api/v1/history — Get user's verification history
router.get('/', authMiddleware, async (req, res) => {
  const userId = req.user!.sub;
  const page = parseInt(req.query.page as string) || 1;
  const limit = parseInt(req.query.limit as string) || 20;
  
  // Validate pagination
  if (page < 1 || limit < 1 || limit > 100) {
    res.status(400).json({ error: 'Invalid pagination parameters' });
    return;
  }
  
  try {
    const result = await verificationService.getHistory(userId, page, limit);
    res.json(result);
  } catch (error: any) {
    logger.error('Get history failed', { error: error.message, userId });
    res.status(500).json({ error: 'Failed to retrieve history' });
  }
});

export { router as historyRoutes };
