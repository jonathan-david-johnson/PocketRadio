FORK_REPO    = git@github.com:jonathan-david-johnson/pocket-casts-ios.git
UPSTREAM     = git@github.com:Automattic/pocket-casts-ios.git
IOS_DIR      = pocket-casts-ios
MENUBAR_DIR  = pocket-radio-menubar
MENUBAR_PROJ = $(MENUBAR_DIR)/PocketRadio.xcodeproj
MENUBAR_SCHEME = PocketRadio

.PHONY: help checkout upstream-remote menubar menubar-build menubar-run menubar-kill run_menubar menubar-release install

.DEFAULT_GOAL := help

# Show this help.
help:
	@echo "PocketRadio — make targets"
	@echo ""
	@echo "  Repo setup"
	@echo "    checkout         Clone the iOS fork into $(IOS_DIR) (skips if present); set upstream remote"
	@echo "    upstream-remote  Add the Automattic upstream remote to $(IOS_DIR)"
	@echo ""
	@echo "  Menubar app (dev)"
	@echo "    menubar          Kill, build (Debug), and launch the menubar app"
	@echo "    menubar-build    Build the menubar app (Debug)"
	@echo "    menubar-run      Launch the built Debug app"
	@echo "    menubar-kill     Quit any running menubar app"
	@echo "    run_menubar      Kill and re-launch existing build (no rebuild)"
	@echo ""
	@echo "  Menubar app (install)"
	@echo "    menubar-release  Build Release (ad-hoc signed)"
	@echo "    install          Build Release and copy into /Applications"
	@echo ""
	@echo "    help             Show this help"

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

# ── Installation ─────────────────────────────────────────────

# Build Release config of menubar app (ad-hoc signed for personal use).
menubar-release:
	xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -configuration Release build CODE_SIGN_IDENTITY=- CODE_SIGNING_REQUIRED=NO

# Build Release and copy into /Applications. Kills any running copy first.
# After install:
#   1. Open /Applications/PocketRadio.app once to register it.
#   2. System Settings -> General -> Login Items -> Open at Login: add PocketRadio.
install: menubar-kill menubar-release
	@RELEASE_DIR=$$(xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -showBuildSettings -configuration Release 2>/dev/null | grep ' BUILD_DIR = ' | sed 's/.*= //')/Release ; \
	if [ ! -d "$$RELEASE_DIR/PocketRadio.app" ]; then \
		echo "Build artifact not found at $$RELEASE_DIR/PocketRadio.app"; exit 1; \
	fi ; \
	echo "Removing old /Applications/PocketRadio.app (if any)..." ; \
	rm -rf /Applications/PocketRadio.app ; \
	echo "Copying $$RELEASE_DIR/PocketRadio.app -> /Applications/" ; \
	cp -R "$$RELEASE_DIR/PocketRadio.app" /Applications/ ; \
	echo "" ; \
	echo "Installed. Next steps:" ; \
	echo "  open /Applications/PocketRadio.app   # first launch (Gatekeeper may prompt)" ; \
	echo "  Then: System Settings -> General -> Login Items -> Open at Login -> + PocketRadio"
