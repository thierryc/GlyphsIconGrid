#!/bin/zsh

set -u

SCRIPT_DIR="${0:A:h}"
if [[ -f "${SCRIPT_DIR}/skills/glyphs-mcp-icon-grid/SKILL.md" ]]; then
  RELEASE_ROOT="$SCRIPT_DIR"
elif [[ -f "${SCRIPT_DIR:h}/skills/glyphs-mcp-icon-grid/SKILL.md" ]]; then
  RELEASE_ROOT="${SCRIPT_DIR:h}"
else
  RELEASE_ROOT="$SCRIPT_DIR"
fi
SOURCE="${RELEASE_ROOT}/skills/glyphs-mcp-icon-grid"
SKILL_NAME="glyphs-mcp-icon-grid"
INSTALL_HOME="${GLYPHS_ICON_GRID_SKILL_HOME:-${HOME}}"

pause_before_exit() {
  if [[ -t 0 ]]; then
    printf "\nPress Return to close this window."
    IFS= read -r _
  fi
}

fail() {
  printf "\nInstallation stopped: %s\n" "$1" >&2
  pause_before_exit
  exit 1
}

install_skill() {
  local label="$1"
  local destination="$2"
  local parent="${destination:h}"
  local backup=""
  local timestamp
  local answer

  if [[ -e "$destination" || -L "$destination" ]]; then
    printf "\nAn existing %s skill is installed at:\n%s\n" "$label" "$destination"
    printf "Replace it? The existing folder will be kept as a dated backup. [y/N] "
    IFS= read -r answer
    case "${answer:l}" in
      y|yes) ;;
      *)
        printf "Skipped %s.\n" "$label"
        return 0
        ;;
    esac

    timestamp="$(/bin/date +%Y%m%d-%H%M%S)"
    backup="${destination}.backup-${timestamp}"
    while [[ -e "$backup" || -L "$backup" ]]; do
      backup="${backup}-1"
    done
  fi

  /bin/mkdir -p "$parent" || fail "Could not create ${parent}."

  if [[ -n "$backup" ]]; then
    /bin/mv "$destination" "$backup" || fail "Could not back up the existing skill."
  fi

  if ! /usr/bin/ditto "$SOURCE" "$destination"; then
    local failed="${destination}.failed"
    if [[ -e "$destination" || -L "$destination" ]]; then
      while [[ -e "$failed" || -L "$failed" ]]; do
        failed="${failed}-1"
      done
      /bin/mv "$destination" "$failed"
    fi
    if [[ -n "$backup" ]]; then
      /bin/mv "$backup" "$destination"
    fi
    fail "Could not copy the skill. Any previous installation was restored."
  fi

  printf "\nInstalled for %s:\n%s\n" "$label" "$destination"
  if [[ -n "$backup" ]]; then
    printf "Previous version backed up at:\n%s\n" "$backup"
  fi
}

[[ -f "${SOURCE}/SKILL.md" ]] || fail \
  "The release is incomplete. Keep this installer beside the included skills folder."

printf "\nGlyphsIconGrid agent skill installer\n"
printf "====================================\n"
printf "1) Codex, Gemini, and Cursor (shared location)\n"
printf "2) Claude\n"
printf "3) All supported clients\n"

choice="${1:-}"
if [[ -z "$choice" ]]; then
  printf "Choose 1, 2, or 3 [1]: "
  IFS= read -r choice
  choice="${choice:-1}"
fi

case "${choice:l}" in
  1|shared|codex|gemini|cursor)
    install_skill "Codex, Gemini, and Cursor" \
      "${INSTALL_HOME}/.agents/skills/${SKILL_NAME}"
    ;;
  2|claude)
    install_skill "Claude" \
      "${INSTALL_HOME}/.claude/skills/${SKILL_NAME}"
    ;;
  3|all)
    install_skill "Codex, Gemini, and Cursor" \
      "${INSTALL_HOME}/.agents/skills/${SKILL_NAME}"
    install_skill "Claude" \
      "${INSTALL_HOME}/.claude/skills/${SKILL_NAME}"
    ;;
  *)
    fail "Unknown choice '${choice}'. Run the installer again and choose 1, 2, or 3."
    ;;
esac

printf "\nDone. Restart your AI client before using \$glyphs-mcp-icon-grid.\n"
pause_before_exit
