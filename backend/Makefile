.PHONY: install test lint format typecheck clean deploy

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	pytest

# Run tests with coverage
test-coverage:
	pytest --cov --cov-report=html

# Run unit tests only
test-unit:
	pytest -m unit

# Run integration tests only
test-integration:
	pytest -m integration

# Lint code
lint:
	pylint functions/ layers/

# Format code
format:
	black functions/ layers/ tests/

# Type check
typecheck:
	mypy functions/ layers/

# Run all quality checks
quality: format lint typecheck test

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf htmlcov/ .coverage coverage.xml
	rm -rf dist/ build/
	rm -rf cdk.out/

# Deploy to dev environment
deploy-dev:
	cd infrastructure && cdk deploy --profile backend-dev --region us-west-2

# Deploy to staging
deploy-staging:
	cd infrastructure && cdk deploy --profile backend-staging --context env=staging --region us-west-2

# Deploy to production
deploy-prod:
	cd infrastructure && cdk deploy --profile backend-prod --context env=production --region us-west-2

# Synthesize CloudFormation template
synth:
	cd infrastructure && cdk synth --region us-west-2

# Show differences
diff:
	cd infrastructure && cdk diff --region us-west-2

# Package Lambda function
package-%:
	cd functions/$* && \
	rm -rf package/ function.zip && \
	mkdir -p package && \
	pip install -r requirements.txt -t package/ && \
	cd package && zip -r ../function.zip . && \
	cd .. && zip -g function.zip *.py
