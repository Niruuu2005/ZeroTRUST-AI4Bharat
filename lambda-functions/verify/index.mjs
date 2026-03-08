import { DynamoDBClient, GetItemCommand, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { marshall, unmarshall } from '@aws-sdk/util-dynamodb';
import crypto from 'crypto';

const dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION });

export const handler = async (event) => {
    const body = JSON.parse(event.body);
    const cacheKey = crypto.createHash('sha256').update(body.content).digest('hex');

    try {
        // Check cache
        const cached = await dynamodb.send(new GetItemCommand({
            TableName: 'ZeroTrustCache',
            Key: marshall({ cache_key: cacheKey })
        }));

        if (cached.Item) {
            return {
                statusCode: 200,
                headers: { 'Access-Control-Allow-Origin': '*' },
                body: JSON.stringify({
                    ...unmarshall(cached.Item).result,
                    cached: true
                })
            };
        }

        // Call EC2 service
        const response = await fetch(`http://${process.env.EC2_IP}:8000/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const result = await response.json();

        // Store in cache
        await dynamodb.send(new PutItemCommand({
            TableName: 'ZeroTrustCache',
            Item: marshall({
                cache_key: cacheKey,
                result: result,
                ttl: Math.floor(Date.now() / 1000) + 86400
            })
        }));

        return {
            statusCode: 200,
            headers: { 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ ...result, cached: false })
        };
    } catch (error) {
        return {
            statusCode: 500,
            headers: { 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ error: error.message })
        };
    }
};
