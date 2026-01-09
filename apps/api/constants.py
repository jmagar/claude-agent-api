"""Constants for the API."""

# Built-in tools list
BUILT_IN_TOOLS: tuple[str, ...] = (
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "Bash",
    "Glob",
    "Grep",
    "LS",
    "WebFetch",
    "WebSearch",
    "Task",
    "TodoWrite",
    "NotebookEdit",
    "NotebookRead",
    "AskUserQuestion",
    "Skill",  # T116c: Skill tool for invoking skills
    "SlashCommand",  # Slash command invocation
)
