#!/bin/bash
# ============================================================
# make_messy_commits.sh
# Tạo nhiều commit "lung tung" trên branch hiện tại để test
#
# CÁCH DÙNG:
#   bash make_messy_commits.sh [số_lượng]
#   bash make_messy_commits.sh 50
# ============================================================

COUNT="${1:-40}"
WORK_DIR="__demo_mess__"
mkdir -p "$WORK_DIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}Tạo $COUNT commit lung tung trên branch: $(git branch --show-current)${NC}"
echo ""

# ============================================================
# Pool các dạng commit SAI format (thực tế hay gặp)
# ============================================================

# Dạng 1: Không có ticket, viết tắt kiểu dev lười
NO_TICKET_MSGS=(
  "fix bug"
  "fix"
  "update"
  "done"
  "WIP"
  "test"
  "asdf"
  "okokok"
  "sửa lỗi rồi"
  "commit"
  "save"
  "temp"
  "changes"
  "misc fixes"
  "final"
  "final2"
  "final FINAL"
  "please work"
  "why is this broken"
  "hotfix"
  "hotfix2"
  "idk"
  "trying something"
)

# Dạng 2: Có ticket nhưng SAI format
BAD_TICKET_MSGS=(
  "DL-101 add login page"
  "DL-102: fix null pointer"
  "DL-103 - update profile api"
  "[dl-104] fix bug"
  "[DL-105]missing space after bracket"
  "fix [DL-106] wrong ticket position"
  "bugfix for DL-107"
  "DL108 no hyphen at all"
  "(DL-109) wrong bracket type"
  "DL-110update no space"
  "feat/DL-111/add-something"
  "#DL-112 wrong prefix"
  "[DL-113][extra-bracket] message"
  "DL-114"
  "[DL-115] "
)

# Dạng 3: Đúng format (để xen vào cho thực tế)
GOOD_MSGS=(
  "[DL-200] add authentication module"
  "[DL-201] fix token refresh logic"
  "[DL-202] update user profile endpoint"
  "[DL-203] refactor database connection"
  "[DL-204] add unit tests for auth"
)

# Dạng 4: Merge/squash/fixup style
META_MSGS=(
  "Merge branch 'feature/old-stuff' into feature/current"
  "Merge remote-tracking branch 'origin/main'"
  "squash! add login"
  "squash! fix bug"
  "fixup! previous commit"
  "fixup! fix bug"
  "Revert \"add something\""
  "Revert \"WIP\""
)

# ============================================================
# Tạo các file giả lập source code
# ============================================================
MODULES=("auth" "user" "payment" "notification" "dashboard" "api" "utils" "config" "db" "cache")
ACTIONS=("add" "update" "fix" "refactor" "remove" "cleanup" "optimize" "migrate")
EXTS=("js" "ts" "py" "go" "java" "css" "html")

rand_int() { echo $(( RANDOM % $1 )); }

pick_random() {
  local arr=("$@")
  echo "${arr[$(( RANDOM % ${#arr[@]} ))]}"
}

# ============================================================
# Generator: chọn dạng commit ngẫu nhiên theo tỉ lệ
# ============================================================
random_commit_msg() {
  local r=$(( RANDOM % 100 ))
  if   [ $r -lt 35 ]; then pick_random "${NO_TICKET_MSGS[@]}"   # 35% không ticket
  elif [ $r -lt 60 ]; then pick_random "${BAD_TICKET_MSGS[@]}"   # 25% ticket sai format
  elif [ $r -lt 75 ]; then pick_random "${GOOD_MSGS[@]}"          # 15% đúng format
  elif [ $r -lt 85 ]; then pick_random "${META_MSGS[@]}"          # 10% merge/squash
  else
    # 15% random hoàn toàn (dev gõ bừa)
    local random_words=("implement" "bugfix" "refactor" "cleanup" "update" "patch" "tweak" "improve")
    local w1=$(pick_random "${random_words[@]}")
    local mod=$(pick_random "${MODULES[@]}")
    echo "$w1 $mod"
  fi
}

# ============================================================
# Vòng lặp tạo commits
# ============================================================
CREATED=0
for i in $(seq 1 $COUNT); do
  # Tạo file thay đổi ngẫu nhiên
  module=$(pick_random "${MODULES[@]}")
  ext=$(pick_random "${EXTS[@]}")
  action=$(pick_random "${ACTIONS[@]}")
  file="$WORK_DIR/${module}_${action}_${i}.${ext}"

  # Nội dung file giả
  echo "// $module - change #$i - $(date +%s%N)" > "$file"
  echo "const x_${i} = '$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8 2>/dev/null || echo "random${i}")';" >> "$file"

  git add "$file" > /dev/null 2>&1

  msg=$(random_commit_msg)
  git commit -m "$msg" > /dev/null 2>&1

  # Hiển thị màu theo loại
  if echo "$msg" | grep -qP '^\[DL-\d+\] .+'; then
    echo -e "  ${GREEN}✓${NC} $(git log -1 --format='%h') | $msg"
  elif echo "$msg" | grep -qiP 'DL-?\d+'; then
    echo -e "  ${YELLOW}~${NC} $(git log -1 --format='%h') | $msg"
  else
    echo -e "  ${RED}✗${NC} $(git log -1 --format='%h') | $msg"
  fi

  CREATED=$(( CREATED + 1 ))
done

echo ""
echo -e "${CYAN}=== Tổng kết ===${NC}"
TOTAL=$(git log main..HEAD --oneline 2>/dev/null | wc -l || git log --oneline | wc -l)
GOOD_COUNT=$(git log main..HEAD --oneline 2>/dev/null | grep -cP '^\w+ \[DL-\d+\] .+' || echo "?")
BAD_COUNT=$(( TOTAL - GOOD_COUNT ))

echo -e "Đã tạo  : ${GREEN}$CREATED commits${NC}"
echo -e "Đúng ✓  : ${GREEN}$GOOD_COUNT${NC}"
echo -e "Sai  ✗  : ${RED}$BAD_COUNT${NC}"
echo ""
echo -e "${YELLOW}Để fix tất cả commit sai format:${NC}"
echo -e "  ${CYAN}bash fix_commits_fallback.sh main DL-999${NC}"
