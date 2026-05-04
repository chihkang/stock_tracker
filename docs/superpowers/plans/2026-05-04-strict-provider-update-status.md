# Strict Provider Update Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make scheduled portfolio updates truthfully report success, partial success, or failure while routing stock quotes through market-specific providers.

**Architecture:** Add market-routed quote providers and structured update results. Portfolio updates will write `updateStatus` to the gist, allow partial writes, and exit non-zero unless every requested stock updated successfully.

**Tech Stack:** Python 3.10, requests, BeautifulSoup, pytest, GitHub Actions.

---

### Task 1: Provider Routing And Results

**Files:**
- Create: `src/stock_tracker/providers/market_data.py`
- Modify: `src/stock_tracker/scraper/finance_scraper.py`
- Test: `tests/test_market_data_providers.py`

- [ ] Write tests for symbol routing and provider-specific symbol normalization.
- [ ] Implement price result and failure objects.
- [ ] Implement Taiwan and US Yahoo providers with market-specific normalization.
- [ ] Keep scraper facade functions compatible by returning dicts keyed by the original symbols.

### Task 2: Portfolio Update Status

**Files:**
- Modify: `src/stock_tracker/portfolio/portfolio_manager.py`
- Test: `tests/test_portfolio_update_status.py`

- [ ] Write tests for full success, partial success, and failed update outcomes.
- [ ] Add `updateStatus` with `success`, `partial_success`, or `failed`.
- [ ] On failed updates, write only `updateStatus` and leave prices, totals, percentages, and exchange rate unchanged.
- [ ] On partial updates, write updated prices plus `updateStatus`, then signal a non-zero CLI exit.

### Task 3: CLI Exit Semantics

**Files:**
- Modify: `src/stock_tracker/__main__.py`
- Test: `tests/test_cli_exit_status.py`

- [ ] Write tests that partial and failed statuses return non-zero.
- [ ] Return zero only when `updateStatus.status == "success"`.

### Task 4: Documentation

**Files:**
- Modify: `README.md`

- [ ] Document market-routed providers.
- [ ] Document `updateStatus` schema.
- [ ] Document GitHub Actions failure semantics.
