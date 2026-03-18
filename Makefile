

# Root Makefile for Treasure Runner Project

DIST_DIR       := ./dist
PUZZLEGEN_SO := $(DIST_DIR)/libpuzzlegen.so

# Build student code 
backend:
	@$(MAKE) -C c all

# Prepare distribution: build .so files and copy to dist/
dist: setup-lib backend
	@mkdir -p dist
	@cp c/lib/libbackend.so dist/


# Clean all build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@$(MAKE) -C c clean



#------------------
# setup puzzlegen library in dist/
#------------------
.PHONY: setup-lib
setup-lib:
	@arch=$$(dpkg --print-architecture 2>/dev/null || uname -m); \
	if [ "$$arch" = "amd64" ] || [ "$$arch" = "x86_64" ]; then \
		cp $(DIST_DIR)/libpuzzlegen-linux-amd64.so $(PUZZLEGEN_SO); \
		echo "Using libpuzzlegen-linux-amd64.so"; \
	else \
		cp $(DIST_DIR)/libpuzzlegen-linux-arm64.so $(PUZZLEGEN_SO); \
		echo "Using libpuzzlegen-linux-arm64.so"; \
	fi

