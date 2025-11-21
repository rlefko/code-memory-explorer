# Claude Code Memory Explorer - Makefile
# Simple, beautiful commands for managing the application

# Colors for beautiful output
BLUE := \033[1;34m
GREEN := \033[1;32m
YELLOW := \033[1;33m
RED := \033[1;31m
PURPLE := \033[1;35m
CYAN := \033[1;36m
WHITE := \033[1;37m
NC := \033[0m # No Color

# Port configuration (with defaults)
NGINX_PORT ?= 8080
BACKEND_PORT ?= 8000
QDRANT_PORT ?= 6333

# Export for docker-compose
export NGINX_PORT BACKEND_PORT QDRANT_PORT

# Docker compose command (auto-detect version)
DOCKER_COMPOSE := $(shell which docker-compose 2>/dev/null || echo "docker compose")

# Auto-detect ARM64 platform
ARCH := $(shell uname -m)
ifeq ($(ARCH),arm64)
    COMPOSE_FILE := -f docker-compose.yml -f docker-compose.arm64.yml
else ifeq ($(ARCH),aarch64)
    COMPOSE_FILE := -f docker-compose.yml -f docker-compose.arm64.yml
else
    COMPOSE_FILE := -f docker-compose.yml
endif

# Default target - starts everything
.PHONY: all
all: run

# Main commands
.PHONY: run
run: header check-prerequisites
	@echo "$(BLUE)🚀 Starting Claude Code Memory Explorer...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) --profile internal-qdrant up -d
	@echo "$(GREEN)⏳ Waiting for services to be ready...$(NC)"
	@sleep 5
	@make health-check
	@echo ""
	@echo "$(GREEN)✨ Application is ready!$(NC)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(WHITE)   🌐 Web Interface:$(NC) http://localhost:$(NGINX_PORT)"
	@echo "$(WHITE)   📚 API Docs:$(NC) http://localhost:$(NGINX_PORT)/api/docs"
	@echo "$(WHITE)   🔍 Qdrant:$(NC) http://localhost:$(NGINX_PORT)/qdrant/dashboard"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Useful commands:$(NC)"
	@echo "   $(WHITE)make logs$(NC)    - View application logs"
	@echo "   $(WHITE)make stop$(NC)    - Stop all services"
	@echo "   $(WHITE)make restart$(NC) - Restart all services"
	@echo "   $(WHITE)make clean$(NC)   - Remove everything"
	@echo ""

# Run with external Qdrant
.PHONY: external-qdrant
external-qdrant: header check-prerequisites check-external-qdrant
	@echo "$(BLUE)🚀 Starting with external Qdrant instance...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) -f docker-compose.external.yml up -d
	@echo "$(GREEN)⏳ Waiting for services to be ready...$(NC)"
	@sleep 5
	@make health-check-external
	@echo ""
	@echo "$(GREEN)✨ Application is ready!$(NC)"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(WHITE)   🌐 Web Interface:$(NC) http://localhost:$(NGINX_PORT)"
	@echo "$(WHITE)   📚 API Docs:$(NC) http://localhost:$(NGINX_PORT)/api/docs"
	@echo "$(WHITE)   🔍 Using external Qdrant at:$(NC) localhost:6333"
	@echo "$(CYAN)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(YELLOW)💡 Useful commands:$(NC)"
	@echo "   $(WHITE)make logs$(NC)    - View application logs"
	@echo "   $(WHITE)make stop$(NC)    - Stop all services"
	@echo "   $(WHITE)make restart$(NC) - Restart all services"
	@echo ""

# Development mode with hot reload
.PHONY: dev
dev: header
	@echo "$(BLUE)🔧 Starting in development mode with hot reload...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) -f docker-compose.dev.yml up

# Stop all services
.PHONY: stop
stop:
	@echo "$(YELLOW)🛑 Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ All services stopped$(NC)"

# Restart services
.PHONY: restart
restart:
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) restart
	@echo "$(GREEN)✅ Services restarted$(NC)"

# View logs
.PHONY: logs
logs:
	@echo "$(BLUE)📋 Showing logs (Ctrl+C to exit)...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) logs -f

# View logs for specific service
.PHONY: logs-%
logs-%:
	@echo "$(BLUE)📋 Showing logs for $* (Ctrl+C to exit)...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) logs -f $*

# Clean everything (including volumes)
.PHONY: clean
clean:
	@echo "$(RED)⚠️  This will remove all containers, volumes, and data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) down -v --rmi local
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Rebuild images
.PHONY: rebuild
rebuild:
	@echo "$(YELLOW)🔨 Rebuilding images...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) build --no-cache
	@echo "$(GREEN)✅ Images rebuilt$(NC)"

# Build images
.PHONY: build
build:
	@echo "$(YELLOW)🔨 Building images...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) build
	@echo "$(GREEN)✅ Images built$(NC)"

# Pull latest images
.PHONY: pull
pull:
	@echo "$(BLUE)⬇️  Pulling latest images...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) pull
	@echo "$(GREEN)✅ Images updated$(NC)"

# Check service status
.PHONY: status
status:
	@echo "$(BLUE)📊 Service Status:$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) ps

# Health check
.PHONY: health-check
health-check:
	@echo "$(BLUE)🏥 Checking service health...$(NC)"
	@curl -f http://localhost:$(NGINX_PORT)/api/health > /dev/null 2>&1 && echo "$(GREEN)✅ Backend API: Healthy$(NC)" || echo "$(RED)❌ Backend API: Not responding$(NC)"
	@curl -f http://localhost:$(NGINX_PORT)/qdrant/health > /dev/null 2>&1 && echo "$(GREEN)✅ Qdrant DB: Healthy$(NC)" || echo "$(RED)❌ Qdrant DB: Not responding$(NC)"
	@curl -f http://localhost:$(NGINX_PORT)/ > /dev/null 2>&1 && echo "$(GREEN)✅ Frontend: Healthy$(NC)" || echo "$(RED)❌ Frontend: Not responding$(NC)"

# Health check for external Qdrant mode
.PHONY: health-check-external
health-check-external:
	@echo "$(BLUE)🏥 Checking service health (external Qdrant)...$(NC)"
	@curl -f http://localhost:$(NGINX_PORT)/api/health > /dev/null 2>&1 && echo "$(GREEN)✅ Backend API: Healthy$(NC)" || echo "$(RED)❌ Backend API: Not responding$(NC)"
	@curl -f http://localhost:6333/health > /dev/null 2>&1 && echo "$(GREEN)✅ External Qdrant: Healthy$(NC)" || echo "$(RED)❌ External Qdrant: Not responding$(NC)"
	@curl -f http://localhost:$(NGINX_PORT)/ > /dev/null 2>&1 && echo "$(GREEN)✅ Frontend: Healthy$(NC)" || echo "$(RED)❌ Frontend: Not responding$(NC)"

# Check if external Qdrant is available
.PHONY: check-external-qdrant
check-external-qdrant:
	@echo "$(BLUE)🔍 Checking external Qdrant availability...$(NC)"
	@curl -f http://localhost:6333/health > /dev/null 2>&1 || (echo "$(RED)❌ External Qdrant not found at localhost:6333$(NC)" && echo "$(YELLOW)Please ensure your Qdrant instance is running$(NC)" && exit 1)
	@echo "$(GREEN)✅ External Qdrant is available$(NC)"

# Shell access
.PHONY: shell-%
shell-%:
	@echo "$(BLUE)🐚 Opening shell in $* container...$(NC)"
	@$(DOCKER_COMPOSE) $(COMPOSE_FILE) exec $* /bin/sh

# Index a sample project (for testing)
.PHONY: index-sample
index-sample:
	@echo "$(PURPLE)📚 Indexing sample project...$(NC)"
	@echo "$(YELLOW)Note: Ensure claude-indexer is installed$(NC)"
	@claude-indexer index -p ../claude_indexer -c sample-indexer-code || echo "$(RED)❌ Failed to index. Is claude-indexer installed?$(NC)"

# Open in browser
.PHONY: open
open:
	@echo "$(BLUE)🌐 Opening in browser...$(NC)"
	@python3 -m webbrowser "http://localhost:8080" 2>/dev/null || \
	 python -m webbrowser "http://localhost:8080" 2>/dev/null || \
	 open "http://localhost:8080" 2>/dev/null || \
	 xdg-open "http://localhost:8080" 2>/dev/null || \
	 echo "$(YELLOW)Please open http://localhost:8080 in your browser$(NC)"

# Pretty header
.PHONY: header
header:
	@echo ""
	@echo "$(PURPLE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(PURPLE)   Claude Code Memory Explorer$(NC)"
	@echo "$(PURPLE)   Beautiful Code Visualization & Search$(NC)"
	@echo "$(PURPLE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""

# Check prerequisites
.PHONY: check-prerequisites
check-prerequisites:
	@echo "$(BLUE)🔍 Checking prerequisites...$(NC)"
	@which docker > /dev/null 2>&1 || (echo "$(RED)❌ Docker not found. Please install Docker.$(NC)" && exit 1)
	@docker info > /dev/null 2>&1 || (echo "$(RED)❌ Docker daemon not running. Please start Docker.$(NC)" && exit 1)
	@echo "$(GREEN)✅ Prerequisites satisfied$(NC)"
	@echo ""

# Help command
.PHONY: help
help:
	@echo "$(PURPLE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(PURPLE)   Claude Code Memory Explorer - Commands$(NC)"
	@echo "$(PURPLE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(WHITE)Basic Commands:$(NC)"
	@echo "  $(CYAN)make$(NC)              Start the application (default)"
	@echo "  $(CYAN)make stop$(NC)         Stop all services"
	@echo "  $(CYAN)make restart$(NC)      Restart all services"
	@echo "  $(CYAN)make logs$(NC)         View logs (all services)"
	@echo "  $(CYAN)make status$(NC)       Check service status"
	@echo "  $(CYAN)make open$(NC)         Open in browser"
	@echo ""
	@echo "$(WHITE)Development:$(NC)"
	@echo "  $(CYAN)make dev$(NC)          Start with hot reload"
	@echo "  $(CYAN)make build$(NC)        Build Docker images"
	@echo "  $(CYAN)make rebuild$(NC)      Rebuild images (no cache)"
	@echo "  $(CYAN)make shell-[service]$(NC) Open shell in container"
	@echo ""
	@echo "$(WHITE)Maintenance:$(NC)"
	@echo "  $(CYAN)make clean$(NC)        Remove everything (⚠️  data loss)"
	@echo "  $(CYAN)make pull$(NC)         Update base images"
	@echo "  $(CYAN)make health-check$(NC) Check service health"
	@echo ""
	@echo "$(WHITE)Examples:$(NC)"
	@echo "  $(CYAN)make logs-backend$(NC) View backend logs only"
	@echo "  $(CYAN)make shell-backend$(NC) Open shell in backend"
	@echo "  $(CYAN)make index-sample$(NC) Index a sample project"
	@echo ""

# Default target
.DEFAULT_GOAL := run