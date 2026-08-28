HOOKS_DIR := hooks
BIN_DIR := $(HOOKS_DIR)/bin

HOOK_SRCS := $(wildcard $(HOOKS_DIR)/*/main.go)
HOOK_BINS := $(patsubst $(HOOKS_DIR)/%/main.go,$(BIN_DIR)/%,$(HOOK_SRCS))

.PHONY: all build-all clean $(notdir $(HOOK_BINS))

all: build-all

build-all: $(HOOK_BINS)

$(BIN_DIR)/%: $(HOOKS_DIR)/%/main.go $(HOOKS_DIR)/%/go.mod
	@mkdir -p $(BIN_DIR)
	cd $(HOOKS_DIR)/$* && go build -o ../bin/$* .

# Alias per hook name (e.g. `make git-branch-guard`) pointing at its binary.
define hook_alias
$(notdir $1): $1
endef
$(foreach b,$(HOOK_BINS),$(eval $(call hook_alias,$b)))

clean:
	rm -rf $(BIN_DIR)
