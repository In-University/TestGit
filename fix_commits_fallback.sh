#!/bin/bash
# ============================================================
# fix_commits_fallback.sh  (dùng git filter-branch thuần, không cần cài thêm)
# Chậm hơn filter-repo nhưng không cần dependency ngoài
#
# DÙNG KHI git-filter-repo chưa cài được
# CÁCH DÙNG: bash fix_commits_fallback.sh [base_branch] [default_ticket]
# ============================================================

BASE_BRANCH="${1:-main}"
DEFAULT_TICKET="${2:-DL-000}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

CURRENT_BRANCH=$(git branch --show-current)
MERGE_BASE=$(git merge-base HEAD "$BASE_BRANCH")

echo -e "${CYAN}=== Fallback: git filter-branch ===${NC}"
echo -e "Base: $BASE_BRANCH | Merge-base: $MERGE_BASE"

# Tạo file helper script riêng (git filter-branch dùng /bin/sh, không support export -f)
HELPER_SCRIPT=$(mktemp /tmp/normalize_XXXX.sh)
chmod +x "$HELPER_SCRIPT"
cat > "$HELPER_SCRIPT" << HELPEREOF
#!/bin/bash
msg="\$(cat)"
DEFAULT_TICKET="$DEFAULT_TICKET"

# Đã đúng format -> giữ nguyên
if echo "\$msg" | grep -qP '^\[DL-\d+\] .+'; then
  echo "\$msg"; exit 0
fi
# [dl-xxx] hoặc [DL-xxx] thiếu space
if echo "\$msg" | grep -qP '^\[[Dd][Ll]-\d+\].+'; then
  ticket=\$(echo "\$msg" | grep -oP '(?<=\[)[Dd][Ll]-\d+(?=\])' | tr '[:lower:]' '[:upper:]')
  rest=\$(echo "\$msg" | sed -E 's/^\[[Dd][Ll]-[0-9]+\]\s*//')
  echo "[\$ticket] \$rest"; exit 0
fi
# DL-xxx: msg hoặc DL-xxx msg
if echo "\$msg" | grep -qiP '^DL-\d+[: ]'; then
  ticket=\$(echo "\$msg" | grep -oiP '^DL-\d+' | tr '[:lower:]' '[:upper:]')
  rest=\$(echo "\$msg" | sed -E 's/^[Dd][Ll]-[0-9]+[: ]+//')
  echo "[\$ticket] \$rest"; exit 0
fi
# Ticket ở giữa/cuối: "fix [DL-105] something"
if echo "\$msg" | grep -qiP '\[[Dd][Ll]-\d+\]'; then
  ticket=\$(echo "\$msg" | grep -oiP 'DL-\d+' | tr '[:lower:]' '[:upper:]')
  rest=\$(echo "\$msg" | sed -E 's/\s*\[[Dd][Ll]-[0-9]+\]\s*/ /g' | xargs)
  echo "[\$ticket] \$rest"; exit 0
fi
# Không tìm được ticket -> gắn default ticket
echo "[\$DEFAULT_TICKET] \$msg"
HELPEREOF

# Backup trước khi làm gì
BACKUP_BRANCH="backup/${CURRENT_BRANCH}-$(date +%Y%m%d%H%M%S)"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}Backup tạo tại: $BACKUP_BRANCH${NC}"

echo -e "${YELLOW}Đang chạy filter-branch (có thể chậm với nhiều commit)...${NC}"

FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter "bash $HELPER_SCRIPT" \
  "$MERGE_BASE"..HEAD

rm -f "$HELPER_SCRIPT"

echo ""
echo -e "${GREEN}Hoàn thành! Kiểm tra kết quả:${NC}"
git log "$MERGE_BASE"..HEAD --oneline | head -20
echo ""
echo -e "${YELLOW}Force push (bắt buộc vì SHA đã thay đổi):${NC}"
echo -e "  ${CYAN}git push origin $CURRENT_BRANCH --force-with-lease${NC}"
