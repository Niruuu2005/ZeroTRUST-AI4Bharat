/**
 * Optional Winston transport for AWS CloudWatch Logs.
 * Only used when CW_LOG_GROUP is set. Does not block local dev.
 */
import Transport from 'winston-transport';
import {
  CloudWatchLogsClient,
  CreateLogStreamCommand,
  PutLogEventsCommand,
} from '@aws-sdk/client-cloudwatch-logs';

const LOG_GROUP = process.env.CW_LOG_GROUP;
const LOG_STREAM_PREFIX = process.env.CW_LOG_STREAM_PREFIX ?? 'api-gateway';
const REGION = process.env.AWS_REGION ?? process.env.AWS_DEFAULT_REGION ?? 'us-east-1';

let nextSequenceToken: string | undefined;
let currentStreamName: string | null = null;

function getStreamName(): string {
  const date = new Date().toISOString().slice(0, 10);
  return `${LOG_STREAM_PREFIX}-${date}`;
}

async function ensureStream(client: CloudWatchLogsClient, streamName: string): Promise<void> {
  if (currentStreamName === streamName) return;
  currentStreamName = streamName;
  nextSequenceToken = undefined;
  try {
    await client.send(
      new CreateLogStreamCommand({
        logGroupName: LOG_GROUP!,
        logStreamName: streamName,
      })
    );
  } catch (e: any) {
    if (e?.name !== 'ResourceAlreadyExistsException') {
      throw e;
    }
  }
}

async function sendToCloudWatch(log: string, timestamp: number): Promise<void> {
  if (!LOG_GROUP) return;
  const client = new CloudWatchLogsClient({ region: REGION });
  const streamName = getStreamName();

  try {
    await ensureStream(client, streamName);
    const res = await client.send(
      new PutLogEventsCommand({
        logGroupName: LOG_GROUP,
        logStreamName: streamName,
        logEvents: [{ message: log, timestamp }],
        sequenceToken: nextSequenceToken,
      })
    );
    nextSequenceToken = res.nextSequenceToken;
  } catch (err) {
    if (err && typeof (err as any).message === 'string') {
      if ((err as any).message.includes('InvalidSequenceTokenException')) {
        const match = (err as any).message.match(/sequenceToken is: (\S+)/);
        if (match) {
          nextSequenceToken = match[1];
          await sendToCloudWatch(log, timestamp);
          return;
        }
      }
    }
    process.stderr.write(`[CloudWatch] Failed to send log: ${err}\n`);
  }
}

export function createCloudWatchTransport(): Transport | null {
  if (!LOG_GROUP) return null;
  return new Transport({
    log(info, callback) {
      const message = typeof info.message === 'string' ? info.message : JSON.stringify(info);
      const timestamp = info.timestamp ? new Date(info.timestamp).getTime() : Date.now();
      sendToCloudWatch(message, timestamp).finally(() => callback?.());
    },
  });
}
