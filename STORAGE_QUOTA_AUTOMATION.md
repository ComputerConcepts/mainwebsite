# Storage Quota Update Automation

## Overview
The `update_storage_quotas.py` script automatically recalculates and updates storage quotas for all users based on current VM capacity, ensuring optimal storage allocation.

## Script Features
- **Dynamic Quota Calculation**: Automatically allocates available VM storage among active users
- **Reserves 1GB**: Always keeps 1GB free for website operations  
- **Logging**: Creates detailed logs in `storage_quota_updates.log`
- **Dry Run Mode**: Test changes without applying them
- **Verbose Output**: Detailed system statistics

## Usage

### Basic Update (Run this hourly)
```bash
python update_storage_quotas.py
```

### Test Mode (Check what would change)
```bash
python update_storage_quotas.py --dry-run --verbose
```

### Verbose Mode (Show detailed statistics)
```bash
python update_storage_quotas.py --verbose
```

## Setting Up Hourly Automation

### Option 1: Windows Task Scheduler
1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task > Name: "Storage Quota Update"
3. Trigger: Daily, repeat every 1 hour
4. Action: Start a program
   - Program: `C:\Users\gauba\Downloads\computer concepts\venv\Scripts\python.exe`
   - Arguments: `update_storage_quotas.py`
   - Start in: `C:\Users\gauba\Downloads\computer concepts`

### Option 2: PowerShell Scheduled Job
```powershell
# Create a scheduled job that runs every hour
$trigger = New-JobTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue) -Once -At (Get-Date)
$action = {
    Set-Location "C:\Users\gauba\Downloads\computer concepts"
    & "C:\Users\gauba\Downloads\computer concepts\venv\Scripts\python.exe" update_storage_quotas.py
}
Register-ScheduledJob -Name "StorageQuotaUpdate" -ScriptBlock $action -Trigger $trigger
```

### Option 3: Manual Cron-like Setup
Create a PowerShell script that runs continuously:
```powershell
# continuous_quota_update.ps1
while ($true) {
    Set-Location "C:\Users\gauba\Downloads\computer concepts"
    & "C:\Users\gauba\Downloads\computer concepts\venv\Scripts\python.exe" update_storage_quotas.py
    Start-Sleep -Seconds 3600  # Sleep for 1 hour
}
```

## What the Script Does
1. **Calculates Available Storage**: VM total - used - 1GB reserved
2. **Counts Active Users**: Only includes active employee accounts
3. **Allocates Quotas**: Divides available storage equally among users
4. **Updates Database**: Sets new quota for each user
5. **Logs Results**: Records timestamp, user count, and new quotas

## Monitoring
- Check `storage_quota_updates.log` for execution history
- Use `--verbose` flag to see detailed system statistics
- Use `--dry-run` to preview changes before applying

## Benefits of Hourly Updates
- **Automatic Scaling**: As users join/leave, quotas adjust automatically
- **Optimal Resource Usage**: Always uses maximum available storage
- **Fair Distribution**: Equal allocation ensures no user gets unfair advantage
- **System Protection**: Maintains 1GB buffer for website operations
