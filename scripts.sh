#!/bin/bash
# Comandos úteis para o projeto NDVI Calculator

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌱 NDVI Calculator - Comandos Úteis${NC}\n"

# Função para mostrar comando e executar
run_command() {
    echo -e "${GREEN}$1${NC}"
    echo -e "${YELLOW}Comando: $2${NC}\n"
}

case "$1" in
    "install")
        run_command "📦 Instalar dependências" "uv sync"
        uv sync
        ;;
    
    "run")
        run_command "🚀 Executar aplicação web" "uv run python main.py"
        uv run python main.py
        ;;
    
    "example")
        run_command "📝 Executar exemplos" "uv run python examples/example_usage.py"
        uv run python examples/example_usage.py
        ;;
    
    "test")
        run_command "🧪 Executar testes" "uv run pytest"
        uv run pytest
        ;;
    
    "test-cov")
        run_command "📊 Executar testes com cobertura" "uv run pytest --cov=src --cov-report=html"
        uv run pytest --cov=src --cov-report=html
        echo -e "\n${GREEN}Relatório disponível em: htmlcov/index.html${NC}"
        ;;
    
    "format")
        run_command "🎨 Formatar código" "uv run black src/ && uv run isort src/"
        uv run black src/ tests/ examples/
        uv run isort src/ tests/ examples/
        ;;
    
    "lint")
        run_command "🔍 Verificar tipos" "uv run mypy src/"
        uv run mypy src/
        ;;
    
    "check")
        run_command "✅ Verificar instalação" "uv run python check_setup.py"
        uv run python check_setup.py
        ;;
    
    "clean")
        run_command "🧹 Limpar cache e outputs" "rm -rf __pycache__ .pytest_cache htmlcov outputs/*"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
        rm -rf .pytest_cache htmlcov .mypy_cache
        echo -e "${GREEN}Cache limpo!${NC}"
        ;;
    
    *)
        echo "Uso: ./scripts.sh [comando]"
        echo ""
        echo "Comandos disponíveis:"
        echo "  install    - Instalar dependências"
        echo "  run        - Executar aplicação web"
        echo "  example    - Executar exemplos"
        echo "  test       - Executar testes"
        echo "  test-cov   - Executar testes com cobertura"
        echo "  format     - Formatar código (black + isort)"
        echo "  lint       - Verificar tipos (mypy)"
        echo "  check      - Verificar instalação"
        echo "  clean      - Limpar cache e outputs"
        echo ""
        echo "Exemplos:"
        echo "  ./scripts.sh run"
        echo "  ./scripts.sh test"
        echo "  ./scripts.sh format"
        ;;
esac
