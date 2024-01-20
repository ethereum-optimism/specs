dependencies:
    pnpm i --frozen-lockfile

lint-specs-check:
    npx markdownlint-cli2 "./specs/**/*.md"

lint-specs-fix:
    npx markdownlint-cli2-fix "./specs/**/*.md"

lint-specs-toc:
    npx doctoc '--title=**Table of Contents**' ./specs

lint-links:
    docker run --init -it -v `pwd`:/input lycheeverse/lychee --verbose --no-progress --exclude-loopback \
    		--exclude twitter.com --exclude explorer.optimism.io --exclude linux-mips.org --exclude vitalik.ca \
    		--exclude-mail /input/README.md "/input/specs/**/*.md"