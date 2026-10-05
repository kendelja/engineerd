# Engineerd — Job Discovery Platform
<p align="center">
  <img src="./EngineerdBanner.png" width="200">
</p>

Engineerd is a full-stack job discovery platform that aggregates job postings from multiple sources into a centralized dashboard. It uses a custom data ingestion pipeline to **scrape, parse, normalize, validate, deduplicate, and store** job data in PostgreSQL.

## Tech Stack

* **Backend:** Python, FastAPI
* **Frontend:** React, JavaScript
* **Database:** PostgreSQL
* **Scraping & Parsing:** Playwright, BeautifulSoup
* **API:** REST

## Features

* Aggregates job postings from **Built In** and **Wellfound**
* Multi-page scraping with source-specific scrapers and parsers
* Handles multiple job positions within Wellfound company listings
* Normalizes inconsistent data into a shared job structure
* Validates and deduplicates postings before database insertion
* Stores job data in PostgreSQL
* FastAPI endpoints for ingestion and job retrieval
* React dashboard displaying company, location, salary, experience, posting date, source, and logos

<p align="center">
  <img src="./EngineerdDemo.PNG" width="1000">
</p>

## Architecture

```
Job Sources
     ↓
Scrapers
     ↓
Parsers
     ↓
Normalization
     ↓
Validation
     ↓
Deduplication
     ↓
PostgreSQL
     ↓
FastAPI
     ↓
React Dashboard
```

The ingestion system uses **source-specific scrapers and parsers with a shared processing pipeline**, making it straightforward to add additional job sources.

## Project Structure

```
engineerd/
├── backend/
│   └── app/
│       ├── api/
│       ├── database/
│       ├── ingestion/
│       │   ├── scrapers/
│       │   ├── parsers/
│       │   ├── normalizer.py
│       │   ├── validator.py
│       │   ├── deduplicator.py
│       │   └── pipeline.py
│       └── models/
├── frontend/
├── database/
│   └── schema.sql
└── README.md
```

## Roadmap

* [ ] Add additional job sources
* [ ] Add advanced filtering
* [ ] Add job relevance/match scoring
* [ ] Add scheduled ingestion
* [ ] Add AI-assisted job matching
* [ ] Deploy application

## Why I Built It

Engineerd was built to reduce the noise of traditional job searches while providing a practical project for **full-stack development, web scraping, data engineering, and API development**. It also provides a foundation for future automated job relevance and AI-assisted matching.
