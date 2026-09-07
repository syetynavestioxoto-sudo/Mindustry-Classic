#!/bin/sh
# Pre-seed RoboVM dist into a local Maven repo so the 2.3.0 Gradle plugin
# (which hardcodes plain-http Central, dead since 2020) resolves offline.
# The plugin uses Aether with local repo $HOME/.m2/repository, consulted
# before remotes. The _remote.repositories file marks artifacts as locally
# installed (no revalidation).
#
# Usage: seed-m2.sh [M2REPO]   (default: $HOME/.m2/repository)
# Env: SEED_TARBALL=path  skip download, use existing tarball.
set -e
M2="${1:-$HOME/.m2/repository}"
G=com/mobidevelop/robovm/robovm-dist/2.3.0
D="$M2/$G"
mkdir -p "$D"
if [ -n "$SEED_TARBALL" ]; then
    cp "$SEED_TARBALL" "$D/robovm-dist-2.3.0-nocompiler.tar.gz"
else
    curl -sSL -o "$D/robovm-dist-2.3.0-nocompiler.tar.gz" \
      https://repo1.maven.org/maven2/$G/robovm-dist-2.3.0-nocompiler.tar.gz
fi
cat > "$D/robovm-dist-2.3.0.pom" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.mobidevelop.robovm</groupId>
  <artifactId>robovm-dist</artifactId>
  <version>2.3.0</version>
  <packaging>pom</packaging>
</project>
EOF
# Aether: empty tracker key = locally installed, always usable offline.
printf 'robovm-dist-2.3.0-nocompiler.tar.gz>=\nrobovm-dist-2.3.0.pom>=\n' \
  > "$D/_remote.repositories"
ls -la "$D"
echo "seeded $D"
