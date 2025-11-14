# Duplicate Upload Protection Implementation

## Overview
This document describes the implementation of protection mechanisms to prevent data corruption and system issues when users attempt to upload files multiple times, either sequentially or concurrently.

## Problem Scenarios Addressed

### Scenario 1: Sequential Re-upload
- User uploads files, waits for completion, then uploads again
- **Solution**: System allows second upload after first ETL completes

### Scenario 2: Rapid Double Upload (Before ETL completes)
- User uploads files, then uploads again before ETL finishes
- **Risk**: File overwrite, race conditions, data corruption
- **Solution**: Second upload is rejected with clear message

### Scenario 3: Multiple Concurrent Users
- Multiple users try to upload simultaneously
- **Risk**: File conflicts, concurrent pipeline execution
- **Solution**: Only first upload proceeds, others are blocked

## Implementation Components

### 1. Backend Status Endpoint (`upload.py`)
**Added:** `GET /upload/status`

Returns system processing status by checking for `_complete` marker in MinIO landing bucket.

```python
{
    "is_processing": true/false,
    "message": "Status message",
    "status": "ready" or "processing"
}
```

### 2. Backend Upload Protection (`upload.py`)
**Modified:** `POST /upload/`

Before accepting files:
1. Checks for `_complete` marker in MinIO
2. If marker exists → Rejects upload with HTTP 409 Conflict
3. Provides clear error message with estimated wait time (2-5 minutes)

### 3. Backend Threading Lock (`handler.py`)
**Added:** Non-blocking threading lock in `PipelineEventHandler`

- Prevents concurrent ETL execution
- If pipeline is already running, duplicate trigger is ignored
- Lock is automatically released after pipeline completes (success or failure)

**Protection Timeline:**
```
Upload #1: Files → _complete → ETL starts (lock acquired)
Upload #2: Tries to start → Lock busy → Trigger skipped
ETL #1: Completes → Lock released → Bucket cleared
Upload #2 can now proceed
```

### 4. Frontend Status Polling (`DataUpload.tsx`)
**Added:** System status check every 5 seconds

- Polls `/upload/status` endpoint
- Updates UI state based on processing status
- Tracks processing duration in real-time

### 5. Frontend Processing Overlay (`DataUpload.tsx` & CSS)
**Added:** Full-screen processing overlay

**Features:**
- Blocks all UI interaction while processing
- Shows animated spinner
- Displays processing message
- Shows elapsed time (minutes:seconds)
- Automatically disappears when processing completes

**Visual Design:**
- Semi-transparent dark backdrop with blur effect
- White modal with rounded corners
- Blue spinning loader
- Clear, informative text

## Data Flow

### Normal Upload Flow
```
User selects files
    ↓
Frontend checks status (polling) → System ready ✓
    ↓
User clicks Upload
    ↓
Backend checks for _complete → Not found ✓
    ↓
Files uploaded to MinIO
    ↓
_complete marker created
    ↓
Frontend polling detects _complete → Shows overlay
    ↓
Observer detects trigger → Acquires lock
    ↓
ETL runs → Processes data → Clears bucket
    ↓
_complete marker removed
    ↓
Frontend polling detects removal → Hides overlay
    ↓
System ready for next upload
```

### Blocked Upload Flow
```
User A uploads files → ETL running
    ↓
User B opens upload page
    ↓
Frontend polling detects _complete → Shows overlay
    ↓
User B tries to upload (button disabled)
    ↓
If button somehow clicked → Backend rejects (409)
    ↓
ETL completes → _complete removed
    ↓
User B's overlay disappears → Can now upload
```

## Key Benefits

1. **✅ No Data Loss**: Files cannot be overwritten during processing
2. **✅ No Duplicates**: UPSERT logic + upload blocking prevents duplicate records
3. **✅ No Concurrent Execution**: Threading lock ensures one pipeline at a time
4. **✅ Clear User Feedback**: Real-time status with processing time
5. **✅ Automatic Recovery**: System unlocks after ETL completes (even on failure)
6. **✅ Cross-User Protection**: Overlay appears for all users when system is busy
7. **✅ No New Dependencies**: Uses existing MinIO, no Redis/database required

## Protection Levels

| Level | Component | Protection Against |
|-------|-----------|-------------------|
| Frontend | Polling + Overlay | Accidental clicks, user confusion |
| Backend API | Status check | Concurrent uploads, API abuse |
| Backend Handler | Threading lock | Concurrent pipeline execution |
| Database | UPSERT logic | Duplicate records |

## Estimated Wait Times

- **ETL only**: 30 seconds - 2 minutes (data dependent)
- **Full pipeline**: 5-10 minutes (includes MBA, PED, NLP, Holt-Winters)

Users are blocked only during ETL phase, as the landing bucket is cleared after ETL completes.

## Error Handling

### If ETL Fails
- Lock is released in `finally` block
- Trigger file is removed
- System becomes available for next upload
- User can retry immediately

### If Status Check Fails
- Frontend assumes "ready" state (fail-safe)
- Backend still enforces marker check
- Prevents system lockout due to polling errors

## Testing Scenarios

### Test 1: Sequential Upload
1. Upload files → Wait for completion
2. Upload again → Should succeed ✓

### Test 2: Rapid Upload
1. Upload files
2. Immediately try to upload again
3. Should see processing overlay and/or 409 error ✓

### Test 3: Concurrent Users
1. User A uploads
2. User B opens page while A's ETL is running
3. User B should see processing overlay ✓
4. After A's ETL completes, User B can upload ✓

### Test 4: Recovery from Failure
1. Upload files that cause ETL to crash
2. System should still clear lock and markers
3. Next upload should succeed ✓

## Files Modified

### Backend
- `backend/app/api/upload.py` - Added status endpoint and upload protection
- `backend/app/services/storage.py` - Added `check_processing_status()` function
- `backend/app/observer/handler.py` - Added threading lock

### Frontend
- `frontend/src/components/DataUpload.tsx` - Added polling and overlay
- `frontend/src/components/DataUpload.module.css` - Added overlay styles

## Configuration

No configuration changes required. System uses existing MinIO buckets and endpoints.

## Monitoring

Check logs for:
- `"Pipeline is already running. Skipping this trigger."` - Indicates duplicate trigger was blocked
- `"Upload rejected: Processing already in progress"` - Indicates upload was blocked
- `"Pipeline lock released"` - Indicates successful lock cleanup

## Future Enhancements (Optional)

1. Add Redis distributed lock for multi-server deployments
2. Add estimated completion time based on file size
3. Add progress bar showing ETL stages
4. Add notification when processing completes
5. Add manual override for admin users after timeout

