#!/bin/bash

command_file="runs.txt"   # Replace with your actual file name
temp_file="temp.txt"
max_concurrent=128

active_pids=()

# Make a copy of the command file to work with
cp "$command_file" "$temp_file"

# Function to launch a command and track its PID (same as before)
launch_command() {
    command=$(head -n 1 "$temp_file")
    echo "Launching: $command"
    eval "$command" &
    active_pids+=($!)
    sed -i '1d' "$temp_file"
}

while [ -s "$temp_file" ]  # Work with the temporary copy
do
    while [ ${#active_pids[@]} -lt $max_concurrent ]
    do
        launch_command
    done

    wait -n

    for i in "${!active_pids[@]}"; do
        if ! ps -p "${active_pids[i]}" > /dev/null; then
            unset "active_pids[$i]"
        fi
    done
done

wait
echo "All commands completed."

# Optionally, remove the temporary file:
rm "$temp_file"