# Plan: Implement "Change Tracking Path" feature

## Overview
Allow users to change the `executable_path` (tracking target) of a watched application without affecting its `application_id`, historical data, `executable_name`, `launch_path`, or other metadata.

## Decisions (confirmed)
1. Dead-letter queue: batch-replace old path with new path in both queue files
2. Conflict detection: reject with QMessageBox if new path is already used
3. Monitor refresh: full refresh via existing `_refresh_monitor_list()` / `update_watch_list()`
4. `executable_name`: keep unchanged (user-custom display name)

## File Changes

### 1. `client/db/repository.py` - DONE
Added `change_tracking_path(old_path, new_path) -> Tuple[bool, str]` + `_refresh_failed_queues()` helper.

### 2. `client/ui/dialogs.py` - TODO
- Change "进程路径:" label to "追踪进程:"
- Add "更换" button next to the path label
- Add `needs_monitor_refresh` flag in `__init__`
- Add `_on_change_tracking_path()` method

### 3. `client/ui/window.py` - TODO
- In `_on_detail_requested`: after `dialog.exec()`, check `needs_monitor_refresh` and call `_refresh_monitor_list()`

### 4. `client/main.py` - already done (translator fix)

## Remaining work
- [ ] dialogs.py: replace process path row with tracking path + button
- [ ] dialogs.py: add `needs_monitor_refresh` flag
- [ ] dialogs.py: add `_on_change_tracking_path()` method
- [ ] window.py: check `needs_monitor_refresh` after dialog close
- [ ] Verify compile + runtime tests