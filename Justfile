set positional-arguments

# default recipe to display help information
default:
  @just --list

# Install required dependencies
deps:
    cargo install mdbook mdbook-katex mdbook-linkcheck mdbook-mermaid
    pnpm i --frozen-lockfile

# Lint the workspace for all available targets
lint-check: lint-specs-md-check lint-specs-toc-check lint-specs-spelling-check lint-links-check lint-filenames-check

# Updates all files to fix linting issues
lint: lint-specs-md lint-specs-toc

# Validates markdown file formatting
lint-specs-md-check:
    npx markdownlint-cli2 "./specs/**/*.md"

# Updates markdown files formatting to satisfy lints
lint-specs-md:
    npx markdownlint-cli2 --fix "./specs/**/*.md"

# Backwards compatibility
lint-specs-md-fix:
    just lint-specs-md

# Validates Table of Content Sections with doctoc
lint-specs-toc-check:
    npx doctoc '--title=**Table of Contents**' ./specs && git diff --exit-code ./specs

# Updates Table of Content Sections with doctoc
lint-specs-toc:
    npx doctoc '--title=**Table of Contents**' ./specs

# Backwards compatibility
lint-specs-toc-fix:
    lint-specs-toc

# Validates spelling using cspell
lint-specs-spelling-check:
    npx cspell "./**/*.md"

# Updates cspell words file with new words
lint-specs-spelling:
    npx cspell --words-only --unique "./**/*.md" | sort --ignore-case | uniq > words.txt

# Backwards compatibility
lint-specs-spelling-fix:
    lint-specs-spelling

# Validates all hyperlinks respond with status 200
lint-links-check:
    docker run --init -it -v `pwd`:/input lycheeverse/lychee --verbose --no-progress --exclude-loopback \
    		--exclude twitter.com --exclude explorer.optimism.io --exclude linux-mips.org --exclude vitalik.eth.limo \
    		--exclude-mail /input/README.md "/input/specs/**/*.md"

# Filenames must not contain underscores
lint-filenames-check:
    #!/usr/bin/env bash
    for file in $(find ./specs -type f); do
      if [[ "$file" == *_* ]]; then
        echo "File with underscore found: $file"
        exit 1
      fi
    done
    echo "Filename linting complete"

build:
    mdbook build

# Serves the mdbook locally
serve *args='':
    mdbook serve $@
