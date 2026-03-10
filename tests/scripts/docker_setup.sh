#!/bin/bash
# Complete Docker setup for fraud detection system

set -e

echo "🚀 Starting Fraud Detection System Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

# Start services
echo -e "${YELLOW}Starting Docker services...${NC}"
docker-compose up -d

# Wait for services
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check PostgreSQL
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 5
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

# Check Redis
echo -e "${YELLOW}Checking Redis...${NC}"
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; do
    echo "Waiting for Redis..."
    sleep 5
done
echo -e "${GREEN}✓ Redis is ready${NC}"

# Check Kafka
echo -e "${YELLOW}Checking Kafka...${NC}"
sleep 5
echo -e "${GREEN}✓ Kafka is ready${NC}"

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python scripts/setup_db.py

echo -e "${GREEN}✓ Database initialized${NC}"

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Generate training data: python scripts/generate_sample_data.py"
echo "2. Train models: python scripts/run_training.py"
echo "3. Start simulator: python scripts/run_simulator.py"
echo "4. Start API: python scripts/run_api.py"
echo "5. View dashboard: streamlit run dashboard/app.py"
echo ""
echo "Access URLs:"
echo "- API: http://localhost:8000"
echo "- Docs: http://localhost:8000/docs"
echo "- Dashboard: http://localhost:8501"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"