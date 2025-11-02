# Session Management End-to-End Testing Checklist

**Feature**: Phase 2 - Session Management Dashboard
**Date**: 2025-11-01
**Status**: Ready for Testing

## Prerequisites

1. Backend server running on port 12656
2. Frontend dev server running (`npm run dev`)
3. At least 5-10 test research sessions in database with varying:
   - Statuses (in_progress, completed, failed)
   - Languages (en, vi, es, etc.)
   - File counts
   - Some archived sessions

## Test Scenarios

### 1. Page Load and Initial State

- [ ] Navigate to `/sessions` route
- [ ] Verify page loads without errors
- [ ] Verify header shows "Session Management"
- [ ] Verify session count totals are displayed
- [ ] Verify default view mode is "grid"
- [ ] Verify sessions are displayed in grid cards
- [ ] Verify loading state appears briefly
- [ ] Verify no error state is shown

### 2. View Mode Toggle

#### Grid to List View
- [ ] Click "List View" button
- [ ] Verify view transitions to table layout
- [ ] Verify table headers are visible (checkbox, title, status, created, files, actions)
- [ ] Verify all sessions appear as table rows
- [ ] Verify button text changes to "Grid View"

#### List to Grid View
- [ ] Click "Grid View" button
- [ ] Verify view transitions back to grid cards
- [ ] Verify all sessions appear as cards
- [ ] Verify button text changes to "List View"

### 3. Session Display (Grid View)

For each session card, verify:
- [ ] Session title is displayed and truncated if too long
- [ ] Status badge shows correct color (blue=in_progress, green=completed, red=failed)
- [ ] Created date shows relative time (e.g., "2 hours ago")
- [ ] File count is displayed
- [ ] Total file size is displayed in human-readable format
- [ ] Language badge appears (if language set)
- [ ] Archived badge appears (if archived)
- [ ] Selection checkbox is visible in top-left
- [ ] "Quick View →" button is visible at bottom
- [ ] Action menu (⋮) button is visible

### 4. Session Display (List View)

For each session row, verify:
- [ ] Selection checkbox in first column
- [ ] Title in second column with archived badge if applicable
- [ ] Status badge in third column with correct color
- [ ] Created date in fourth column (relative time)
- [ ] File count in fifth column (with size if available)
- [ ] Action buttons in last column (duplicate, archive/restore, delete, view)
- [ ] Row highlights on hover
- [ ] Row background changes when selected

### 5. Session Selection

#### Single Selection
- [ ] Click checkbox on a session (grid or list view)
- [ ] Verify session is highlighted/outlined
- [ ] Verify bulk actions toolbar appears
- [ ] Verify "1 selected" is shown
- [ ] Click checkbox again to deselect
- [ ] Verify selection is removed
- [ ] Verify bulk actions toolbar disappears

#### Multiple Selection
- [ ] Select 3 different sessions
- [ ] Verify all 3 are highlighted
- [ ] Verify "3 selected" is shown
- [ ] Verify bulk actions toolbar shows archive/delete/clear buttons

#### Select All (List View Only)
- [ ] Switch to list view
- [ ] Click checkbox in table header
- [ ] Verify all visible sessions are selected
- [ ] Verify correct count is shown
- [ ] Click header checkbox again to deselect all

### 6. Quick View Modal

#### Opening Modal
- [ ] Click anywhere on a session card (grid view)
- [ ] Verify modal opens with smooth animation
- [ ] Verify modal backdrop appears (darkened background)
- [ ] Verify modal shows correct session title
- [ ] Verify status badge is displayed
- [ ] Verify language badge is displayed (if applicable)
- [ ] Verify archived badge is displayed (if archived)

#### Modal Tabs - Overview
- [ ] Verify "Overview" tab is active by default
- [ ] Verify session information section shows:
  - [ ] Session ID
  - [ ] Status
  - [ ] Created date (absolute and relative)
  - [ ] Last updated date
  - [ ] Archived date (if applicable)
  - [ ] Language
  - [ ] File count
  - [ ] Total size
- [ ] Verify research parameters section shows (if parameters exist):
  - [ ] All parameter key-value pairs
  - [ ] Proper formatting

#### Modal Tabs - Files
- [ ] Click "Files" tab
- [ ] Verify tab becomes active
- [ ] Verify file count is shown in tab title
- [ ] Verify placeholder message is displayed
- [ ] Verify "View Full Session" button is present

#### Modal Tabs - Logs
- [ ] Click "Logs" tab
- [ ] Verify tab becomes active
- [ ] Verify placeholder message about execution logs is shown

#### Modal Tabs - Metadata
- [ ] Click "Metadata" tab
- [ ] Verify tab becomes active
- [ ] Verify JSON parameters are displayed in code block
- [ ] Verify syntax highlighting (green text on dark background)
- [ ] Verify JSON is properly formatted with indentation

#### Modal Actions - Duplicate
- [ ] Click "Duplicate" button in modal footer
- [ ] Verify modal closes
- [ ] Verify navigation to new session (or stays on dashboard)
- [ ] Verify toast notification appears
- [ ] Verify sessions list refreshes
- [ ] Verify new duplicated session appears in list

#### Modal Actions - Archive (Non-Archived Session)
- [ ] Open modal for non-archived session
- [ ] Click "Archive" button
- [ ] Verify confirmation dialog appears
- [ ] Click "OK" in confirmation
- [ ] Verify modal closes
- [ ] Verify toast notification appears
- [ ] Verify session is removed from active list (if "Show Archived" is off)

#### Modal Actions - Restore (Archived Session)
- [ ] Enable "Show Archived" filter
- [ ] Open modal for archived session
- [ ] Verify "Restore" button is shown (not "Archive")
- [ ] Click "Restore" button
- [ ] Verify modal closes
- [ ] Verify toast notification appears
- [ ] Verify session appears in active list

#### Modal Actions - Delete
- [ ] Click "Delete" button in modal footer
- [ ] Verify confirmation dialog with strong warning
- [ ] Click "Cancel" to test cancellation
- [ ] Verify modal stays open
- [ ] Click "Delete" again and confirm with "OK"
- [ ] Verify modal closes
- [ ] Verify toast notification appears
- [ ] Verify session is removed from list

#### Modal Closing
- [ ] Click "Close" button in footer
- [ ] Verify modal closes with animation
- [ ] Click backdrop (outside modal) to open again
- [ ] Click anywhere on backdrop
- [ ] Verify modal closes
- [ ] Open modal again
- [ ] Press Escape key
- [ ] Verify modal closes

### 7. Session Actions (Grid View - Action Menu)

#### Open Action Menu
- [ ] Click action menu (⋮) button on a session card
- [ ] Verify dropdown menu appears
- [ ] Verify menu shows: Full Details, Duplicate, Archive/Restore, Delete

#### Full Details Navigation
- [ ] Click "Full Details" in action menu
- [ ] Verify navigation to `/sessions/{session-id}`
- [ ] (Note: This route may show placeholder for now)

#### Duplicate from Menu
- [ ] Return to sessions dashboard
- [ ] Open action menu
- [ ] Click "Duplicate"
- [ ] Verify same behavior as modal duplicate button

#### Archive from Menu
- [ ] Open action menu for non-archived session
- [ ] Click "Archive"
- [ ] Verify confirmation appears
- [ ] Confirm
- [ ] Verify session is archived

#### Restore from Menu
- [ ] Enable "Show Archived"
- [ ] Open action menu for archived session
- [ ] Verify "Restore" option is shown
- [ ] Click "Restore"
- [ ] Verify session is restored

#### Delete from Menu
- [ ] Open action menu
- [ ] Click "Delete"
- [ ] Verify confirmation with warning
- [ ] Confirm
- [ ] Verify session is deleted

### 8. Session Actions (List View - Icon Buttons)

Verify all icon buttons work in list view:
- [ ] Duplicate button (📋 icon) - same as grid view
- [ ] Archive button (📦 icon) - same as grid view
- [ ] Restore button (🔄 icon) - shown for archived sessions
- [ ] Delete button (🗑️ icon) - same as grid view
- [ ] View button (👁️ icon) - opens quick view modal

### 9. Filters

#### Show Archived Toggle
- [ ] Verify checkbox is unchecked by default
- [ ] Verify only active sessions are shown
- [ ] Check "Show Archived" checkbox
- [ ] Verify archived sessions appear in list
- [ ] Verify archived sessions have "Archived" badge
- [ ] Uncheck "Show Archived"
- [ ] Verify archived sessions disappear

#### Status Filter
- [ ] Select "In Progress" from status dropdown
- [ ] Verify only in_progress sessions are shown
- [ ] Verify session count updates
- [ ] Select "Completed"
- [ ] Verify only completed sessions are shown
- [ ] Select "Failed"
- [ ] Verify only failed sessions are shown
- [ ] Select "All Statuses"
- [ ] Verify all sessions are shown again

#### Combined Filters
- [ ] Enable "Show Archived"
- [ ] Select "Completed" status
- [ ] Verify only completed sessions (archived + active) are shown
- [ ] Change to "In Progress" while archived is still enabled
- [ ] Verify filtering works correctly

#### Reset Filters
- [ ] Apply multiple filters (archived + status)
- [ ] Click "Reset Filters" button
- [ ] Verify all filters are cleared
- [ ] Verify "Show Archived" is unchecked
- [ ] Verify status is "All Statuses"
- [ ] Verify all active sessions are shown

### 10. Bulk Operations

#### Bulk Archive
- [ ] Select 3 non-archived sessions
- [ ] Click "Archive Selected" in bulk actions toolbar
- [ ] Verify confirmation shows correct count (3)
- [ ] Confirm
- [ ] Verify all 3 sessions are archived
- [ ] Verify toast notification appears
- [ ] Verify sessions disappear if "Show Archived" is off

#### Bulk Delete
- [ ] Select 2 sessions
- [ ] Click "Delete Selected" in bulk actions toolbar
- [ ] Verify confirmation with strong warning
- [ ] Confirm
- [ ] Verify both sessions are deleted
- [ ] Verify toast notification appears
- [ ] Verify sessions are removed from list

#### Clear Selection
- [ ] Select several sessions
- [ ] Click "Clear" button in bulk actions toolbar
- [ ] Verify all selections are removed
- [ ] Verify bulk actions toolbar disappears

### 11. Pagination

#### Basic Pagination
- [ ] Verify pagination controls at bottom show:
  - [ ] "Showing X-Y of Z sessions"
  - [ ] "Previous" button (disabled on page 1)
  - [ ] Page counter "Page 1 of N"
  - [ ] "Next" button (enabled if more pages)

#### Navigate Pages
- [ ] Click "Next" button
- [ ] Verify page counter increments
- [ ] Verify new sessions are loaded
- [ ] Verify "Previous" button is now enabled
- [ ] Click "Previous" button
- [ ] Verify page counter decrements
- [ ] Verify previous sessions are shown
- [ ] Navigate to last page
- [ ] Verify "Next" button is disabled

#### Pagination with Filters
- [ ] Apply a filter that reduces total count
- [ ] Verify pagination updates to show new total
- [ ] Verify correct number of pages
- [ ] Reset filters
- [ ] Verify pagination resets to page 1

### 12. Loading States

- [ ] Refresh page
- [ ] Verify loading spinner appears briefly
- [ ] Verify "Loading sessions..." text is shown
- [ ] Wait for sessions to load
- [ ] Verify spinner disappears
- [ ] Verify sessions appear

### 13. Empty States

#### No Sessions
- [ ] (If possible) Test with empty database or filters that return no results
- [ ] Verify empty state message appears
- [ ] Verify folder icon (📁) is shown
- [ ] Verify "No Sessions Found" heading
- [ ] Verify descriptive message
- [ ] Verify "Start New Research" button
- [ ] Click "Start New Research"
- [ ] Verify navigation to home page

### 14. Error States

#### Network Error Simulation
- [ ] Stop backend server
- [ ] Refresh sessions page
- [ ] Verify error state appears
- [ ] Verify error icon is shown
- [ ] Verify "Failed to Load Sessions" heading
- [ ] Verify error message is displayed
- [ ] Verify "Retry" button is visible
- [ ] Restart backend server
- [ ] Click "Retry" button
- [ ] Verify sessions load successfully

### 15. Responsive Design

#### Desktop (1920x1080)
- [ ] Verify grid shows 3 columns
- [ ] Verify all elements are properly spaced
- [ ] Verify table is fully visible in list view

#### Tablet (768x1024)
- [ ] Resize window or use responsive mode
- [ ] Verify grid shows 2 columns
- [ ] Verify table scrolls horizontally if needed

#### Mobile (375x667)
- [ ] Resize to mobile width
- [ ] Verify grid shows 1 column
- [ ] Verify cards are full width
- [ ] Verify modal is responsive
- [ ] Verify buttons stack properly

### 16. Accessibility

- [ ] Test keyboard navigation:
  - [ ] Tab through all interactive elements
  - [ ] Verify focus indicators are visible
  - [ ] Verify Escape key closes modal
  - [ ] Verify Enter key activates buttons
- [ ] Test with screen reader (if available):
  - [ ] Verify session information is announced
  - [ ] Verify button purposes are clear
  - [ ] Verify status changes are announced

### 17. Performance

- [ ] Load page with 100+ sessions
- [ ] Verify page loads within 2 seconds
- [ ] Verify scrolling is smooth
- [ ] Verify no lag when switching views
- [ ] Verify no lag when opening modal
- [ ] Verify pagination limits results to 20 per page

### 18. Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (if on macOS)
- [ ] Edge

Verify all features work consistently across browsers.

## Bug Report Template

If any issues are found during testing:

```markdown
**Issue**: [Brief description]
**Severity**: Critical | High | Medium | Low
**Steps to Reproduce**:
1.
2.
3.

**Expected Behavior**:
**Actual Behavior**:
**Browser**:
**Screenshot**: (if applicable)
```

## Testing Completion

After completing all tests:

- [ ] All critical features work correctly
- [ ] All bugs are documented
- [ ] High-priority bugs are fixed
- [ ] Feature is ready for production deployment

---

**Tested By**: _________________
**Date**: _________________
**Overall Status**: ☐ Pass | ☐ Pass with Minor Issues | ☐ Fail
