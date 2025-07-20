# AI Analysis Background Processing Setup

This document explains how to set up background processing for AI file analysis using the new queue system.

## Overview

The AI analysis system has been updated to use a queue-based background processing approach. When users request AI analysis of files, they are now queued in the database and processed by a separate background script.

## Components

### 1. Database Queue System
- **AIFileAnalysis Model**: Enhanced with queue status tracking
- **Status Values**: `queued`, `processing`, `completed`, `failed`, `retrying`
- **Priority System**: Higher priority analyses are processed first
- **Retry Logic**: Failed analyses can be automatically retried up to 3 times

### 2. Background Processor Script
- **File**: `background_ai_processor.py`
- **Purpose**: Processes queued analyses in the background
- **Features**: 
  - Batch processing
  - Continuous monitoring mode
  - Timeout handling
  - Retry management
  - Logging

### 3. PythonAnywhere Scheduler
- **File**: `pythonanywhere_scheduler.py`
- **Purpose**: Optimized for PythonAnywhere's task scheduling system
- **Features**: 
  - Conservative resource usage
  - Batch processing (3 files at a time)
  - Comprehensive logging

## Setup Instructions

### For PythonAnywhere

1. **Upload the files** to your PythonAnywhere account:
   ```
   /home/yourusername/computer-concepts/background_ai_processor.py
   /home/yourusername/computer-concepts/pythonanywhere_scheduler.py
   ```

2. **Update the paths** in `pythonanywhere_scheduler.py`:
   ```python
   project_path = '/home/yourusername/computer-concepts'  # Update this
   logging.FileHandler('/home/yourusername/ai_processing.log'),  # Update this
   ```

3. **Set up a scheduled task** in the PythonAnywhere dashboard:
   - Go to: Dashboard → Tasks
   - Command: `python3.10 /home/yourusername/computer-concepts/pythonanywhere_scheduler.py`
   - Schedule: Every 5-10 minutes (adjust based on your needs)

4. **Run migrations** to update the database:
   ```bash
   python manage.py migrate
   ```

### For Other Hosting Providers

1. **Set up a cron job** to run the background processor:
   ```bash
   # Run every 5 minutes
   */5 * * * * cd /path/to/your/project && python background_ai_processor.py --mode batch --batch-size 5
   ```

2. **Or run in continuous mode** (requires process management):
   ```bash
   python background_ai_processor.py --mode continuous --interval 30
   ```

### For Local Development

1. **Run the processor manually**:
   ```bash
   # Process one analysis
   python background_ai_processor.py --mode single
   
   # Process a batch
   python background_ai_processor.py --mode batch --batch-size 3
   
   # Run continuously (press Ctrl+C to stop)
   python background_ai_processor.py --mode continuous --interval 10
   ```

## Usage

### For Users
1. Upload a file through the file manager
2. Click "Analyze with AI" - the file will be queued
3. Check the analysis status in the AI dashboard
4. View completed analyses in the file analysis section

### For Administrators
1. Access the **AI Queue Dashboard** at `/employee/ai/queue/`
2. Monitor queue statistics and processing status
3. Retry failed analyses
4. View processing logs

## Queue Dashboard Features

- **Real-time Statistics**: See queued, processing, completed, and failed counts
- **Currently Processing**: View files being processed right now
- **Failed Analyses**: See failed analyses that can be retried
- **Recent Activity**: Monitor recent processing history
- **Auto-refresh**: Enable automatic page refresh every 30 seconds
- **Retry Functionality**: Manually retry failed analyses

## API Endpoints

- `POST /api/ai/analyze-file/<file_id>/` - Queue a file for analysis
- `GET /api/ai/analysis-status/<analysis_id>/` - Check analysis status
- `POST /api/ai/retry-analysis/<analysis_id>/` - Retry a failed analysis

## Configuration Options

### Background Processor Settings
```python
# In background_ai_processor.py
max_concurrent = 3      # Maximum simultaneous analyses
process_timeout = 300   # Timeout per analysis (seconds)
```

### PythonAnywhere Settings
```python
# In pythonanywhere_scheduler.py
max_concurrent = 2      # Lower for shared hosting
process_timeout = 180   # 3 minutes timeout
batch_size = 3          # Process 3 files per run
```

## Monitoring and Logs

### Log Files
- **ai_processing.log**: Main processing log
- **Django logs**: Standard Django logging for web requests

### Log Entries Include
- Analysis start/completion times
- Processing duration
- Error messages for failed analyses
- Queue statistics
- Performance metrics

### Example Log Entries
```
2025-07-20 10:30:15 - INFO - Starting analysis of file: document.pdf (ID: 123)
2025-07-20 10:30:45 - INFO - Completed analysis of document.pdf in 30245ms
2025-07-20 10:31:00 - INFO - Queue status: {'queued': 5, 'processing': 1, 'completed': 156, 'failed': 2}
```

## Troubleshooting

### Common Issues

1. **Files not being processed**:
   - Check if the background processor is running
   - Verify the scheduled task is active
   - Check log files for errors

2. **Analyses failing**:
   - Check file permissions
   - Verify file paths are correct
   - Review error messages in the queue dashboard

3. **Performance issues**:
   - Reduce batch size
   - Increase processing timeout
   - Check server resources

### Manual Recovery

If analyses get stuck in "processing" state:
```python
# Run in Django shell
from pages.models import AIFileAnalysis
from django.utils import timezone
from datetime import timedelta

# Find stale analyses
stale = AIFileAnalysis.objects.filter(
    status='processing',
    processing_started_at__lt=timezone.now() - timedelta(minutes=10)
)

# Reset them to queued
for analysis in stale:
    analysis.status = 'queued'
    analysis.processing_started_at = None
    analysis.save()
```

## Security Considerations

- Background processor runs with Django's security settings
- File access is restricted to uploaded files only
- Analysis results are stored securely in the database
- User permissions are respected for analysis access

## Performance Tips

1. **Optimize for your hosting environment**:
   - PythonAnywhere: Use smaller batch sizes (2-3 files)
   - VPS/Dedicated: Can handle larger batches (5-10 files)

2. **Schedule appropriately**:
   - High traffic sites: Every 2-5 minutes
   - Low traffic sites: Every 10-15 minutes

3. **Monitor resource usage**:
   - Watch CPU and memory consumption
   - Adjust batch sizes based on available resources

## Future Enhancements

Potential improvements for the queue system:
- Priority levels for different user types
- Webhook notifications for completed analyses
- Bulk analysis operations
- Queue analytics and reporting
- Integration with external AI services
