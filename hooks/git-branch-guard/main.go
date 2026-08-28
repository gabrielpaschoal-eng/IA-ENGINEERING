// Command git-branch-guard is a Claude Code PreToolUse hook for Bash: it blocks
// configured git subcommands (e.g. commit, push) when the current branch is on
// the protected list. Config path: arg1, else $GIT_GUARD_CONFIG, else
// <this binary's dir>/../config/git-guard.json.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

type config struct {
	ProtectedBranches []string `json:"protectedBranches"`
	BlockedCommands   []string `json:"blockedCommands"`
	ExemptRepos       []string `json:"exemptRepos"`
}

type hookInput struct {
	ToolInput struct {
		Command string `json:"command"`
	} `json:"tool_input"`
}

var assignmentRe = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*=`)

// gitOptsWithValue are git global options that consume the following token as
// their value, so the real subcommand isn't mistaken for an option value.
var gitOptsWithValue = map[string]bool{
	"-C": true, "-c": true, "--git-dir": true, "--work-tree": true, "--namespace": true,
}

func main() {
	configPath := resolveConfigPath()
	cfg, ok := loadConfig(configPath)
	if !ok || len(cfg.BlockedCommands) == 0 {
		os.Exit(0)
	}

	var input hookInput
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil || input.ToolInput.Command == "" {
		os.Exit(0)
	}

	repoRoot, err := gitOutput("rev-parse", "--show-toplevel")
	if err != nil || repoRoot == "" {
		os.Exit(0)
	}
	if contains(cfg.ExemptRepos, repoRoot) {
		os.Exit(0)
	}

	blocked := ""
	for _, words := range splitCommands(input.ToolInput.Command) {
		if sc := gitSubcommand(words); sc != "" && contains(cfg.BlockedCommands, sc) {
			blocked = sc
			break
		}
	}
	if blocked == "" {
		os.Exit(0)
	}

	branch, err := gitOutput("rev-parse", "--abbrev-ref", "HEAD")
	if err != nil || branch == "" || !contains(cfg.ProtectedBranches, branch) {
		os.Exit(0)
	}

	deny(branch, configPath)
}

func resolveConfigPath() string {
	if len(os.Args) > 1 && os.Args[1] != "" {
		return os.Args[1]
	}
	if v := os.Getenv("GIT_GUARD_CONFIG"); v != "" {
		return v
	}
	if exe, err := os.Executable(); err == nil {
		return filepath.Join(filepath.Dir(exe), "..", "config", "git-guard.json")
	}
	return "config/git-guard.json"
}

func loadConfig(path string) (config, bool) {
	var cfg config
	data, err := os.ReadFile(path)
	if err != nil {
		return cfg, false
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return cfg, false
	}
	return cfg, true
}

func gitOutput(args ...string) (string, error) {
	out, err := exec.Command("git", args...).Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

func contains(list []string, v string) bool {
	for _, item := range list {
		if item == v {
			return true
		}
	}
	return false
}

// splitCommands tokenizes a shell command line (quote-aware) and splits it on
// ;, &, &&, ||, |, and subshell parens, returning each command's word list.
func splitCommands(cmd string) [][]string {
	tokens := tokenize(cmd)
	separators := map[string]bool{";": true, "&": true, "&&": true, "||": true, "|": true, "(": true, ")": true}

	var commands [][]string
	var cur []string
	for _, t := range tokens {
		if separators[t] {
			if len(cur) > 0 {
				commands = append(commands, cur)
				cur = nil
			}
			continue
		}
		cur = append(cur, t)
	}
	if len(cur) > 0 {
		commands = append(commands, cur)
	}
	return commands
}

func tokenize(cmd string) []string {
	var tokens []string
	var cur strings.Builder
	inSingle, inDouble := false, false

	flush := func() {
		if cur.Len() > 0 {
			tokens = append(tokens, cur.String())
			cur.Reset()
		}
	}

	runes := []rune(cmd)
	for i := 0; i < len(runes); i++ {
		c := runes[i]
		switch {
		case inSingle:
			if c == '\'' {
				inSingle = false
			} else {
				cur.WriteRune(c)
			}
		case inDouble:
			if c == '"' {
				inDouble = false
			} else if c == '\\' && i+1 < len(runes) && strings.ContainsRune(`"\$`, runes[i+1]) {
				i++
				cur.WriteRune(runes[i])
			} else {
				cur.WriteRune(c)
			}
		case c == '\'':
			inSingle = true
		case c == '"':
			inDouble = true
		case c == '\\':
			if i+1 < len(runes) {
				i++
				cur.WriteRune(runes[i])
			}
		case c == ' ' || c == '\t' || c == '\n':
			flush()
		case c == ';' || c == '|' || c == '&' || c == '(' || c == ')':
			flush()
			if (c == '|' || c == '&') && i+1 < len(runes) && runes[i+1] == c {
				tokens = append(tokens, string(c)+string(c))
				i++
			} else {
				tokens = append(tokens, string(c))
			}
		default:
			cur.WriteRune(c)
		}
	}
	flush()
	return tokens
}

// gitSubcommand returns the git subcommand of a command's word list ("" if
// it isn't a git invocation), skipping leading env-var assignments and git's
// own global options.
func gitSubcommand(words []string) string {
	i := 0
	for i < len(words) && assignmentRe.MatchString(words[i]) {
		i++
	}
	if i >= len(words) || words[i] != "git" {
		return ""
	}
	i++
	for i < len(words) {
		a := words[i]
		if strings.HasPrefix(a, "-") {
			if gitOptsWithValue[a] && !strings.Contains(a, "=") {
				i++
			}
			i++
			continue
		}
		return a
	}
	return ""
}

func deny(branch, configPath string) {
	reason := fmt.Sprintf("Comando bloqueado na branch protegida '%s' (config: %s). Crie e mude para outra branch antes (git checkout -b <nome>), ou ajuste protectedBranches/blockedCommands/exemptRepos no JSON.", branch, configPath)
	output := map[string]any{
		"hookSpecificOutput": map[string]any{
			"hookEventName":            "PreToolUse",
			"permissionDecision":       "deny",
			"permissionDecisionReason": reason,
		},
	}
	_ = json.NewEncoder(os.Stdout).Encode(output)
	os.Exit(0)
}
