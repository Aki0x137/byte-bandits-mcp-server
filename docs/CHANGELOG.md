# Changelog

All notable changes to this project will be documented here.

Format: Keep a [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) style.

## [Unreleased]
### Added
- Initial documentation scaffolding.
- Simple HTML JWT Token Generator with FastAPI & Jinja2 templates
  - GET /token-generator: Form with country code and phone number
  - POST /generate-token: Generates/returns JWT and stores in Redis for 14 days
  - Templates in templates/token_form.html, token_success.html, token_error.html
  - Config via JWT_SECRET, JWT_EXPIRATION_DAYS (default 14 days), TOKEN_APP_PATH, TOKEN_APP_PORT

### Changed
- Update README and mcp.md with token generator usage and configuration
- Include templates directory in wheel build config

### Fixed
- In-memory Redis client implementation parity (execute, expiry, lrange, ltrim, etc.)
