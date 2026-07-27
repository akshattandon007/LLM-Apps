#!/usr/bin/env bash
# Semantic Shell wrapper for bash integration
# Add this to your ~/.bashrc:
#   eval "$(semantic-shell-init)"

# Main wrapper function
ss() {
    local cmd
    cmd=$(semantic-shell "$@")
    
    if [[ $cmd == ERROR:* ]]; then
        echo "$cmd" >&2
        return 1
    fi
    
    # Display the command
    echo -e "\033[1;36m▶\033[0m $cmd"
    
    # Ask for confirmation
    read -p "Run this command? [Y/n] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        # Add to history and execute
        history -s "$cmd"
        eval "$cmd"
    else
        echo "Command cancelled"
        return 1
    fi
}

# Init function for bashrc
semantic-shell-init() {
    cat << 'EOF'
# Semantic Shell integration
ss() {
    local cmd
    cmd=$(semantic-shell "$@")
    
    if [[ $cmd == ERROR:* ]]; then
        echo "$cmd" >&2
        return 1
    fi
    
    echo -e "\033[1;36m▶\033[0m $cmd"
    read -p "Run this command? [Y/n] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        history -s "$cmd"
        eval "$cmd"
    else
        echo "Command cancelled"
        return 1
    fi
}
EOF
}

# If sourced, define the function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Script was executed, show init code
    semantic-shell-init
fi
