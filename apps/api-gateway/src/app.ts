import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import 'express-async-errors';
import { verifyRoutes } from './routes/verify.routes';
import { authRoutes } from './routes/auth.routes';
import { historyRoutes } from './routes/history.routes';
import { mediaRoutes } from './routes/media.routes';
import { trendingRoutes } from './routes/trending.routes';
import { errorMiddleware } from './middleware/error.middleware';
import { logger } from './utils/logger';

const app = express();

app.set('trust proxy', 1);

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
    }
  }
}));

const ALLOWED_ORIGINS = [
  'https://zerotrust.ai',
  'http://localhost:5173',
  'http://localhost:3001',
];
app.use(cors({
  origin: (origin, cb) => {
    if (!origin) return cb(null, true); // server-to-server
    const ok = ALLOWED_ORIGINS.includes(origin) || /^chrome-extension:\/\//.test(origin);
    cb(ok ? null : new Error('CORS'), ok);
  },
  credentials: true,
}));

app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logger
app.use((req, _res, next) => {
  logger.info(`${req.method} ${req.path}`, { ip: req.ip, ua: req.headers['user-agent']?.slice(0, 80) });
  next();
});

// Routes
app.get('/health', (_req, res) => {
  res.json({ status: 'healthy', service: 'api-gateway', time: new Date().toISOString() });
});

app.use('/api/v1/verify', verifyRoutes);
app.use('/api/v1/auth', authRoutes);
app.use('/api/v1/history', historyRoutes);
app.use('/api/v1/media', mediaRoutes);
app.use('/api/v1/trending', trendingRoutes);

// 404
app.use((_req, res) => res.status(404).json({ error: 'Route not found' }));

// Error handler
app.use(errorMiddleware);

export default app;
