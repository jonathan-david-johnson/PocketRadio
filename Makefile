FORK_REPO    = git@github.com:jonathan-david-johnson/pocket-casts-ios.git
UPSTREAM     = git@github.com:Automattic/pocket-casts-ios.git
IOS_DIR      = pocket-casts-ios
MENUBAR_DIR  = pocket-radio-menubar
MENUBAR_PROJ = $(MENUBAR_DIR)/PocketRadio.xcodeproj
MENUBAR_SCHEME = PocketRadio

.PHONY: checkout upstream-remote menubar menubar-build menubar-run menubar-kill run_menubar

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

# ── Menubar App ──────────────────────────────────────────────

# Build & launch the menubar app
menubar: menubar-kill menubar-build menubar-run

menubar-build:
	xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -configuration Debug build

menubar-run:
	open "$$(xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -showBuildSettings -configuration Debug 2>/dev/null | grep ' BUILD_DIR = ' | sed 's/.*= //')/Debug/PocketRadio.app"

menubar-kill:
	@pkill -f "PocketRadio.app/Contents/MacOS/PocketRadio" 2>/dev/null; true

# Kill and re-launch existing build (no rebuild)
run_menubar: menubar-kill menubar-run
