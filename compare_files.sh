#!/bin/bash
# Compare local backend files with server versions
echo "=== Comparing key files ==="
for f in core/vimax/extractor.py core/vimax/decomposer.py core/proxy.py api/generate.py models/db.py api/user.py config.py api/payment.py api/auth.py api/pool.py api/sqb_pay.py api/alipay_pay.py main.py; do
  if [ -f "/tmp/local_backend/$f" ] && [ -f "/home/ubuntu/aiforge/backend/$f" ]; then
    diff_result=$(diff /tmp/local_backend/$f /home/ubuntu/aiforge/backend/$f 2>/dev/null)
    if [ -n "$diff_result" ]; then
      echo "DIFF: $f"
      echo "$diff_result" | head -5
      echo "---"
    else
      echo "SAME: $f"
    fi
  elif [ -f "/tmp/local_backend/$f" ]; then
    echo "ONLY_LOCAL: $f (not on server)"
  elif [ -f "/home/ubuntu/aiforge/backend/$f" ]; then
    echo "ONLY_SERVER: $f (not local)"
  fi
done
