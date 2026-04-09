# Contributing to Heritage Lens Multimodal

Thank you for your interest in contributing to Heritage Lens Multimodal!

## Development Setup

1. **Clone and setup environment**:
```bash
git clone <repository-url>
cd heritage-lens-multimodal
bash setup-multimodal-env.sh
source venv/bin/activate
```

2. **Install development dependencies**:
```bash
pip install pytest pytest-asyncio black isort mypy
```

3. **Configure pre-commit hooks** (optional):
```bash
pip install pre-commit
pre-commit install
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Document functions with docstrings
- Run `black` for formatting before committing

## Testing

Run tests before submitting PRs:
```bash
python -m pytest tests/ -v
```

Add tests for new features:
```bash
# Create test file
touch tests/test_your_feature.py

# Run specific test
python -m pytest tests/test_your_feature.py -v
```

## Project Structure

```
heritage-lens-multimodal/
├── agents/           # Sub-agents (synthesis, retrieval, vision, etc.)
├── pipelines/        # Data ingestion pipelines
├── ui/              # Web interfaces
├── config/          # Configuration files
├── tests/           # Test suite
└── data/            # Data storage (not committed)
```

## Adding New Features

### Adding a New Agent

1. Create agent in `agents/<category>/<agent_name>.py`
2. Add `__init__.py` exports
3. Add tests in `tests/test_<agent_name>.py`
4. Update orchestrator if needed

### Adding a New Pipeline

1. Create pipeline in `pipelines/<category>/<pipeline_name>.py`
2. Follow the existing pattern with async methods
3. Add CLI support if applicable
4. Document usage in README

## Submitting Changes

1. Create a feature branch
2. Make your changes
3. Add/update tests
4. Update documentation
5. Run verification: `python verify_setup.py`
6. Submit pull request

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Documentation improvements

## License

[Your License Here]
