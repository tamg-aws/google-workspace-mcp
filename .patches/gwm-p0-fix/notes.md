# GWM P0 fix — notes (2026-04-25)

Branch: `fix/gwm-p0-scope-hardening`
Base: `be2a46d` on `main`

## Findings addressed
- **GWM-01 (P0)** — Scope-gated tool registration
- **GWM-02 (P0)** — `gmail_create_filter` action allowlist

## Write-tool classification (from server.py grep of `@mcp.tool()`)

### Read tools (always registered)
- gmail: search, read_message, read_thread, list_labels, get_attachment, list_filters, get_vacation
- calendar: list_calendars, get_events, freebusy, list_recurring_instances
- meet: get_space, list_participants, get_artifacts, list_conference_records, list_participant_sessions
- drive: search, read_file, list_folder, export, list_comments, list_revisions, list_permissions
- docs: read
- sheets: read, get_info
- tasks: list_tasklists, list
- contacts: search, list, list_groups, get_photo
- slides: read, get_thumbnail
- forms: read, list_responses

### Write tools (gated behind `WRITE_ALLOWED`)
- gmail: send, draft, modify_labels, send_draft, trash, untrash, create_label, delete_label, create_filter, delete_filter, set_vacation
- calendar: create_event, update_event, delete_event, quick_add
- meet: create_space, end_conference
- drive: create_file, share_file, create_folder, copy_file, add_comment, delete_permission, trash, untrash
- docs: create, insert_text, find_replace, append_text, insert_table, insert_image, format_text, insert_bullets, insert_page_break
- sheets: write, append, create, clear, batch_update, add_sheet, delete_sheet, merge_cells, add_chart, add_conditional_format, add_named_range
- tasks: create, update, delete, create_tasklist, move, clear_completed
- contacts: create, update, delete, create_group, modify_group_members, batch_create, batch_delete
- slides: create, add_slide, add_text, insert_shape, insert_image, insert_table, insert_video, format_text
- forms: create, add_question, update_question, delete_question, move_question, update_settings

## Design
- `auth.has_write_scopes()` returns True if any effective scope is NOT readonly.
  Readonly heuristic: endswith `.readonly` or `.metadata`.
- `server.py`: `WRITE_ALLOWED = has_write_scopes()` computed once at import time.
  `write_tool()` decorator is either `mcp.tool()` (write allowed) or a no-op (read-only).
  Each write tool function is decorated with `@write_tool()` instead of `@mcp.tool()`.
- `tools_gmail.gmail_create_filter`: reject any `action` key outside
  `{addLabelIds, removeLabelIds}` with `ValueError` before any API call.

## Verification
- `python3 -m py_compile server.py auth.py tools_gmail.py` — must pass.
- Runtime check: with readonly scopes, `has_write_scopes()` returns False and
  write tools are not registered.
