# Verification report

## Passed automated checks

- Django system check: no issues.
- Additive migration applied to the provided database.
- Twelve integration tests cover public template rendering, search and filters, account creation/password validation, saved jobs, application submission and duplicates, expired jobs, employer status updates, cross-account isolation, REST API field controls, PDF upload and private access, salary validation, CSRF/POST-only actions, notification isolation, and repeatable demo seeding.
- Original users, jobs, profiles, and applications retained in the supplied database.

## Verification limits

A browser visual inspection was not available in the execution environment. Desktop/mobile CSS and templates were implemented, and HTML responses were exercised through Django's test client; this does not replace a visual check on your devices. No public hosting, external email delivery, load test, or production security audit was performed.

## Manual acceptance check

Run the app and complete the candidate/employer walkthrough in README.md. Check the job grid at desktop and mobile widths, keyboard navigation, resume download, sign-out, and the notification badge after a status change. Review existing listings for completeness and any missing original media files.
