#!/bin/bash

# Script to install pgvector extension for Odoo AI module
# Usage: sudo ./install_pgvector.sh [database_name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Odoo AI Module - pgvector Extension Installer ===${NC}\n"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./install_pgvector.sh [database_name]"
    exit 1
fi

# Get database name
if [ -z "$1" ]; then
    echo -e "${YELLOW}Please enter your Odoo database name:${NC}"
    read -p "Database name: " DBNAME
else
    DBNAME=$1
fi

if [ -z "$DBNAME" ]; then
    echo -e "${RED}Error: Database name is required${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Checking if database exists...${NC}"
DB_EXISTS=$(su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='$DBNAME'\"")

if [ "$DB_EXISTS" != "1" ]; then
    echo -e "${RED}Error: Database '$DBNAME' does not exist${NC}"
    echo -e "${YELLOW}Available databases:${NC}"
    su - postgres -c "psql -l"
    exit 1
fi

echo -e "${GREEN}Database '$DBNAME' found${NC}"

# Check if pgvector is already installed
echo -e "\n${YELLOW}Checking if pgvector extension exists...${NC}"
EXTENSION_EXISTS=$(su - postgres -c "psql -d $DBNAME -tAc \"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');\"")

if [ "$EXTENSION_EXISTS" = "t" ]; then
    echo -e "${GREEN}pgvector extension is already installed!${NC}"
    exit 0
fi

# Install pgvector extension
echo -e "\n${YELLOW}Installing pgvector extension...${NC}"
su - postgres -c "psql -d $DBNAME -c 'CREATE EXTENSION IF NOT EXISTS vector;'"

# Verify installation
EXTENSION_EXISTS=$(su - postgres -c "psql -d $DBNAME -tAc \"SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');\"")

if [ "$EXTENSION_EXISTS" = "t" ]; then
    echo -e "\n${GREEN}✓ pgvector extension successfully installed!${NC}"
    echo -e "${GREEN}You can now install the Odoo AI module.${NC}"
else
    echo -e "\n${RED}✗ Failed to install pgvector extension${NC}"
    echo -e "${YELLOW}Please check if pgvector is installed on your system.${NC}"
    echo -e "${YELLOW}Installation instructions: https://github.com/pgvector/pgvector${NC}"
    exit 1
fi
