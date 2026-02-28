import winston from 'winston';
import { createCloudWatchTransport } from './cloudwatch-transport';

const level = process.env.NODE_ENV === 'production' ? 'info' : 'debug';

const transports: winston.transport[] = [
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    ),
  }),
];

const cw = createCloudWatchTransport();
if (cw) transports.push(cw);

export const logger = winston.createLogger({
  level,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports,
});
