#!/bin/bash
# Script tạo nhiều commit sai format để demo

mkdir -p src docs tests

# ==============================
# BATCH 1: Commit hoàn toàn sai format (không có ticket ID)
# ==============================
echo "feat: add login page" > src/auth.js && git add . && git commit -m "feat: add login page"
echo "fixed null pointer" > src/utils.js && git add . && git commit -m "fixed null pointer"
echo "update readme" >> docs/notes.md && git add . && git commit -m "update readme"
echo "WIP" > src/temp.js && git add . && git commit -m "WIP"
echo "hotfix" >> src/auth.js && git add . && git commit -m "hotfix"

# ==============================
# BATCH 2: Có ticket nhưng sai format (thiếu ngoặc vuông, sai case...)
# ==============================
echo "v2" >> src/auth.js && git add . && git commit -m "DL-101 add dashboard"
echo "v3" >> src/auth.js && git add . && git commit -m "[dl-102] fix bug login"
echo "v4" >> src/auth.js && git add . && git commit -m "DL103: update api"
echo "v5" >> src/auth.js && git add . && git commit -m "[DL-104]fix spacing issue"
echo "v6" >> src/auth.js && git add . && git commit -m "fix [DL-105] wrong position"

# ==============================
# BATCH 3: Một số đúng format (để contrast)
# ==============================
echo "v7" >> src/auth.js && git add . && git commit -m "[DL-106] add user profile"
echo "v8" >> src/auth.js && git add . && git commit -m "[DL-107] refactor auth service"

# ==============================
# BATCH 4: Merge commit style / squash mess
# ==============================
echo "v9" >> src/auth.js && git add . && git commit -m "Merge branch 'feature/old' into feature/demo-commit-fix"
echo "v10" >> src/auth.js && git add . && git commit -m "squash! add login"
echo "v11" >> src/auth.js && git add . && git commit -m "fixup! merge conflict"
echo "test" > tests/auth.test.js && git add . && git commit -m "add test"
echo "test2" >> tests/auth.test.js && git add . && git commit -m "test again"
echo "test3" >> tests/auth.test.js && git add . && git commit -m "still testing"

# ==============================
# BATCH 5: Tiếp tục sai format theo kiểu dev khác
# ==============================
for i in {108..120}; do
  echo "feature_$i" >> src/feature_$i.js
  git add .
  git commit -m "add feature $i without ticket"
done

echo "Done! Total commits on branch:"
git log main..HEAD --oneline | wc -l
echo ""
echo "Sample commits:"
git log main..HEAD --oneline | head -20
