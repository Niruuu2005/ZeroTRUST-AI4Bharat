# 🛡️ ZeroTRUST AI4Bharat

**AI-Powered Fake News Detection & Claim Verification System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20S3%20%7C%20Lambda-orange)](https://aws.amazon.com/)
[![Security](https://img.shields.io/badge/Security-No%20Secrets%20Committed-green)]()

---

## ⚠️ IMPORTANT: Security First

> **🔐 This repository contains NO real credentials.** All sensitive data uses placeholders.  
> **📖 New users**: Read [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md) to configure your own credentials.

**Before contributing or committing:**
- ✅ Read [SECURITY_README.md](SECURITY_README.md)
- ✅ Check [DELETE_BEFORE_COMMIT.md](DELETE_BEFORE_COMMIT.md)
- ✅ Never commit `.env` files with real credentials

---

## 🚀 What is ZeroTRUST?

ZeroTRUST is an advanced AI-powered platform that helps combat misinformation by:

- 🔍 **Automated Fact-Checking**: Analyzes claims against multiple trustworthy sources
- 🤖 **Multi-Agent AI System**: Uses specialized AI agents (Research, News, Scientific, Social Media)
- 🎥 **Media Analysis**: Detects deepfakes, manipulated images, and audio
- 📊 **Real-time Verification**: Provides credibility scores and evidence trails
- 🌐 **Multi-Platform**: Web portal, browser extension, and API access

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Setup & Configuration](#-setup--configuration)
- [Documentation](#-documentation)
- [Technology Stack](#-technology-stack)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
│  Web Portal  │  Browser Extension  │  Mobile App (Future)  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (Node.js)                      │
│  Authentication │ Rate Limiting │ Request Routing            │
└─────────────┬───────────────────────────────┬───────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────┐   ┌──────────────────────────┐
│  Verification Engine (Python)│   │  Media Analysis (Python) │
│  ┌───────────────────────┐  │   │  ┌──────────────────┐   │
│  │ Manager Agent (LLM)   │  │   │  │ Image Analysis   │   │
│  │ ├─ Research Agent     │  │   │  │ Video Analysis   │   │
│  │ ├─ News Agent         │  │   │  │ Audio Analysis   │   │
│  │ ├─ Scientific Agent   │  │   │  │ Text Extraction  │   │
│  │ └─ Social Media Agent │  │   │  └──────────────────┘   │
│  └───────────────────────┘  │   └──────────────────────────┘
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│                     AWS Services                             │
│  Bedrock (LLM) │ S3 │ Lambda │ DynamoDB │ CloudWatch        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Capabilities

- ✅ **Multi-Source Verification**: Checks claims against news APIs, academic papers, fact-check databases
- ✅ **AI Agent Orchestration**: Manager agent coordinates specialized agents for comprehensive analysis
- ✅ **Media Forensics**: Detects manipulated images, deepfake videos, and synthetic audio
- ✅ **Evidence Tracking**: Provides source citations and confidence scores
- ✅ **Real-time Analysis**: Fast processing with caching for repeated queries
- ✅ **User Authentication**: Secure JWT-based auth system
- ✅ **Browser Extension**: Verify claims directly while browsing

### Technical Features

- 🔄 **Scalable Architecture**: Microservices-based design
- 📊 **Comprehensive Logging**: CloudWatch integration for monitoring
- 🔐 **Security First**: No hardcoded credentials, JWT authentication
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- 🧪 **Extensive Testing**: Unit, integration, and E2E tests with Playwright
- 🌐 **AWS Integration**: Leverages Bedrock, S3, Lambda, DynamoDB

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Docker** & Docker Compose (optional)
- **AWS Account** with Bedrock access
- **PostgreSQL** database (or Supabase free tier)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/ZeroTRUST-AI4Bharat.git
cd ZeroTRUST-AI4Bharat
```

### 2. Configure Credentials

**⚠️ IMPORTANT**: Follow the complete setup guide:

```bash
# Read the setup guide
cat SETUP_SECRETS_GUIDE.md

# Copy environment templates
cp apps/api-gateway/.env.example apps/api-gateway/.env
cp apps/web-portal/.env.example apps/web-portal/.env

# Edit with your credentials
nano apps/api-gateway/.env
```

**Required credentials:**
- AWS Access Key ID & Secret
- Database connection string (PostgreSQL/Supabase)
- JWT secret (generate with `openssl rand -hex 64`)

**See detailed instructions:** [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md)

### 3. Install Dependencies

```bash
# API Gateway
cd apps/api-gateway
npm install

# Web Portal
cd ../web-portal
npm install

# Verification Engine
cd ../verification-engine
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
```

### 4. Run Services

**Option A: Using Docker Compose (Recommended)**

```bash
docker-compose up
```

**Option B: Manual Start**

```bash
# Terminal 1: API Gateway
cd apps/api-gateway
npm run dev

# Terminal 2: Verification Engine
cd apps/verification-engine
uvicorn src.main:app --reload --port 8000

# Terminal 3: Web Portal
cd apps/web-portal
npm run dev

# Terminal 4: Media Analysis
cd apps/media-analysis
uvicorn src.main:app --reload --port 8001
```

### 5. Access the Application

- **Web Portal**: http://localhost:5173
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔧 Setup & Configuration

### Environment Setup

| Guide | Description |
|-------|-------------|
| [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md) | **START HERE** - Complete credential setup guide |
| [SECURITY_README.md](SECURITY_README.md) | Security best practices and verification |
| [DELETE_BEFORE_COMMIT.md](DELETE_BEFORE_COMMIT.md) | Pre-commit checklist |

### AWS Setup

| Step | Guide | Description |
|------|-------|-------------|
| 1 | [01-iam-setup.md](aws-setup/01-iam-setup.md) | IAM user and permissions |
| 2 | [02-bedrock-setup.md](aws-setup/02-bedrock-setup.md) | Enable Bedrock models |
| 3 | [03-s3-setup.md](aws-setup/03-s3-setup.md) | S3 bucket for media |
| 4 | [04-dynamodb-setup.md](aws-setup/04-dynamodb-setup.md) | DynamoDB tables |
| 5 | [05-cloudwatch-setup.md](aws-setup/05-cloudwatch-setup.md) | CloudWatch logging |
| 6 | [06-lambda-setup.md](aws-setup/06-lambda-setup.md) | Lambda functions |
| 7 | [07-media-services-setup.md](aws-setup/07-media-services-setup.md) | Media analysis services |

### Quick References

- **Free Tier Guide**: [QUICKSTART_FREE_TIER.md](QUICKSTART_FREE_TIER.md)
- **AWS Migration**: [AWS_MIGRATION_GUIDE.md](AWS_MIGRATION_GUIDE.md)
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## 📚 Documentation

### For Developers

- **Architecture Analysis**: [COMPREHENSIVE_ARCHITECTURE_ANALYSIS.md](COMPREHENSIVE_ARCHITECTURE_ANALYSIS.md)
- **Implementation Status**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Development Plan**: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
- **Testing Guide**: [E2E_TESTING_GUIDE.md](E2E_TESTING_GUIDE.md)

### For DevOps

- **AWS Services Analysis**: [AWS_SERVICES_USAGE_ANALYSIS.md](AWS_SERVICES_USAGE_ANALYSIS.md)
- **Free Tier Optimization**: [FREE_TIER_OPTIMIZATION.md](FREE_TIER_OPTIMIZATION.md)
- **Deployment Steps**: [STEP_4_ECS_DEPLOYMENT.md](STEP_4_ECS_DEPLOYMENT.md)

---

## 🛠️ Technology Stack

### Frontend
- **React** + **TypeScript** + **Vite**
- **TailwindCSS** for styling
- **Axios** for API calls
- **Browser Extension** (Vanilla JS)

### Backend
- **Node.js** + **Express** (API Gateway)
- **Python** + **FastAPI** (Verification Engine & Media Analysis)
- **PostgreSQL** (Database)
- **Redis** (Caching)

### AI & ML
- **AWS Bedrock** (LLM inference)
  - Amazon Nova models
  - Mistral Pixtral
- **LangChain** (Agent orchestration)
- **Custom AI Agents** (Research, News, Scientific, Social)

### AWS Services
- **Bedrock**: LLM hosting
- **S3**: Media storage
- **Lambda**: Serverless functions
- **DynamoDB**: NoSQL cache
- **CloudWatch**: Logging & monitoring
- **Rekognition**: Image analysis
- **Textract**: Text extraction
- **Transcribe**: Audio transcription

### DevOps
- **Docker** & **Docker Compose**
- **Playwright** (E2E testing)
- **Pytest** (Python testing)
- **Jest** (JavaScript testing)

---

## 🤝 Contributing

We welcome contributions! Before contributing:

1. **Read security guidelines**: [SECURITY_README.md](SECURITY_README.md)
2. **Never commit real credentials**
3. **Follow the development plan**: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)
4. **Run tests** before submitting PRs

### Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes

# 3. Run tests
npm test                    # Frontend tests
pytest                      # Python tests
npm run test:e2e           # E2E tests

# 4. Verify no secrets
git diff --staged | grep -iE "AKIA|secret_access_key"
# Should return nothing!

# 5. Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AI4Bharat** for the initiative
- **AWS** for Bedrock and infrastructure services
- **Open-source community** for amazing tools and libraries

---

## 📞 Support & Contact

- **Documentation**: Start with [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md)
- **Issues**: Please use GitHub Issues
- **Security**: For security vulnerabilities, please email security@zerotrust-ai4bharat.org

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ by the ZeroTRUST AI4Bharat Team**

**Last Updated**: March 3, 2026
