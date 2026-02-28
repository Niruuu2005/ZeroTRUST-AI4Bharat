import { Router } from 'express';
import { optionalAuth } from '../middleware/auth.middleware';
import { validateBody } from '../middleware/validate.middleware';
import { VerificationService } from '../services/VerificationService';
import { verifyBodySchema } from '../validators';
import { logger } from '../utils/logger';

const router = Router();
const verificationService = new VerificationService();

// POST /api/v1/verify — Main verification endpoint
router.post('/', optionalAuth, validateBody(verifyBodySchema), async (req, res) => {
  const { content, type, source } = req.body;
  const userId = req.user?.sub ?? 'anonymous';

  try {
    const result = await verificationService.verify(content, type, source ?? 'api', userId);
    res.json(result);
  } catch (error: any) {
    logger.error('Verification failed', { error: error.message, userId });
    res.status(500).json({ error: 'Verification failed', message: error.message });
  }
});

// GET /api/v1/verify/:id — Get verification by ID
router.get('/:id', async (req, res) => {
  const { id } = req.params;
  
  try {
    const result = await verificationService.getById(id);
    
    if (!result) {
      res.status(404).json({ error: 'Verification not found' });
      return;
    }
    
    res.json(result);
  } catch (error: any) {
    logger.error('Get verification failed', { error: error.message, id });
    res.status(500).json({ error: 'Failed to retrieve verification' });
  }
});

export { router as verifyRoutes };
