#!/bin/bash

# Script to install pgvector extension for Odoo 19 AI module
# Usage: sudo ./install_pgvector_odoo19.sh [database_name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Odoo 19 AI Module - pgvector Extension Installer ===${NC}\n"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./install_pgvector_odoo19.sh [database_name]"
    exit 1
fi

# List all databases first
echo -e "${YELLOW}Available PostgreSQL databases:${NC}"
su - postgres -c "psql -l" | grep -E "^\s" | head -20
echo ""

# Get database name
if [ -z "$1" ]; then
    echo -e "${YELLOW}Please enter your Odoo database name (from the list above):${NC}"
    read -p "Database name: " DBNAME
else
    DBNAME=$1
fi

if [ -z "$DBNAME" ]; then
    echo -e "${RED}Error: Database name is required${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking if database '$DBNAME' exists...${NC}"
DB_EXISTS=$(su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='$DBNAME'\"")

if [ "$DB_EXISTS" != "1" ]; then
    echo -e "${RED}Error: Database '$DBNAME' does not exist${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database '$DBNAME' found${NC}"

# Check if pgvector is already installed
echo -e "\n${YELLOW}Checking if pgvector extension exists in '$DBNAME'...${NC}"
EXTENSION_EXISTS=$(su - postgres -c "psql -d $DBNAME -tAc \"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');\"")

if [ "$EXTENSION_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ pgvector extension is already installed!${NC}"
    echo -e "${BLUE}You can now install the Odoo AI module.${NC}"
    exit 0
fi

# Check if pgvector is available in the system
echo -e "\n${YELLOW}Checking if pgvector is installed on the system...${NC}"
PGVECTOR_AVAILABLE=$(su - postgres -c "psql -d $DBNAME -tAc \"SELECT 1 FROM pg_available_extensions WHERE name = 'vector';\"" || echo "")

if [ -z "$PGVECTOR_AVAILABLE" ]; then
    echo -e "${RED}✗ pgvector is not installed on your system${NC}"
    echo -e "${YELLOW}Please install pgvector first:${NC}"
    echo -e "${BLUE}Ubuntu/Debian:${NC}"
    echo "  sudo apt-get install postgresql-server-dev-all git build-essential"
    echo "  git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git"
    echo "  cd pgvector"
    echo "  make"
    echo "  sudo make install"
    echo ""
    echo -e "${BLUE}More info: https://github.com/pgvector/pgvector${NC}"
    exit 1
fi

# Install pgvector extension
echo -e "\n${YELLOW}Installing pgvector extension in database '$DBNAME'...${NC}"
su - postgres -c "psql -d $DBNAME -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

# Verify installation
EXTENSION_EXISTS=$(su - postgres -c "psql -d $DBNAME -tAc \"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');\"")

if [ "$EXTENSION_EXISTS" = "t" ]; then
    echo -e "\n${GREEN}✓✓✓ Success! pgvector extension installed in '$DBNAME'!${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Restart Odoo: sudo systemctl restart odoo19"
    echo "  2. Go to Apps menu in Odoo"
    echo "  3. Search for 'AI' and install the module"
else
    echo -e "\n${RED}✗ Failed to install pgvector extension${NC}"
    exit 1
fi
