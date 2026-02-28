# Implementation Plan: ZeroTRUST Production Readiness

## Overview

This implementation plan transforms the ZeroTRUST system from a 45% complete prototype into a production-ready misinformation detection platform. The plan focuses on implementing critical missing components in a logical sequence, with each task building on previous work. The approach prioritizes unblocking AI capabilities first, then implementing core verification logic, followed by API routes, testing, and finally AWS deployment.

## Tasks

- [x] 1. Configure AWS Bedrock and External APIs
  - Configure AWS credentials in .env.local (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)
  - Enable Bedrock models in AWS Console (Claude 3.5 Sonnet, Claude 3 Haiku, Mistral Large)
  - Configure external API keys (NEWS_API_KEY, GNEWS_API_KEY, GOOGLE_SEARCH_KEY, GOOGLE_SEARCH_ENGINE_ID, TWITTER_BEARER_TOKEN, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
  - Test Bedrock integration by invoking each model
  - Test external API integration by querying each service
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [x] 2. Implement Normalization Layer
  - [x] 2.1 Create TextNormalizer class
    - Implement HTML tag stripping and entity decoding
    - Implement lowercase conversion
    - Implement stop word removal
    - Implement unicode normalization
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [x] 2.2 Write property test for text normalization
    - **Property 23: Text Normalization Idempotence**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**
  
  - [x] 2.3 Create MetadataExtractor class
    - Implement URL extraction
    - Implement statistics extraction
    - Implement quote extraction
    - _Requirements: 13.5_
  
  - [x] 2.4 Write property test for metadata extraction
    - **Property 24: Metadata Extraction Completeness**
    - **Validates: Requirements 13.5**
  
  - [x] 2.5 Create LanguageDetector class
    - Implement language detection using langdetect or similar
    - Return ISO 639-1 language codes
    - _Requirements: 13.6_
  
  - [x] 2.6 Write property test for language detection
    - **Property 25: Language Detection Accuracy**
    - **Validates: Requirements 13.6**

- [x] 3. Implement Credibility Scoring System
  - [x] 3.1 Create CredibilityScorer class
    - Implement Evidence Quality calculation (40% weight)
    - Implement Agent Consensus calculation (30% weight)
    - Implement Source Reliability calculation (30% weight)
    - Implement confidence penalty logic
    - Implement score-to-category mapping
    - Implement confidence level calculation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10_
  
  - [x] 3.2 Write property test for credibility score formula
    - **Property 5: Credibility Score Formula Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
  
  - [x] 3.3 Write property test for score-to-category mapping
    - **Property 6: Score-to-Category Mapping**
    - **Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**
  
  - [x] 3.4 Write property test for confidence penalty
    - **Property 7: Confidence Penalty Application**
    - **Validates: Requirements 4.10**

- [x] 4. Implement Evidence Aggregator
  - [x] 4.1 Create EvidenceAggregator class
    - Implement URL normalization function
    - Implement source deduplication by normalized URL
    - Implement evidence summary calculation (stance counts)
    - Implement source sorting by credibility score
    - Implement agent coverage statistics
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 4.2 Write property test for source deduplication
    - **Property 8: Source Deduplication by URL**
    - **Validates: Requirements 5.1**
  
  - [x] 4.3 Write property test for evidence stance counting
    - **Property 9: Evidence Stance Counting**
    - **Validates: Requirements 5.2**
  
  - [x] 4.4 Write property test for source sorting
    - **Property 10: Source Sorting by Credibility**
    - **Validates: Requirements 5.3**
  
  - [x] 4.5 Write property test for agent verdict preservation
    - **Property 11: Agent Verdict Preservation**
    - **Validates: Requirements 5.5**

- [-] 5. Implement Report Generator
  - [x] 5.1 Create ReportGenerator class
    - Implement report structure assembly
    - Implement limitation auto-generation logic
    - Implement LLM-based recommendation generation using Bedrock
    - Implement report serialization to JSON
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  
  - [x] 5.2 Write property test for report schema completeness
    - **Property 12: Report Schema Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.7**
  
  - [-] 5.3 Write property test for report serialization
    - **Property 13: Report Serialization Round Trip**
    - **Validates: Requirements 6.8**
  
  - [~] 5.4 Write property test for limitation auto-generation
    - **Property 14: Limitation Auto-Generation**
    - **Validates: Requirements 2.7, 6.6**

- [~] 6. Checkpoint - Verify core services work independently
  - Ensure all tests pass, ask the user if questions arise.

- [~] 7. Implement Manager Agent with LangGraph
  - [~] 7.1 Create AgentState TypedDict
    - Define all state fields (claim, normalized_claim, domain, selected_agents, agent_results, etc.)
    - _Requirements: 3.1_
  
  - [~] 7.2 Implement workflow node functions
    - Implement normalize_claim node (uses TextNormalizer, MetadataExtractor, LanguageDetector)
    - Implement analyze_claim_domain node (uses Bedrock for domain classification)
    - Implement select_agents node (domain-to-agent mapping)
    - Implement execute_agents node (parallel execution with asyncio.gather)
    - Implement aggregate_evidence node (uses EvidenceAggregator)
    - Implement calculate_credibility node (uses CredibilityScorer)
    - Implement generate_report node (uses ReportGenerator)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [~] 7.3 Construct LangGraph StateGraph
    - Add all nodes to graph
    - Add edges in correct order
    - Set entry and finish points
    - Compile graph
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [~] 7.4 Write property test for Manager Agent workflow
    - **Property 4: Manager Agent Workflow Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**
  
  - [~] 7.5 Write property test for parallel agent execution
    - **Property 29: Parallel Agent Execution**
    - **Validates: Requirements 15.3**

- [~] 8. Create Verification Router
  - [~] 8.1 Create /verify endpoint in FastAPI
    - Define Pydantic request model
    - Implement request validation
    - Invoke Manager Agent
    - Return serialized report
    - Handle errors gracefully
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
  
  - [~] 8.2 Write integration test for verification flow
    - Test complete end-to-end verification
    - Test with various claim types
    - Test error handling
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [~] 9. Implement Authentication Routes
  - [~] 9.1 Create auth.routes.ts
    - Implement POST /register endpoint (bcrypt password hashing, user creation)
    - Implement POST /login endpoint (credential validation, JWT generation)
    - Implement POST /refresh endpoint (token validation, new access token)
    - Implement POST /logout endpoint (token revocation via Redis)
    - _Requirements: 7.3, 7.4, 7.5, 7.6_
  
  - [~] 9.2 Write unit tests for authentication routes
    - Test registration with valid/invalid inputs
    - Test login with valid/invalid credentials
    - Test token refresh
    - Test logout and token revocation
    - _Requirements: 7.3, 7.4, 7.5, 7.6_
  
  - [~] 9.3 Write property test for authentication token round trip
    - **Property 15: Authentication Token Round Trip**
    - **Validates: Requirements 7.4, 7.6**

- [~] 10. Implement Verification Routes
  - [~] 10.1 Create verify.routes.ts
    - Implement POST / endpoint (request validation, VerificationService invocation)
    - Implement GET /presigned-url endpoint (S3 presigned URL generation)
    - Add optionalAuth middleware to POST /
    - Add authMiddleware to GET /presigned-url
    - _Requirements: 7.1, 9.1, 9.2_
  
  - [~] 10.2 Write unit tests for verification routes
    - Test POST / with valid/invalid requests
    - Test presigned URL generation
    - Test authentication enforcement
    - _Requirements: 7.1, 9.1, 9.2_
  
  - [~] 10.3 Write property test for verification API validation
    - **Property 16: Verification API Request Validation**
    - **Validates: Requirements 7.1, 7.7**

- [~] 11. Implement History Routes
  - [~] 11.1 Create history.routes.ts
    - Implement GET / endpoint (pagination, VerificationService.getHistory)
    - Implement GET /:id endpoint (single verification retrieval, access control)
    - Add authMiddleware to both endpoints
    - _Requirements: 7.2_
  
  - [~] 11.2 Write unit tests for history routes
    - Test pagination with various page/limit values
    - Test single verification retrieval
    - Test access control (users can only see their own history)
    - _Requirements: 7.2_
  
  - [~] 11.3 Write property test for history pagination
    - **Property 17: History Pagination Correctness**
    - **Validates: Requirements 7.2**

- [~] 12. Implement Rate Limiting Middleware
  - [~] 12.1 Create rateLimit.middleware.ts
    - Implement rate limit configuration for all tiers (public, free, pro, enterprise)
    - Implement Redis-based request tracking
    - Implement rate limit enforcement with 429 responses
    - Add rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_
  
  - [~] 12.2 Write property test for rate limiting
    - **Property 18: Rate Limiting by Tier**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

- [~] 13. Wire API Routes to Express App
  - [~] 13.1 Update app.ts to register all routes
    - Import auth.routes, verify.routes, history.routes
    - Register routes with Express app
    - Apply rate limiting middleware to appropriate routes
    - Test all endpoints with curl or Postman
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [~] 14. Checkpoint - Verify API Gateway and Verification Engine integration
  - Ensure all tests pass, ask the user if questions arise.

- [~] 15. Implement S3 Media Upload Flow
  - [~] 15.1 Create S3 bucket and configure CORS
    - Create S3 bucket: zerotrust-media-uploads-{account}
    - Configure CORS to allow uploads from web portal
    - Configure S3 event notifications to SQS
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [~] 15.2 Implement presigned URL generation
    - Already implemented in verify.routes.ts (task 10.1)
    - Test presigned URL generation and upload
    - _Requirements: 9.1, 9.2_
  
  - [~] 15.3 Implement file validation
    - Add file size validation (10MB images, 100MB videos)
    - Add file type validation (JPEG/PNG/GIF, MP4/MOV)
    - Return 400 for invalid files
    - _Requirements: 9.6, 9.7_
  
  - [~] 15.4 Write property test for S3 presigned URL generation
    - **Property 19: S3 Presigned URL Generation**
    - **Validates: Requirements 9.1, 9.2**
  
  - [~] 15.5 Write property test for media file validation
    - **Property 20: Media File Validation**
    - **Validates: Requirements 9.6, 9.7**

- [~] 16. Deploy DynamoDB Cache Tier
  - [~] 16.1 Create DynamoDB table
    - Create table: zerotrust-claim-verifications
    - Configure partition key: claim_hash (String)
    - Enable TTL on ttl attribute
    - Set billing mode to PAY_PER_REQUEST
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [~] 16.2 Test DynamoDB integration
    - Test cache writes to DynamoDB
    - Test cache reads from DynamoDB
    - Test TTL expiration
    - Test fallback when DynamoDB unavailable
    - _Requirements: 10.1, 10.2, 10.3, 10.7_
  
  - [~] 16.3 Write property test for cache tier waterfall
    - **Property 21: Cache Tier Waterfall**
    - **Validates: Requirements 10.1, 10.2, 10.3**
  
  - [~] 16.4 Write property test for cache fallback resilience
    - **Property 22: Cache Fallback Resilience**
    - **Validates: Requirements 10.7, 14.4**

- [~] 17. Implement Error Handling and Resilience
  - [~] 17.1 Implement circuit breaker for external dependencies
    - Create CircuitBreaker class
    - Apply to external API calls (NewsAPI, Google CSE, Twitter, Reddit)
    - Apply to AWS service calls (Bedrock, S3, DynamoDB)
    - Configure thresholds (5 failures in 60s, 30s timeout)
    - _Requirements: 14.7_
  
  - [~] 17.2 Implement retry logic with exponential backoff
    - Add retry decorator for database operations
    - Configure max 3 attempts with exponential backoff
    - Return 503 after all retries fail
    - _Requirements: 14.5, 14.6_
  
  - [~] 17.3 Implement agent timeout enforcement
    - Add 10-second timeout to agent execution
    - Include timeout note in report when agent times out
    - _Requirements: 14.2_
  
  - [~] 17.4 Write property test for external API error resilience
    - **Property 3: External API Error Resilience**
    - **Validates: Requirements 2.4, 14.1**
  
  - [~] 17.5 Write property test for agent timeout enforcement
    - **Property 26: Agent Timeout Enforcement**
    - **Validates: Requirements 14.2**
  
  - [~] 17.6 Write property test for database retry
    - **Property 27: Database Retry with Exponential Backoff**
    - **Validates: Requirements 14.5, 14.6**
  
  - [~] 17.7 Write property test for circuit breaker
    - **Property 28: Circuit Breaker for External Dependencies**
    - **Validates: Requirements 14.7**

- [~] 18. Implement Cache Compression
  - [~] 18.1 Add compression to cache writes
    - Use gzip compression for cache entries
    - Compress before writing to Redis and DynamoDB
    - Decompress after reading from cache
    - _Requirements: 15.5_
  
  - [~] 18.2 Write property test for cache compression round trip
    - **Property 30: Cache Compression Round Trip**
    - **Validates: Requirements 15.5**

- [~] 19. Write Remaining Property Tests
  - [~] 19.1 Write property test for Bedrock integration
    - **Property 1: Bedrock Integration with Fallback Chain**
    - **Validates: Requirements 1.2, 1.3, 1.4**
  
  - [~] 19.2 Write property test for agent source consultation
    - **Property 2: Agent Source Consultation**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.6**

- [~] 20. Write Integration Tests
  - [~] 20.1 Write integration test for complete verification flow
    - Test end-to-end verification from API Gateway to Verification Engine
    - Test with various claim types (text, URL)
    - Test cache tier waterfall
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [~] 20.2 Write integration test for authentication flow
    - Test register → login → access protected route → refresh → logout
    - Test token revocation
    - _Requirements: 7.3, 7.4, 7.5, 7.6_

- [~] 21. Checkpoint - Verify all tests pass and coverage >70%
  - Run all unit tests, property tests, and integration tests
  - Generate coverage report
  - Ensure coverage >70% across all services
  - Ensure all tests pass, ask the user if questions arise.

- [~] 22. Deploy to AWS Infrastructure
  - [~] 22.1 Create VPC and networking
    - Create VPC with public and private subnets
    - Create NAT gateway for private subnets
    - Configure security groups
    - Configure route tables
    - _Requirements: 12.6_
  
  - [~] 22.2 Create RDS PostgreSQL instance
    - Create Multi-AZ RDS PostgreSQL instance
    - Configure security groups
    - Run Prisma migrations
    - Test connectivity
    - _Requirements: 12.2_
  
  - [~] 22.3 Create ElastiCache Redis cluster
    - Create Redis cluster
    - Configure security groups
    - Update API Gateway connection string
    - Test cache operations
    - _Requirements: 12.3_
  
  - [~] 22.4 Create ECS cluster and task definitions
    - Create ECS cluster
    - Write task definitions for API Gateway, Verification Engine, Media Analysis
    - Configure service discovery
    - Deploy containers to ECS
    - _Requirements: 12.1_
  
  - [~] 22.5 Create Application Load Balancer
    - Create ALB
    - Configure target groups for each service
    - Set up health checks
    - Configure SSL certificate
    - _Requirements: 12.4_
  
  - [~] 22.6 Configure AWS Secrets Manager
    - Migrate all secrets from .env to Secrets Manager
    - Update services to fetch secrets from Secrets Manager
    - Remove .env files from containers
    - _Requirements: 12.7_
  
  - [~] 22.7 Configure CloudWatch logging and monitoring
    - Create log groups for each service
    - Configure log streaming from ECS
    - Create CloudWatch dashboards
    - Set up alarms for errors and performance
    - _Requirements: 12.8_
  
  - [~] 22.8 Configure auto-scaling
    - Configure ECS auto-scaling based on CPU and memory
    - Set min/max task counts
    - Test scaling behavior
    - _Requirements: 12.9_

- [~] 23. Final Checkpoint - Production readiness verification
  - Run end-to-end smoke tests against production environment
  - Verify all services are healthy
  - Verify cache tiers are working
  - Verify rate limiting is enforced
  - Verify authentication flows work
  - Verify verification returns accurate results with >0.7 confidence
  - Verify 30-60 sources are consulted per verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test-related sub-tasks and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- AWS deployment tasks should be executed in order due to dependencies
- All tests should be run in CI/CD pipeline before deployment

