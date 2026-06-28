# 🚀 Quick Start Guide

## Method 1: Local Installation (Recommended for Development)

### 1. Clone the Project

```bash
git clone <your-repo-url>
cd LLM-TradeBot
```

### 2. One-Click Install

```bash
chmod +x install.sh
./install.sh
```

The install script will automatically:

- ✅ Detect Python version (requires 3.11+)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Generate `.env` configuration file

### 3. Configure API Keys

Edit `.env` file and fill in your API keys:

```bash
# Binance API
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_TESTNET=true

# LLM API (DeepSeek)
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 4. One-Click Start

```bash
./start.sh
```

The start script will automatically:

- ✅ Activate virtual environment
- ✅ Check environment variables
- ✅ Start Dashboard (test mode by default)

Visit Dashboard: **<http://localhost:8000>**

---

## Method 2: Docker Deployment (Recommended for Production)

### 1. Clone the Project

```bash
git clone <your-repo-url>
cd LLM-TradeBot
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and fill in API keys
```

### 3. One-Click Start

```bash
cd docker
docker-compose up -d
```

### 4. View Logs

```bash
docker-compose logs -f
```

### 5. Stop Service

```bash
docker-compose down
```

---

## Startup Parameters

### Local Startup

```bash
# Test mode + continuous run
./start.sh --test --mode continuous

# Production mode
./start.sh --mode continuous

# Single run
./start.sh --test
```

### Docker Startup

Modify the `CMD` parameters in `docker/docker-compose.yml`.

---

## Quick Self-Check (Recommended for Beginners)

```bash
# Run full test suite (automatically isolates external pytest plugin pollution)
python3 scripts/run_tests.py
```

For details, see: `docs/TESTING_CN.md`

To run only a specific file, append pytest parameters:

```bash
python3 scripts/run_tests.py -q tests/test_agent_config.py
```

---

## Common Issues

### Q: Python version not meeting requirements?

**A**: Install Python 3.11+

- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`

### Q: Dependency installation failed?

**A**: Ensure build tools are installed

- macOS: `xcode-select --install`
- Ubuntu: `sudo apt install build-essential`

### Q: Dashboard not accessible?

**A**: Check if port 8000 is occupied

```bash
lsof -i :8000
```

### Q: Docker build failed?

**A**: Ensure Docker is installed and running

```bash
docker --version
docker-compose --version
```

---

## Directory Structure

```
LLM-TradeBot/
├── install.sh          # One-click install script
├── start.sh            # One-click start script
├── main.py             # Main program
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/                # Source code
├── data/               # Data directory
├── logs/               # Log directory
└── web/                # Dashboard frontend
```

---

## Next Steps

1. ✅ Visit Dashboard: <http://localhost:8000>
2. ✅ Click "Start" to begin trading
3. ✅ View real-time decisions and analysis

**Wishing you successful trading!** 🎉
