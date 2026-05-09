FORK_REPO    = git@github.com:jonathan-david-johnson/pocket-casts-ios.git
UPSTREAM     = git@github.com:Automattic/pocket-casts-ios.git
IOS_DIR      = pocket-casts-ios

.PHONY: checkout upstream-remote

checkout:
	@if [ -d "$(IOS_DIR)/.git" ]; then \
		echo "$(IOS_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(FORK_REPO)..."; \
		git clone $(FORK_REPO) $(IOS_DIR); \
		cd $(IOS_DIR) && git remote add upstream $(UPSTREAM); \
		echo "Done. Upstream remote set to Automattic/pocket-casts-ios"; \
	fi

upstream-remote:
	@cd $(IOS_DIR) && git remote add upstream $(UPSTREAM) 2>/dev/null || \
		echo "upstream remote already exists"
