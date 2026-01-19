# Changelog

All notable changes to RAGVersion will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-19

### Added
- Initial release of RAGVersion
- Async-first version tracking for RAG applications
- Supabase storage backend with PostgreSQL
- Document parsers: PDF, DOCX, TXT, Markdown
- Batch processing with error resilience
- LangChain integration helper
- LlamaIndex integration helper
- CLI tool with commands: init, migrate, track, list, history, diff, health
- Mock storage for testing
- Comprehensive documentation and examples

### Features
- AsyncVersionTracker core class
- Change detection with content hashing
- Event system with async callback support
- Configuration via YAML and environment variables
- Content compression with gzip
- Resilient batch processing (continue-on-error)

[0.1.0]: https://github.com/sourangshupal/ragversion/releases/tag/v0.1.0
