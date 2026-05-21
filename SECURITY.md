# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email security concerns to the maintainers via the contact on [micap.ai](https://micap.ai)
3. Include a description of the vulnerability and steps to reproduce

We will acknowledge receipt within 48 hours and provide a fix timeline within 7 days.

## Scope

This library processes financial market data (OHLCV) and produces regime classifications. It does not handle authentication, personal data, or payment information. Key security considerations:

- **Configuration files** may contain calibrated model parameters that should be treated as proprietary
- **API tokens** (yfinance, etc.) should never be committed to the repository
- **Data privacy** — the library does not transmit data externally; all processing is local
