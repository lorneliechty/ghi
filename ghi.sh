#!/bin/bash

# ghi.sh — A shell wrapper for ghi operations
# Eliminates the Python boilerplate for agent use.

# ── Find .ghi/ directory (walk up from current dir) ──────────

find_ghi_root() {
    local current="$(pwd)"
    while [[ "$current" != "/" ]]; do
        if [[ -d "$current/.ghi" ]]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "Error: .ghi/ directory not found" >&2
    return 1
}

GHI_ROOT=$(find_ghi_root) || exit 1
GHI_DIR="${GHI_ROOT}/.ghi"
ISSUES_DIR="${GHI_DIR}/issues"

# ── Utilities ──────────────────────────────────────────────────

# Generate ISO 8601 timestamp
now_iso() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Convert ISO date to relative time (e.g., "3 days ago")
time_ago() {
    local iso_date="$1"
    # Extract just the date part (YYYY-MM-DD)
    local date_part="${iso_date:0:10}"
    # Convert to epoch
    local epoch=$(date -d "$date_part" +%s 2>/dev/null) || return 0
    local now=$(date +%s)
    local diff=$((now - epoch))

    if [[ $diff -lt 3600 ]]; then
        echo "$((diff / 60))m ago"
    elif [[ $diff -lt 86400 ]]; then
        echo "$((diff / 3600))h ago"
    else
        echo "$((diff / 86400))d ago"
    fi
}

# Extract a specific field from frontmatter
get_field() {
    local filepath="$1"
    local field="$2"

    local in_frontmatter=0
    local found_first_dash=0

    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ $found_first_dash -eq 0 ]]; then
                found_first_dash=1
                in_frontmatter=1
                continue
            else
                # Second "---" marks end of frontmatter
                break
            fi
        fi

        if [[ $in_frontmatter -eq 1 && "$line" == "${field}:"* ]]; then
            # Extract value after "field: "
            local value="${line#${field}: }"
            # Remove surrounding quotes if present
            value="${value%\"}"
            value="${value#\"}"
            echo "$value"
            return 0
        fi
    done < "$filepath"
}

# Resolve issue by id8 prefix (find first matching file)
resolve_issue_path() {
    local id8="$1"
    local matches=($(ls -1 "${ISSUES_DIR}" | grep "^${id8}" 2>/dev/null || true))

    if [[ ${#matches[@]} -eq 0 ]]; then
        echo "Error: No issue found with prefix '${id8}'" >&2
        return 1
    elif [[ ${#matches[@]} -gt 1 ]]; then
        echo "Error: Multiple issues match prefix '${id8}': ${matches[@]}" >&2
        return 1
    fi

    echo "${ISSUES_DIR}/${matches[0]}"
}

# ── Commands ───────────────────────────────────────────────────

cmd_open() {
    local title="$1"
    shift

    local author=""
    local assigned=""
    local priority=""
    local labels=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --author)
                author="$2"
                shift 2
                ;;
            --assigned)
                assigned="$2"
                shift 2
                ;;
            --priority)
                priority="$2"
                shift 2
                ;;
            --label)
                labels="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    # Generate UUID using system uuidgen (more efficient than Python)
    local uuid=$(uuidgen | tr '[:upper:]' '[:lower:]' 2>/dev/null)
    if [[ -z "$uuid" ]]; then
        # Fallback to Python if uuidgen unavailable
        uuid=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null)
        if [[ -z "$uuid" ]]; then
            echo "Error: Failed to generate UUID" >&2
            return 1
        fi
    fi

    local now=$(now_iso)

    # Build issue file content
    local content="---"
    content+=$'\n'"id: $uuid"
    content+=$'\n'"title: \"$title\""
    content+=$'\n'"status: open"
    content+=$'\n'"opened_by: $author"
    content+=$'\n'"opened_date: $now"

    if [[ -n "$labels" ]]; then
        content+=$'\n'"labels: [$labels]"
    else
        content+=$'\n'"labels: []"
    fi

    if [[ -n "$assigned" ]]; then
        content+=$'\n'"assigned_to: $assigned"
    fi

    if [[ -n "$priority" ]]; then
        content+=$'\n'"priority: $priority"
    fi

    content+=$'\n'"---"
    content+=$'\n'
    content+=$'\n'"(Description to be added)"
    content+=$'\n'

    # Write issue file
    local filepath="${ISSUES_DIR}/${uuid}.md"
    echo -e "$content" > "$filepath"

    echo "Created issue ${uuid:0:8} (${uuid})"
}

cmd_comment() {
    local id8="$1"
    shift

    local author=""
    local text=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --author)
                author="$2"
                shift 2
                ;;
            *)
                # First non-option argument is the comment text
                text="$1"
                shift
                ;;
        esac
    done

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    if [[ -z "$text" ]]; then
        echo "Error: comment text is required" >&2
        return 1
    fi

    local filepath=$(resolve_issue_path "$id8") || return 1
    local now=$(now_iso)

    # Check if comments section already exists
    if ! grep -q "<!-- ghi:comments -->" "$filepath"; then
        # Add the comments marker first
        echo "" >> "$filepath"
        echo "<!-- ghi:comments -->" >> "$filepath"
    fi

    # Append comment using awk (safely handles multiline text and special chars)
    # Fixed for issue #54ea1958: sed breaks on multiline/special chars
    awk -v author="$author" -v date="$now" -v comment="$text" '
        /<!-- ghi:comments -->/ {
            print;
            print "";
            print "<!-- ghi:comment author=\"" author "\" date=\"" date "\" -->";
            print "";
            print comment;
            next;
        }
        { print }
    ' "$filepath" > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    local uuid=$(basename "$filepath" .md)
    echo "Commented on issue ${uuid:0:8}"
}

cmd_close() {
    local id8="$1"
    shift

    local author=""
    local comment_text=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --author)
                author="$2"
                shift 2
                ;;
            --comment)
                comment_text="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    local filepath=$(resolve_issue_path "$id8") || return 1
    local now=$(now_iso)
    local uuid=$(basename "$filepath" .md)

    # Extract frontmatter
    local frontmatter_end=$(grep -n "^---$" "$filepath" | head -2 | tail -1 | cut -d: -f1)
    local body_start=$((frontmatter_end + 1))

    # Rebuild frontmatter with status and closed_date updated
    {
        head -n $((frontmatter_end - 1)) "$filepath" | \
            sed 's/^status: .*/status: resolved/'
        echo "closed_date: $now"
        echo "---"
        tail -n +$body_start "$filepath"
    } > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    # Add status-change comment
    if ! grep -q "<!-- ghi:comments -->" "$filepath"; then
        echo "" >> "$filepath"
        echo "<!-- ghi:comments -->" >> "$filepath"
    fi

    cat >> "$filepath" << EOF

<!-- ghi:comment author="$author" date="$now" -->

**Status changed:** open → resolved

$comment_text
EOF

    echo "Closed issue ${uuid:0:8}"
}

# Validate status value against allowed enum
validate_status() {
    local status="$1"
    case "$status" in
        open|in-progress|resolved|closed|wont-fix)
            return 0
            ;;
        *)
            echo "Error: Invalid status '$status'. Valid values: open, in-progress, resolved, closed, wont-fix" >&2
            return 1
            ;;
    esac
}

# Update issue status (with validation)
cmd_status() {
    local id8="$1"
    shift

    local new_status=""
    local author=""
    local reason=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --status)
                new_status="$2"
                shift 2
                ;;
            --author)
                author="$2"
                shift 2
                ;;
            --reason)
                reason="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    if [[ -z "$new_status" ]]; then
        echo "Error: --status is required" >&2
        return 1
    fi

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    # Validate status before writing (issue #e3577bf4)
    validate_status "$new_status" || return 1

    local filepath=$(resolve_issue_path "$id8") || return 1
    local now=$(now_iso)
    local uuid=$(basename "$filepath" .md)

    # Extract frontmatter
    local frontmatter_end=$(grep -n "^---$" "$filepath" | head -2 | tail -1 | cut -d: -f1)
    local body_start=$((frontmatter_end + 1))

    # Get old status
    local old_status=$(get_field "$filepath" "status")

    # Rebuild frontmatter with new status
    {
        head -n $((frontmatter_end - 1)) "$filepath" | \
            sed "s/^status: .*/status: $new_status/"

        # Update or add closed_date if moving to terminal status
        if [[ "$new_status" == "resolved" || "$new_status" == "closed" || "$new_status" == "wont-fix" ]]; then
            # Check if closed_date exists, replace it; otherwise add it before ---
            if grep -q "^closed_date:" "$filepath"; then
                :  # Will be replaced by sed in next step
            else
                echo "closed_date: $now"
            fi
        fi

        echo "---"
        tail -n +$body_start "$filepath"
    } > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    # Add status-change comment
    if ! grep -q "<!-- ghi:comments -->" "$filepath"; then
        echo "" >> "$filepath"
        echo "<!-- ghi:comments -->" >> "$filepath"
    fi

    local status_msg="**Status changed:** $old_status → $new_status"
    local comment_text="${reason:-}"

    awk -v msg="$status_msg" -v reason="$comment_text" -v author="$author" -v date="$now" '
        /<!-- ghi:comments -->/ {
            print;
            print "";
            print "<!-- ghi:comment author=\"" author "\" date=\"" date "\" -->";
            print "";
            print msg;
            if (reason != "") {
                print "";
                print reason;
            }
            next;
        }
        { print }
    ' "$filepath" > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    echo "Updated status of issue ${uuid:0:8} to '$new_status'"
}

cmd_read() {
    local id8="$1"

    if [[ -z "$id8" ]]; then
        echo "Error: issue ID required" >&2
        return 1
    fi

    local filepath=$(resolve_issue_path "$id8") || return 1
    local uuid=$(basename "$filepath" .md)

    # Extract frontmatter fields
    local title=$(get_field "$filepath" "title")
    local status=$(get_field "$filepath" "status")
    local priority=$(get_field "$filepath" "priority")
    local assigned_to=$(get_field "$filepath" "assigned_to")
    local opened_date=$(get_field "$filepath" "opened_date")

    # Print header
    echo "Title:    $title"
    echo "Status:   $status"
    echo "Priority: $priority"
    echo "Assigned: $assigned_to"
    echo "Opened:   $opened_date"
    echo ""

    # Extract description (text between second --- and <!-- ghi:comments -->)
    local frontmatter_end=$(grep -n "^---$" "$filepath" | head -2 | tail -1 | cut -d: -f1)
    local comments_start=$(grep -n "<!-- ghi:comments -->" "$filepath" | head -1 | cut -d: -f1)

    if [[ -n "$comments_start" ]]; then
        # Description is between frontmatter_end + 1 and comments_start - 1
        local desc_end=$((comments_start - 1))
        local description=$(sed -n "$((frontmatter_end + 1)),$((desc_end))p" "$filepath")
    else
        # No comments section, description is from frontmatter_end to EOF
        local description=$(sed -n "$((frontmatter_end + 1)),\$p" "$filepath")
    fi

    # Print description (trimmed of leading/trailing blank lines)
    description=$(echo "$description" | sed '/^[[:space:]]*$/d')
    if [[ -n "$description" ]]; then
        echo "Description:"
        echo "$description" | sed 's/^/  /'
        echo ""
    fi

    # Extract and display comments using awk for clean parsing
    local comment_count=$(grep -c "<!-- ghi:comment" "$filepath" 2>/dev/null)
    comment_count=${comment_count:-0}

    if [[ $comment_count -gt 0 ]]; then
        echo "Comments ($comment_count):"

        # Use awk to parse comments cleanly
        awk '
        BEGIN { in_comment = 0; comment_header = "" }

        /<!-- ghi:comment author=/ {
            # This is a comment header line
            comment_header = $0;
            # Extract author and date
            if (match(comment_header, /author="([^"]*)" date="([^"]*)"/, arr)) {
                author = arr[1];
                date = arr[2];
                printf "  [%s] %s:\n", date, author;
            }
            in_comment = 1;
            skip_empty = 1;
            next;
        }

        in_comment {
            if (/^<!-- ghi:comment/ || /^$/) {
                # Next comment or blank line after comment
                if (skip_empty && /^$/) {
                    skip_empty = 0;
                    next;
                }
                if (/^<!-- ghi:comment/) {
                    in_comment = 0;
                }
            }

            if (in_comment && !/^$/) {
                printf "    %s\n", $0;
                skip_empty = 0;
            } else if (in_comment && /^$/ && !skip_empty) {
                # Preserve blank lines within comment content
                print "";
            }
        }
        ' "$filepath"
    fi
}

cmd_summary() {
    local assigned=""
    local no_done=0

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --assigned)
                assigned="$2"
                shift 2
                ;;
            --no-done)
                no_done=1
                shift
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    # First pass: count all issues (unfiltered) for header
    local total=0
    local total_active=0
    local total_done=0

    for file in "${ISSUES_DIR}"/*.md; do
        [[ ! -f "$file" ]] && continue
        [[ "$(basename "$file")" == ".gitkeep" ]] && continue

        ((total++))
        local status=$(get_field "$file" "status")

        if [[ "$status" == "open" || "$status" == "in-progress" ]]; then
            ((total_active++))
        else
            ((total_done++))
        fi
    done

    # Print summary header
    echo "ghi: $total issues ($total_active active, $total_done done)"
    if [[ -n "$assigned" ]]; then
        echo " — showing @${assigned}"
    fi
    echo ""

    # Print issues by status
    for status_name in "open" "in-progress" "resolved" "closed"; do
        if [[ $no_done -eq 1 && ("$status_name" == "resolved" || "$status_name" == "closed") ]]; then
            continue
        fi

        local count=0
        local matching_files=()

        for file in "${ISSUES_DIR}"/*.md; do
            [[ ! -f "$file" ]] && continue
            local file_status=$(get_field "$file" "status")
            [[ "$file_status" != "$status_name" ]] && continue

            local assigned_to=$(get_field "$file" "assigned_to")
            if [[ -n "$assigned" && "$assigned_to" != "$assigned" ]]; then
                continue
            fi

            ((count++))
            matching_files+=("$file")
        done

        if [[ $count -gt 0 ]]; then
            local display_status=$(echo "$status_name" | tr '[:lower:]' '[:upper:]')
            echo "$display_status ($count):"

            for file in "${matching_files[@]}"; do
                local uuid=$(basename "$file" .md)
                local title=$(get_field "$file" "title")
                local priority=$(get_field "$file" "priority")
                local opened_date=$(get_field "$file" "opened_date")

                # For terminal statuses, use closed_date for age; otherwise opened_date
                local age_date="$opened_date"
                if [[ "$status_name" == "resolved" || "$status_name" == "closed" ]]; then
                    age_date=$(get_field "$file" "closed_date")
                fi

                local age=$(time_ago "$age_date")
                printf "  [%-8s] %-45s %-8s %s\n" "${uuid:0:8}" "$title" "$priority" "$age"
            done
            echo ""
        fi
    done
}

cmd_list() {
    local assigned=""
    local status=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --assigned)
                assigned="$2"
                shift 2
                ;;
            --status)
                status="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    for file in "${ISSUES_DIR}"/*.md; do
        [[ ! -f "$file" ]] && continue
        [[ "$(basename "$file")" == ".gitkeep" ]] && continue

        local file_status=$(get_field "$file" "status")
        if [[ -n "$status" && "$file_status" != "$status" ]]; then
            continue
        fi

        local assigned_to=$(get_field "$file" "assigned_to")
        if [[ -n "$assigned" && "$assigned_to" != "$assigned" ]]; then
            continue
        fi

        local uuid=$(basename "$file" .md)
        local title=$(get_field "$file" "title")

        printf "[%-8s] %-15s %s\n" "${uuid:0:8}" "$file_status" "$title"
    done
}

# Assign issue to an agent
cmd_assign() {
    local id8="$1"
    shift

    local assignee=""
    local author=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --to)
                assignee="$2"
                shift 2
                ;;
            --author)
                author="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    if [[ -z "$assignee" ]]; then
        echo "Error: --to is required" >&2
        return 1
    fi

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    local filepath=$(resolve_issue_path "$id8") || return 1
    local now=$(now_iso)
    local uuid=$(basename "$filepath" .md)

    # Extract frontmatter
    local frontmatter_end=$(grep -n "^---$" "$filepath" | head -2 | tail -1 | cut -d: -f1)
    local body_start=$((frontmatter_end + 1))

    # Get old assignee
    local old_assignee=$(get_field "$filepath" "assigned_to")
    old_assignee="${old_assignee:-unassigned}"

    # Rebuild frontmatter with new assignment
    {
        head -n $((frontmatter_end - 1)) "$filepath" | \
            sed "s/^assigned_to: .*/assigned_to: $assignee/" || \
            head -n $((frontmatter_end - 1)) "$filepath"

        # Add assigned_to if it wasn't in the file
        if ! grep -q "^assigned_to:" "$filepath"; then
            echo "assigned_to: $assignee"
        fi

        echo "---"
        tail -n +$body_start "$filepath"
    } > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    # Add assignment comment
    if ! grep -q "<!-- ghi:comments -->" "$filepath"; then
        echo "" >> "$filepath"
        echo "<!-- ghi:comments -->" >> "$filepath"
    fi

    local comment_msg="**Assigned:** $old_assignee → $assignee"

    awk -v msg="$comment_msg" -v author="$author" -v date="$now" '
        /<!-- ghi:comments -->/ {
            print;
            print "";
            print "<!-- ghi:comment author=\"" author "\" date=\"" date "\" -->";
            print "";
            print msg;
            next;
        }
        { print }
    ' "$filepath" > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    echo "Assigned issue ${uuid:0:8} to '$assignee'"
}

# Set issue priority
cmd_priority() {
    local id8="$1"
    shift

    local priority=""
    local author=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --level)
                priority="$2"
                shift 2
                ;;
            --author)
                author="$2"
                shift 2
                ;;
            *)
                echo "Unknown option: $1" >&2
                return 1
                ;;
        esac
    done

    if [[ -z "$priority" ]]; then
        echo "Error: --level is required" >&2
        return 1
    fi

    if [[ -z "$author" ]]; then
        echo "Error: --author is required" >&2
        return 1
    fi

    # Validate priority (matches ghi.py VALID_PRIORITIES)
    case "$priority" in
        critical|high|medium|low)
            :  # Valid
            ;;
        *)
            echo "Error: Invalid priority '$priority'. Valid values: critical, high, medium, low" >&2
            return 1
            ;;
    esac

    local filepath=$(resolve_issue_path "$id8") || return 1
    local now=$(now_iso)
    local uuid=$(basename "$filepath" .md)

    # Extract frontmatter
    local frontmatter_end=$(grep -n "^---$" "$filepath" | head -2 | tail -1 | cut -d: -f1)
    local body_start=$((frontmatter_end + 1))

    # Get old priority
    local old_priority=$(get_field "$filepath" "priority")
    old_priority="${old_priority:-unset}"

    # Rebuild frontmatter with new priority
    {
        head -n $((frontmatter_end - 1)) "$filepath" | \
            sed "s/^priority: .*/priority: $priority/" || \
            head -n $((frontmatter_end - 1)) "$filepath"

        # Add priority if it wasn't in the file
        if ! grep -q "^priority:" "$filepath"; then
            echo "priority: $priority"
        fi

        echo "---"
        tail -n +$body_start "$filepath"
    } > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    # Add priority-change comment
    if ! grep -q "<!-- ghi:comments -->" "$filepath"; then
        echo "" >> "$filepath"
        echo "<!-- ghi:comments -->" >> "$filepath"
    fi

    local comment_msg="**Priority changed:** $old_priority → $priority"

    awk -v msg="$comment_msg" -v author="$author" -v date="$now" '
        /<!-- ghi:comments -->/ {
            print;
            print "";
            print "<!-- ghi:comment author=\"" author "\" date=\"" date "\" -->";
            print "";
            print msg;
            next;
        }
        { print }
    ' "$filepath" > "$filepath.tmp"

    mv "$filepath.tmp" "$filepath"

    echo "Set priority of issue ${uuid:0:8} to '$priority'"
}

# ── Main dispatcher ────────────────────────────────────────────

main() {
    local cmd="$1"
    shift || true

    case "$cmd" in
        open)
            cmd_open "$@"
            ;;
        comment)
            cmd_comment "$@"
            ;;
        close)
            cmd_close "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        assign)
            cmd_assign "$@"
            ;;
        priority)
            cmd_priority "$@"
            ;;
        read)
            cmd_read "$@"
            ;;
        summary)
            cmd_summary "$@"
            ;;
        list)
            cmd_list "$@"
            ;;
        *)
            echo "Usage: ghi.sh <command> [options]"
            echo ""
            echo "Commands:"
            echo "  open TITLE --author NAME [--assigned NAME] [--priority LEVEL] [--label LABELS]"
            echo "  comment ID8 --author NAME TEXT"
            echo "  close ID8 --author NAME [--comment TEXT]"
            echo "  status ID8 --status {open|in-progress|resolved|closed|wont-fix} --author NAME [--reason TEXT]"
            echo "  assign ID8 --to NAME --author NAME"
            echo "  priority ID8 --level {critical|high|medium|low} --author NAME"
            echo "  read ID8"
            echo "  summary [--assigned NAME] [--no-done]"
            echo "  list [--status STATUS] [--assigned NAME]"
            return 1
            ;;
    esac
}

main "$@"
