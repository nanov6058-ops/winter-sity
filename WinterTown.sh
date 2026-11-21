#!/bin/sh
printf '\033c\033]0;%s\a' WinterTown
base_path="$(dirname "$(realpath "$0")")"
"$base_path/WinterTown.x86_64" "$@"
