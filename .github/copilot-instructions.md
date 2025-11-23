# Football Betting Analysis Project - Copilot Instructions

This project provides authentic football betting odds analysis using official APIs without web scraping.

## Project Overview
- **Purpose**: Analyze double chance betting markets (1X, X2) with real data
- **Data Sources**: Official sports APIs only (The Odds API, SportRadar, etc.)
- **Analysis**: Implied probability calculations and filtering
- **Output**: Structured tables with validation results

## Code Guidelines
- Use official APIs with proper authentication
- Implement robust error handling for API failures
- Validate all data before processing
- Follow Python best practices for data analysis
- Include comprehensive logging for debugging

## API Integration Rules
- Always use official sports data providers
- Handle rate limits and API quotas properly
- Store API keys securely in environment variables
- Implement fallback mechanisms for API unavailability

## Data Validation
- Verify odds data authenticity
- Cross-reference multiple sources when possible
- Flag suspicious or outdated odds
- Maintain data quality standards

## Security Practices
- Never hardcode API keys
- Use environment variables for sensitive data
- Implement proper input validation
- Log security events appropriately