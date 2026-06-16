#!/bin/bash

set -e

echo "Checking for errors..."

> test-20260617/errors.txt

for file in test-20260617/*.json; do
  if grep -q '"error"' "$file"; then
    echo "Error found in $file:" >> test-20260617/errors.txt
    cat "$file" >> test-20260617/errors.txt
    echo "" >> test-20260617/errors.txt
    echo "----------------------------------------" >> test-20260617/errors.txt
  fi
done

echo "Error check completed. See test-20260617/errors.txt for details."
