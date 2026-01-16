# pgvector Extension Setup for Odoo AI Module

## Problem

When installing the Odoo AI module, you may encounter this error:

```
psycopg2.errors.InsufficientPrivilege: permission denied to create extension "vector"
HINT: Must be superuser to create this extension.
```

This happens because the Odoo database user doesn't have superuser privileges in PostgreSQL.

## Solution

You need to install the pgvector extension manually as the PostgreSQL superuser before installing the AI module.

### Method 1: Using the Helper Script (Recommended)

Run the provided installation script:

```bash
sudo /opt/odoo19/custom-addons/ai/install_pgvector.sh your_database_name
```

Or run it interactively:

```bash
sudo /opt/odoo19/custom-addons/ai/install_pgvector.sh
```

The script will prompt you for the database name.

### Method 2: Manual Installation

#### Step 1: Find your database name

If you don't know your database name, list all databases:

```bash
sudo -u postgres psql -l
```

#### Step 2: Install the extension

Replace `your_database_name` with your actual Odoo database name:

```bash
sudo -u postgres psql -d your_database_name -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Or connect to PostgreSQL and run the command:

```bash
sudo -u postgres psql
\c your_database_name
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

#### Step 3: Verify installation

Check if the extension was installed successfully:

```bash
sudo -u postgres psql -d your_database_name -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Method 3: Install pgvector on System

If pgvector is not installed on your system, you need to install it first:

#### Ubuntu/Debian:

```bash
sudo apt-get install postgresql-server-dev-all
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

Then follow Method 1 or Method 2 above.

#### Using Docker:

If you're using PostgreSQL in Docker, use a PostgreSQL image with pgvector:

```bash
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_PASSWORD=odoo \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_DB=odoo \
  -p 5432:5432 \
  ankane/pgvector:latest
```

## After Installation

Once the pgvector extension is installed:

1. Restart your Odoo server
2. Install the AI module through Odoo's Apps menu
3. The module will detect that pgvector is already installed and proceed normally

## Verification

The modified AI module now:
- ✅ Checks if the extension exists before trying to create it
- ✅ Provides clear error messages with installation instructions
- ✅ Shows the database name in the error message
- ✅ Logs helpful information for debugging

## More Information

- pgvector documentation: https://github.com/pgvector/pgvector
- Odoo AI module documentation: https://www.odoo.com/documentation/19.0/developer/reference/backend/ai.html
