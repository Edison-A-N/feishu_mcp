.PHONY: build clean

build:
	@echo "Building feishu-mcp binary..."
	python -m PyInstaller \
		--name feishu-mcp \
		--onefile \
		--console \
		--clean \
		--noupx \
		--hidden-import mcp.server.fastmcp \
		--hidden-import mcp.types \
		--hidden-import feishu_mcp_sdk \
		--hidden-import feishu_mcp_sdk.config \
		--hidden-import feishu_mcp_sdk.api \
		--hidden-import feishu_mcp_sdk.api.client \
		--hidden-import feishu_mcp_sdk.api.exceptions \
		--collect-all mcp \
		--collect-all fastapi \
		--collect-all pydantic \
		--collect-all lark_oapi \
		src/feishu_mcp_sdk/server.py
	@echo "Build completed! Binary location: dist/feishu-mcp"

clean:
	rm -rf build dist *.spec
	@echo "Cleaned build artifacts"

