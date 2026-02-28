import { Router } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { prisma } from '../config/database';
import { redis } from '../config/redis';
import { authMiddleware } from '../middleware/auth.middleware';
import { validateBody } from '../middleware/validate.middleware';
import { registerBodySchema, loginBodySchema, refreshBodySchema } from '../validators';
import { logger } from '../utils/logger';

const router = Router();

const JWT_SECRET = process.env.JWT_SECRET!;
const JWT_ACCESS_EXPIRY = process.env.JWT_ACCESS_EXPIRY ?? '15m';
const JWT_REFRESH_EXPIRY = process.env.JWT_REFRESH_EXPIRY ?? '7d';

// POST /api/v1/auth/register
router.post('/register', validateBody(registerBodySchema), async (req, res) => {
  const { email, password } = req.body;

  try {
    // Check if user exists
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
      res.status(409).json({ error: 'Email already registered' });
      return;
    }
    
    // Hash password
    const passwordHash = await bcrypt.hash(password, 12);
    
    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        subscriptionTier: 'free',
      },
    });
    
    logger.info('User registered', { userId: user.id, email });
    
    res.status(201).json({
      message: 'Registration successful',
      user: {
        id: user.id,
        email: user.email,
        tier: user.subscriptionTier,
      },
    });
  } catch (error: any) {
    logger.error('Registration failed', { error: error.message, email });
    res.status(500).json({ error: 'Registration failed' });
  }
});

// POST /api/v1/auth/login
router.post('/login', validateBody(loginBodySchema), async (req, res) => {
  const { email, password } = req.body;

  try {
    // Find user
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user || !user.passwordHash) {
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }
    
    // Verify password
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
      res.status(401).json({ error: 'Invalid credentials' });
      return;
    }
    
    // Generate tokens
    const jti = uuidv4();
    const accessToken = jwt.sign(
      { sub: user.id, email: user.email, tier: user.subscriptionTier, jti },
      JWT_SECRET,
      { expiresIn: JWT_ACCESS_EXPIRY } as jwt.SignOptions
    );
    
    const refreshToken = jwt.sign(
      { sub: user.id, jti },
      JWT_SECRET,
      { expiresIn: JWT_REFRESH_EXPIRY } as jwt.SignOptions
    );
    
    logger.info('User logged in', { userId: user.id, email });
    
    res.json({
      accessToken,
      refreshToken,
      user: {
        id: user.id,
        email: user.email,
        tier: user.subscriptionTier,
      },
    });
  } catch (error: any) {
    logger.error('Login failed', { error: error.message, email });
    res.status(500).json({ error: 'Login failed' });
  }
});

// POST /api/v1/auth/refresh
router.post('/refresh', validateBody(refreshBodySchema), async (req, res) => {
  const { refreshToken } = req.body;

  try {
    const payload = jwt.verify(refreshToken, JWT_SECRET) as any;
    
    // Check if token is revoked
    const revoked = await redis.exists(`blocked:jti:${payload.jti}`);
    if (revoked) {
      res.status(401).json({ error: 'Token revoked' });
      return;
    }
    
    // Get user
    const user = await prisma.user.findUnique({ where: { id: payload.sub } });
    if (!user) {
      res.status(401).json({ error: 'User not found' });
      return;
    }
    
    // Generate new access token
    const newJti = uuidv4();
    const accessToken = jwt.sign(
      { sub: user.id, email: user.email, tier: user.subscriptionTier, jti: newJti },
      JWT_SECRET,
      { expiresIn: JWT_ACCESS_EXPIRY } as jwt.SignOptions
    );
    
    res.json({ accessToken });
  } catch (error: any) {
    logger.error('Token refresh failed', { error: error.message });
    res.status(401).json({ error: 'Invalid or expired refresh token' });
  }
});

// POST /api/v1/auth/logout
router.post('/logout', authMiddleware, async (req, res) => {
  const jti = req.user!.jti;
  
  try {
    // Revoke token by adding JTI to blocklist
    // TTL should match token expiry (15 minutes for access token)
    await redis.setex(`blocked:jti:${jti}`, 900, '1');
    
    logger.info('User logged out', { userId: req.user!.sub });
    
    res.json({ message: 'Logout successful' });
  } catch (error: any) {
    logger.error('Logout failed', { error: error.message });
    res.status(500).json({ error: 'Logout failed' });
  }
});

export { router as authRoutes };
