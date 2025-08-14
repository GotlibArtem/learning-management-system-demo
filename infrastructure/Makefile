install:
	pip install --upgrade pip
	pip install -r requirements.txt
	ansible-galaxy install -r requirements.yml

lint-yml:
	@yamllint --strict . && echo "Yaml linting ok"

lint: lint-yml
	ansible-lint --format pep8 --offline
