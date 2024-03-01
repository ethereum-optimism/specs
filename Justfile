set positional-arguments

# default recipe to display help information
default:
  @just --list

# Install required dependencies
deps:
    pnpm i --frozen-lockfile

# Lint the workspace for all available targets
lint: lint-specs-md-check lint-specs-toc-check lint-links

# Updates all files to fix linting issues
lint-fix: lint-specs-md-fix lint-specs-toc

# Validates markdown file formatting
lint-specs-md-check:
    npx markdownlint-cli2 "./specs/**/*.md"

# Updates markdown files formatting to satisfy lints
lint-specs-md-fix:
    npx markdownlint-cli2 --fix "./specs/**/*.md"

# Validates Table of Content Sections with doctoc
lint-specs-toc-check:
    npx doctoc '--title=**Table of Contents**' ./specs && git diff --exit-code ./specs

# Updates Table of Content Sections with doctoc
lint-specs-toc:
    npx doctoc '--title=**Table of Contents**' ./specs

# Validates all hyperlinks respond with status 200
lint-links:
    docker run --init -it -v `pwd`:/input lycheeverse/lychee --verbose --no-progress --exclude-loopback \
    		--exclude twitter.com --exclude explorer.optimism.io --exclude linux-mips.org --exclude vitalik.ca \
    		--exclude-mail /input/README.md "/input/specs/**/*.md"

# Serves the mdbook locally
serve *args='':
    mdbook serve $@
