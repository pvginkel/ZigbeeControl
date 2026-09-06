Brief description
- Add a simple password gate so the Home Assistant iframe only loads the existing Zigbee wrapper UI after authentication. The frontend will call the backend validate endpoint (`GET /api/auth/check`) on startup, show a one-field password form when the check fails, and render the wrapper as soon as validation or login (`POST /api/auth/login`) succeeds.

Relevant files and functions
- src/lib/api.ts: add `checkAuth()` and `login(password)` helpers and reuse the existing config/restart/status wrappers with same-origin cookie behaviour.
- src/hooks/useConfigQuery.ts: allow callers to enable/disable the config query and surface 401/403 responses so the UI can flip back to the login screen when the cookie goes missing.
- src/hooks/useAuth.ts (new): centralise the `GET /api/auth/check` query, expose an `isAuthenticated` flag plus a mutation for `POST /api/auth/login`, and notify the app when auth changes.
- src/App.tsx: gate the current AppShell behind the auth state, show loading while `checkAuth` runs, and render the login screen when unauthenticated.
- src/components/LoginScreen.tsx (new): render the minimal password form, call the login mutation, and surface validation errors.
- src/styles/login.css (new or existing bundle): styling to match the dark wrapper theme for the login screen, including focus states and error text.
- src/hooks/useSseStatus.ts: ensure `openStatusStream` is called with credentials so cookies accompany SSE connections.

Implementation steps
1. API utilities
   - Add `checkAuth()` and `login(password)` to `src/lib/api.ts` targeting `/api/auth/check` and `/api/auth/login`, matching the backend request/response shapes while leaving the existing same-origin fetch defaults untouched so cookies travel automatically.
   - Normalise error handling so 401/403 responses throw a dedicated error type or value the app can use to flip into the unauthenticated state.

2. Auth hook
   - Create `src/hooks/useAuth.ts` that wraps React Query: a `useAuthStatus()` query that runs `checkAuth` on mount (`retry: false`) and a `useLoginMutation()` that posts the password, updates the cached auth status on success, and exposes structured errors for bad passwords.
   - Export helpers to mark the app unauthenticated when any guarded request fails, so other hooks/components can trigger a login screen reset.

3. App gating
   - Refactor `src/App.tsx` to use the new auth hook: render a spinner while the validate query is pending, show `<LoginScreen>` when `isAuthenticated` is false, and only mount `AppShell` + `useConfigQuery` when auth is confirmed.
   - Adjust the config query usage (via the new `enabled` flag) and make sure auth changes trigger `queryClient.invalidateQueries(['config'])` so the tab data reloads immediately after login.

4. Login screen UI
   - Implement `src/components/LoginScreen.tsx` with a password field, submit button, and inline error text using semantic form markup (`<form>`, `<label>`, `aria-live` for errors). Submit should call the login mutation, disable the button while pending, and focus the password input on mount.
   - After a successful login, call the provided callback to let `App.tsx` re-run the auth check and fetch the tab config.

5. Styling and polish
   - Add a small stylesheet (e.g., `src/styles/login.css`) or extend an existing bundle to give the login panel centered layout, dark-surface background, clear focus outlines, and spacing consistent with the app feedback states.
   - Verify keyboard-only users can reach the password field and submit button, and ensure the form respects the "no extra UI" constraint (single password box plus submit control).

6. Propagate auth loss
   - Update `useConfigQuery` (and any restart mutations if needed) to detect 401/403, call the auth hook’s "setUnauthenticated" helper, and surface a friendly message in place of the existing error block so users are prompted to log in again without a full page reload.
   - Ensure SSE reconnection logic closes streams cleanly when the hook reports unauthenticated to avoid endless retry noise while the login form is visible.

7. Documentation updates
   - Add follow-up tasks to revise `AGENTS.md` and `docs/product_brief.md` so both documents describe the authenticated wrapper flow and no longer advertise the app as unauthenticated.
