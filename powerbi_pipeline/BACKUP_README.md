# Manual Tag Overrides Backup System

## What Happened
The `create_sqlite_db.py` script completely recreates the database from CSV files, which unfortunately deleted all manual tag overrides that were stored in a custom `ManualTagOverrides` table.

## Prevention System
I've implemented an automatic backup and restore system:

### 1. Backup Script (`backup_manual_overrides.py`)
- Automatically backs up the `ManualTagOverrides` table before database recreation
- Creates timestamped backup files: `ManualTagOverrides_backup_YYYYMMDD_HHMMSS.csv`
- Always maintains a latest backup: `ManualTagOverrides_latest.csv`

### 2. Modified Database Creation (`create_sqlite_db.py`)
- Now automatically backs up manual overrides before deleting the database
- Recreates the `ManualTagOverrides` table structure after importing CSVs
- Automatically restores manual overrides from the latest backup

## How to Use

### Manual Backup (before risky operations)
```bash
cd /Users/strattoncarroll/Documents/survey-model/powerbi_pipeline
python backup_manual_overrides.py
```

### Manual Restore (if needed)
```bash
# Restore from latest backup
python backup_manual_overrides.py restore

# Restore from specific backup file
python backup_manual_overrides.py restore ManualTagOverrides_backup_20250904_164500.csv
```

### Safe Database Recreation
The `create_sqlite_db.py` script now automatically handles backups:
```bash
python create_sqlite_db.py
```

## Backup Files Location
All backup files are stored in: `/Users/strattoncarroll/Documents/survey-model/powerbi_data_model_v2/`

## Recovery Options
Unfortunately, the data that was lost today (Sept 4, 2025 at 11:46 AM) cannot be automatically recovered because:
1. No backup existed at the time
2. The `ManualTagOverrides` table wasn't part of the CSV export process
3. SQLite doesn't maintain transaction logs by default

## Future Safety
From now on, the system will automatically:
1. ✅ Backup manual overrides before any database recreation
2. ✅ Recreate the ManualTagOverrides table structure
3. ✅ Restore manual overrides from backup
4. ✅ Maintain timestamped backup history

**IMPORTANT**: Always run `python backup_manual_overrides.py` before any major database operations!