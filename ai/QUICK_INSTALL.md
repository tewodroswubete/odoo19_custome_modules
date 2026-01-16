# Quick Install Guide - pgvector for Odoo 19 AI Module

## Your Configuration

- **Odoo Path:** `/opt/odoo19`
- **Config File:** `/etc/odoo/odoo19.conf`
- **Service Name:** `odoo19`
- **DB User:** `odoo19`
- **Addons Path:** `/opt/odoo19/odoo/addons,/opt/odoo19/custom_addons`
- **Sudo Password:** `thanks to god`

## Quick Installation Steps

### Step 1: Run the Installation Script

```bash
sudo /opt/odoo19/custom-addons/ai/install_pgvector_odoo19.sh
```

The script will:
1. Show you all available databases
2. Ask you to enter your database name
3. Install the pgvector extension
4. Verify the installation

### Step 2: Restart Odoo

```bash
sudo systemctl restart odoo19
```

### Step 3: Install AI Module

1. Go to `http://localhost:8073` (or your Odoo URL)
2. Go to **Apps** menu
3. Remove "Apps" filter to see all modules
4. Search for "AI"
5. Click **Install** on the AI module

## If You Don't Know Your Database Name

### Option 1: Check Odoo Logs

```bash
tail -f /var/log/odoo/odoo19-server.log | grep database
```

### Option 2: List All Databases

```bash
echo "thanks to god" | sudo -S -u postgres psql -l | grep odoo
```

### Option 3: Check Through Odoo Web Interface

1. Go to `http://localhost:8073/web/database/manager`
2. Enter admin password: `teddy`
3. You'll see all databases listed

## Manual Installation (If Script Fails)

If you know your database name (e.g., `my_odoo_db`), run:

```bash
echo "thanks to god" | sudo -S -u postgres psql -d my_odoo_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## Troubleshooting

### Error: "pgvector is not available on system"

Install pgvector on your Ubuntu/Debian system:

```bash
sudo apt-get install postgresql-server-dev-all git build-essential
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

Then run the installation script again.

### Error: "permission denied"

Make sure you're using `sudo`:

```bash
sudo /opt/odoo19/custom-addons/ai/install_pgvector_odoo19.sh
```

### Verify Installation

Check if pgvector is installed in your database:

```bash
echo "thanks to god" | sudo -S -u postgres psql -d YOUR_DATABASE_NAME -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## What Changed in the AI Module

The AI module (`/opt/odoo19/custom-addons/ai/__init__.py`) now:

✅ Checks if pgvector extension exists before trying to create it
✅ Provides helpful error messages with your database name
✅ Shows clear installation instructions if permission denied
✅ Logs all actions for debugging

## Need Help?

1. Check Odoo logs: `tail -f /var/log/odoo/odoo19-server.log`
2. Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*-main.log`
3. Test database connection: `psql -U odoo19 -l`

## More Information

- pgvector: https://github.com/pgvector/pgvector
- Odoo AI Module: https://www.odoo.com/documentation/19.0/developer/reference/backend/ai.html
