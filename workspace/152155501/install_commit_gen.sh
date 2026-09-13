#!/bin/bash
# Installation script for commit_gen

ALIAS_CMD="alias commit-gen='node $(pwd)/commit_gen.js'"

if [[ $SHELL == *"zsh"* ]]; then
    echo "$ALIAS_CMD" >> ~/.zshrc
    source ~/.zshrc
elif [[ $SHELL == *"bash"* ]]; then
    echo "$ALIAS_CMD" >> ~/.bashrc
    source ~/.bashrc
fi

echo "commit-gen has been aliased. Please restart your terminal or run 'source ~/.bashrc' (or ~/.zshrc)."