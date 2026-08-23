FORK_REPO     = git@github.com:jonathan-david-johnson/pocket-radio-ios.git
MENUBAR_REPO  = git@github.com:jonathan-david-johnson/pocket-radio-menubar.git
ROKU_REPO     = git@github.com:jonathan-david-johnson/pocket-radio-roku.git
WEB_REPO      = git@github.com:jonathan-david-johnson/pocket-radio-web.git
WINDOWS_REPO  = git@github.com:jonathan-david-johnson/pocket-radio-windows.git
ANDROID_REPO  = git@github.com:jonathan-david-johnson/pocket-radio-android.git
UPSTREAM      = git@github.com:Automattic/pocket-casts-ios.git
IOS_DIR       = pocket-radio-ios
MENUBAR_DIR   = pocket-radio-menubar
CONSOLE_DIR   = pocket-radio-console
WEB_DIR       = pocket-radio-web
WINDOWS_DIR   = pocket-radio-windows
ANDROID_DIR   = pocket-radio-android
MENUBAR_PROJ  = $(MENUBAR_DIR)/PocketRadio.xcodeproj
MENUBAR_SCHEME = PocketRadio
ROKU_DIR      = pocket-radio-roku
ROKU_HOST    ?= 10.99.99.50
ROKU_STICK_HOST ?= 10.99.99.54

# Android device serials (default: the single connected device)
ANDROID_TV_SERIAL     ?=
ANDROID_MOBILE_SERIAL ?=

.PHONY: help checkout upstream-remote hooks hooks-check status run_sim menubar menubar-build menubar-run menubar-kill menubar-log menubar-test run_menubar menubar-release install console console-build console-run console-run_upnext console-run_kcrw console-debug console-debug_upnext console-debug_kcrw console-test console-vet roku-build roku-deploy roku-install roku-telnet roku-killtelnet roku-screenshot roku-run roku-deploy-stick roku-install-stick windows windows-build windows-build-exe windows-vet android android-build android-test android-tv android-mobile android-log android-lint android-clean

.DEFAULT_GOAL := help

# Show this help.
help:
	@echo "PocketRadio — make targets"
	@echo ""
	@echo "  Repo setup"
	@echo "    checkout         Clone the iOS, menubar, and Roku repos (skips any that are present)"
	@echo "    upstream-remote  Add the Automattic upstream remote to $(IOS_DIR)"
	@echo "    hooks            Point this repo + all nested repos at .githooks/"
	@echo "    hooks-check      Verify every repo resolves to .githooks/pre-commit"
	@echo ""
	@echo "  Repo status"
	@echo "    status           Show branch and sync status for all submodules"
	@echo "  iOS app (delegates to $(IOS_DIR)/Makefile)"
	@echo "    run_sim          Build, install, and launch on the simulator"
	@echo ""
	@echo "  Console app (delegates to $(CONSOLE_DIR)/Makefile)"
	@echo "    console          Build the console binary"
	@echo "    console-build    Build the console binary"
	@echo "    console-run           Build and launch the full TUI"
	@echo "    console-run_upnext    Build and play the top of Up Next (mini mode)"
	@echo "    console-run_kcrw      Build and play KCRW (mini mode)"
	@echo "    console-debug         Full TUI with debug logging (debug.log)"
	@echo "    console-debug_upnext  Up Next mini mode with debug logging"
	@echo "    console-debug_kcrw    KCRW mini mode with debug logging"
	@echo "    console-test     Run the hermetic test suite"
	@echo "    console-vet      Run go vet"
	@echo ""
	@echo "  Menubar app (dev)"
	@echo "    menubar          Kill, build (Debug), and launch the menubar app"
	@echo "    menubar-build    Build the menubar app (Debug)"
	@echo "    menubar-run      Launch the built Debug app"
	@echo "    menubar-kill     Quit any running menubar app"
	@echo "    menubar-log      Stream unified log output from the running menubar app"
	@echo "    menubar-test     Run menubar unit tests"
	@echo "    run_menubar      Kill and re-launch existing build (no rebuild)"
	@echo ""
	@echo "  Menubar app (install)"
	@echo "    menubar-release  Build Release (ad-hoc signed)"
	@echo "    install          Build Release and copy into /Applications"
	@echo ""
	@echo "  Windows app (delegates to $(WINDOWS_DIR)/Makefile)"
	@echo "    windows          Build the Windows systray binary (current platform)"
	@echo "    windows-build    Build the Windows systray binary (current platform)"
	@echo "    windows-build-exe  Cross-compile .exe from Mac (requires: brew install mingw-w64)"
	@echo "    windows-vet      Run go vet"
	@echo ""
	@echo "  Android apps (delegates to $(ANDROID_DIR)/Makefile — not yet scaffolded, see docs/android)"
	@echo "    android          Assemble both app modules (debug)"
	@echo "    android-build    Assemble both app modules (debug)"
	@echo "    android-test     Run JVM unit tests across :core:*"
	@echo "    android-tv       Install + launch on the TV device (ANDROID_TV_SERIAL)"
	@echo "    android-mobile   Install + launch on the phone device (ANDROID_MOBILE_SERIAL)"
	@echo "    android-log      adb logcat filtered to the app"
	@echo "    android-lint     ktlint + android lint"
	@echo "    android-clean    Gradle clean"
	@echo ""
	@echo "  Web app (delegates to $(WEB_DIR)/Makefile — not yet scaffolded, see docs/web)"
	@echo ""
	@echo "  Roku channel (delegates to $(ROKU_DIR)/Makefile; needs ROKU_PASS env)"
	@echo "    roku-build       Package channel sources into channel.zip"
	@echo "    roku-deploy      Build + sideload to the device"
	@echo "    roku-install     Sideload existing channel.zip"
	@echo "    roku-telnet      Open BrightScript debug console (port 8085)"
	@echo "    roku-killtelnet  Kill any local telnet/nc sessions to the debug console"
	@echo "    roku-screenshot  Pull a device screenshot"
	@echo "    roku-run         Deploy + open debug console (tee /tmp/roku.log)"
	@echo "    roku-deploy-stick   Build + sideload to stick device ($(ROKU_STICK_HOST))"
	@echo "    roku-install-stick  Sideload existing channel.zip to stick device ($(ROKU_STICK_HOST))"
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
	@if [ -d "$(MENUBAR_DIR)/.git" ]; then \
		echo "$(MENUBAR_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(MENUBAR_REPO)..."; \
		git clone $(MENUBAR_REPO) $(MENUBAR_DIR); \
	fi
	@if [ -d "$(ROKU_DIR)/.git" ]; then \
		echo "$(ROKU_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(ROKU_REPO)..."; \
		git clone $(ROKU_REPO) $(ROKU_DIR); \
	fi
	@if [ -d "$(WEB_DIR)/.git" ]; then \
		echo "$(WEB_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(WEB_REPO)..."; \
		git clone $(WEB_REPO) $(WEB_DIR); \
	fi
	@if [ -d "$(WINDOWS_DIR)/.git" ]; then \
		echo "$(WINDOWS_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(WINDOWS_REPO)..."; \
		git clone $(WINDOWS_REPO) $(WINDOWS_DIR); \
	fi
	@if [ -d "$(ANDROID_DIR)/.git" ]; then \
		echo "$(ANDROID_DIR) already cloned — skipping"; \
	else \
		echo "Cloning $(ANDROID_REPO)..."; \
		git clone $(ANDROID_REPO) $(ANDROID_DIR) || \
			echo "$(ANDROID_DIR) not created yet — see docs/android/milestones/milestone_0.md"; \
	fi

upstream-remote:
	@cd $(IOS_DIR) && git remote add upstream $(UPSTREAM) 2>/dev/null || \
		echo "upstream remote already exists"

# ── Git Hooks ────────────────────────────────────────────────
# Point this repo and every nested repo at .githooks/ (one shared copy).
# Scoped to PocketRadio only — never set globally. Re-run after `make checkout`.

hooks:
	@git config core.hooksPath .githooks
	@echo "$(shell pwd) -> .githooks"
	@root="$$(pwd)"; \
	find . -mindepth 2 -maxdepth 4 -name .git -not -path './.git/*' 2>/dev/null | while read -r g; do \
		repo="$$(dirname "$$g")"; \
		rel="$$(python3 -c "import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))" "$$root/.githooks" "$$repo")"; \
		git -C "$$repo" config core.hooksPath "$$rel"; \
		echo "  $$repo -> $$rel"; \
	done
	@echo "Done. Verify with: make hooks-check"

hooks-check:
	@fail=0; \
	for repo in . $$(find . -mindepth 2 -maxdepth 4 -name .git -not -path './.git/*' -exec dirname {} \; 2>/dev/null); do \
		hp="$$(git -C "$$repo" config core.hooksPath 2>/dev/null)"; \
		resolved="$$(cd "$$repo" && cd "$$hp" 2>/dev/null && pwd -P)/pre-commit"; \
		if [ -x "$$resolved" ]; then \
			printf "  ok   %s\n" "$$repo"; \
		else \
			printf "  MISS %s (hooksPath=%s)\n" "$$repo" "$$hp"; fail=1; \
		fi; \
	done; \
	[ "$$fail" = 0 ] && echo "All repos wired to .githooks/pre-commit" || \
		{ echo "Some repos unwired — run: make hooks"; exit 1; }

# ── Repo Status ──────────────────────────────────────────────

SUBMODULES = $(IOS_DIR) $(MENUBAR_DIR) $(ROKU_DIR) $(CONSOLE_DIR) $(WEB_DIR) $(WINDOWS_DIR) $(ANDROID_DIR)

status:
	@for dir in $(SUBMODULES); do \
		if [ -d "$$dir/.git" ]; then \
			branch=$$(git -C "$$dir" branch --show-current 2>/dev/null || echo "(detached)"); \
			if git -C "$$dir" rev-parse '@{u}' >/dev/null 2>&1; then \
				counts=$$(git -C "$$dir" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null); \
				behind=$$(echo "$$counts" | cut -f1); \
				ahead=$$(echo "$$counts" | cut -f2); \
			else \
				behind=0; ahead=0; \
			fi; \
			dirty=$$(git -C "$$dir" status --porcelain 2>/dev/null | wc -l); \
			dirty_str=""; \
			[ "$$dirty" -gt 0 ] && dirty_str=" [dirty]"; \
			printf "%-22s %-12s (↓ %s ↑ %s)%s\n" "$$dir" "$$branch" "$$behind" "$$ahead" "$$dirty_str"; \
		else \
			printf "%-22s (not cloned)\n" "$$dir"; \
		fi; \
	done

# ── iOS App ──────────────────────────────────────────────────
# Real target lives in $(IOS_DIR)/Makefile; this delegates.

run_sim:
	@$(MAKE) -C $(IOS_DIR) run_sim

# ── Console App ──────────────────────────────────────────────
# Real targets live in $(CONSOLE_DIR)/Makefile; these delegate.

console: console-build

console-build:
	@$(MAKE) -C $(CONSOLE_DIR) build

console-run:
	@$(MAKE) -C $(CONSOLE_DIR) run

console-run_upnext:
	@$(MAKE) -C $(CONSOLE_DIR) run_upnext

console-run_kcrw:
	@$(MAKE) -C $(CONSOLE_DIR) run_kcrw

console-debug:
	@$(MAKE) -C $(CONSOLE_DIR) run-debug

console-debug_upnext:
	@$(MAKE) -C $(CONSOLE_DIR) run_upnext-debug

console-debug_kcrw:
	@$(MAKE) -C $(CONSOLE_DIR) run_kcrw-debug

console-test:
	@$(MAKE) -C $(CONSOLE_DIR) test

console-vet:
	@$(MAKE) -C $(CONSOLE_DIR) vet

# ── Menubar App ──────────────────────────────────────────────

# Build & launch the menubar app
menubar: menubar-kill menubar-build menubar-run

menubar-build:
	xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -configuration Debug build

menubar-run:
	open "$$(xcodebuild -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -showBuildSettings -configuration Debug 2>/dev/null | grep ' BUILD_DIR = ' | sed 's/.*= //')/Debug/PocketRadio.app"

menubar-kill:
	@pkill -f "PocketRadio.app/Contents/MacOS/PocketRadio" 2>/dev/null; true

menubar-test:
	xcodebuild test -project $(MENUBAR_PROJ) -scheme $(MENUBAR_SCHEME) -destination 'platform=macOS'

# Kill and re-launch existing build (no rebuild)
menubar-log:
	log stream --predicate 'process == "PocketRadio"' --level debug

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

# ── Windows App ──────────────────────────────────────────────
# Real targets live in $(WINDOWS_DIR)/Makefile; these delegate.

windows: windows-build

windows-build:
	@$(MAKE) -C $(WINDOWS_DIR) build

windows-build-exe:
	@$(MAKE) -C $(WINDOWS_DIR) build-windows

windows-vet:
	@$(MAKE) -C $(WINDOWS_DIR) vet

# ── Android Apps ─────────────────────────────────────────────
# Real targets live in $(ANDROID_DIR)/Makefile; these delegate.
# Repo not scaffolded yet — see docs/android/milestones/milestone_0.md.

android: android-build

android-build:
	@$(MAKE) -C $(ANDROID_DIR) build

android-test:
	@$(MAKE) -C $(ANDROID_DIR) test

android-tv:
	@$(MAKE) -C $(ANDROID_DIR) tv ANDROID_TV_SERIAL=$(ANDROID_TV_SERIAL)

android-mobile:
	@$(MAKE) -C $(ANDROID_DIR) mobile ANDROID_MOBILE_SERIAL=$(ANDROID_MOBILE_SERIAL)

android-log:
	@$(MAKE) -C $(ANDROID_DIR) log

android-lint:
	@$(MAKE) -C $(ANDROID_DIR) lint

android-clean:
	@$(MAKE) -C $(ANDROID_DIR) clean

# ── Roku Channel ─────────────────────────────────────────────
# Real targets live in $(ROKU_DIR)/Makefile; these delegate. Pass ROKU_PASS via env.

roku-build:
	@$(MAKE) -C $(ROKU_DIR) build

roku-deploy:
	@$(MAKE) -C $(ROKU_DIR) deploy

roku-install:
	@$(MAKE) -C $(ROKU_DIR) install

roku-deploy-stick:
	@$(MAKE) -C $(ROKU_DIR) deploy ROKU_HOST=$(ROKU_STICK_HOST)

roku-install-stick:
	@$(MAKE) -C $(ROKU_DIR) install ROKU_HOST=$(ROKU_STICK_HOST)

roku-telnet:
	@$(MAKE) -C $(ROKU_DIR) telnet

roku-killtelnet:
	@$(MAKE) -C $(ROKU_DIR) killtelnet

roku-screenshot:
	@$(MAKE) -C $(ROKU_DIR) screenshot

roku-run:
	@$(MAKE) -C $(ROKU_DIR) deploy
	@echo "Launching channel via ECP..."
	@curl -s -d '' http://$(ROKU_HOST):8060/keypress/Home >/dev/null
	@sleep 1
	@curl -s -d '' http://$(ROKU_HOST):8060/launch/dev >/dev/null
	@sleep 2
	nc $(ROKU_HOST) 8085 | tee /tmp/roku.log
