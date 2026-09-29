# Pinned Ollama with reviewed template/output fixes and native Gemma tool decoding.
FROM golang:1.26.0-bookworm@sha256:2a0ba12e116687098780d3ce700f9ce3cb340783779646aafbabed748fa6677c AS build
WORKDIR /src
ADD https://codeload.github.com/ollama/ollama/tar.gz/refs/tags/v0.34.4 /tmp/ollama.tar.gz
RUN echo 'c265dfff78cd2fe909f9f9fa0bb21b1e34dfcd354e1bfa13ed8eac2cfce90940  /tmp/ollama.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/ollama.tar.gz --strip-components=1 -C /src
COPY template-json.patch unparsed-tool-output.patch /tmp/
RUN echo '25d63f40f90a6e1f5820164faca11655d8cfb9f9c47216c138ceb1baea63784e  /tmp/template-json.patch' | sha256sum -c - \
    && echo '5172a6b076ee7dfadb8052913de5d13fdf963cffb748d7e22eb67dad87fe964f  /tmp/unparsed-tool-output.patch' | sha256sum -c - \
    && git apply --check /tmp/template-json.patch /tmp/unparsed-tool-output.patch \
    && git apply /tmp/template-json.patch /tmp/unparsed-tool-output.patch
# Prove the new template test detects the stock defect, then restore the fix.
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    git apply -R --include=template/template.go /tmp/template-json.patch \
    && if go test -count=1 ./template/ -run '^TestTemplateToolFunctionJSON$' > /tmp/before.txt 2>&1; then cat /tmp/before.txt; exit 1; fi \
    && cat /tmp/before.txt \
    && grep -q 'not valid JSON:' /tmp/before.txt \
    && git apply --include=template/template.go /tmp/template-json.patch \
    && go test -count=1 ./template/... ./thinking/... ./tools/... \
    && go vet ./template/... ./tools/... \
    && CGO_ENABLED=1 go build -trimpath -buildmode=pie \
       -ldflags='-w -s -X github.com/ollama/ollama/version.Version=0.34.4-poc.18391.17284' \
       -o /out/ollama .
# Route Gemma through the bundled native grammar; preserve its string delimiter.
COPY gemma-native-tools.patch /tmp/
RUN echo '42f0afb553b84be729b262f83634e0556e8670ac403f0ee7dbd26ef6ba918ae6  /tmp/gemma-native-tools.patch' | sha256sum -c - \
    && git apply --check /tmp/gemma-native-tools.patch \
    && git apply /tmp/gemma-native-tools.patch
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    git apply -R --include=server/routes.go /tmp/gemma-native-tools.patch \
    && if go test -count=1 ./server/ -run '^TestGemma4NativeToolRoute$' > /tmp/gemma-before.txt 2>&1; then cat /tmp/gemma-before.txt; exit 1; fi \
    && cat /tmp/gemma-before.txt \
    && grep -q 'Gemma tool calls bypass native grammar' /tmp/gemma-before.txt \
    && git apply --include=server/routes.go /tmp/gemma-native-tools.patch \
    && test -z "$(gofmt -l llm/server.go llm/llama_server.go llm/native_template_test.go server/routes.go server/native_gemma4.go server/native_gemma4_test.go)" \
    && go test -count=1 ./llm/... ./server/... ./model/renderers/... ./model/parsers/... ./openai/... \
    && go vet ./llm/... ./server/... \
    && CGO_ENABLED=1 go build -trimpath -buildmode=pie \
       -ldflags='-w -s -X github.com/ollama/ollama/version.Version=0.34.4-poc.gemma-native.2' \
       -o /out/ollama .
# Rebuild only the matching native chat/parser shared library. Keep the pinned
# inference engine, CPU/GPU libraries and model weights from the official image.
FROM build AS native-build
RUN apt-get update && apt-get install -y --no-install-recommends cmake ninja-build && rm -rf /var/lib/apt/lists/*
ADD https://codeload.github.com/ggml-org/llama.cpp/tar.gz/161755f29e415e2c33efe906e91843c068efd664 /tmp/llama.tar.gz
RUN echo 'ea7b03494c2e9f24b5bcb6602c921fa413b868eb7f68fcf299eb6e84e361ea42  /tmp/llama.tar.gz' | sha256sum -c - \
    && mkdir /llama && tar -xzf /tmp/llama.tar.gz --strip-components=1 -C /llama
COPY gemma-preserved-token.patch gemma-native-test.cpp /tmp/
RUN echo 'bca1122698b16a0db55314b96e404cd4ea60c9ebfac4bf7380a04f5619f57fd2  /tmp/gemma-preserved-token.patch' | sha256sum -c - \
    && cmake -S llama/server -B /native -G Ninja \
       -DFETCHCONTENT_SOURCE_DIR_LLAMA_CPP=/llama \
       -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
       -DGGML_BACKEND_DL=ON -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF \
       -DGGML_CPU_ALL_VARIANTS=OFF \
    && cmake --build /native --target llama-common --parallel 4 \
    && g++ -std=c++17 -I/llama/common -I/llama/include -I/llama/ggml/include \
       /tmp/gemma-native-test.cpp -L/native/bin -Wl,-rpath,/native/bin -lllama-common -lllama -o /tmp/gemma-native-test \
    && if /tmp/gemma-native-test /src/server/templates/gemma4-small.jinja > /tmp/native-before.txt 2>&1; then cat /tmp/native-before.txt; exit 1; fi \
    && cat /tmp/native-before.txt \
    && grep -q 'Missing Gemma string delimiter' /tmp/native-before.txt \
    && cd /llama && git apply --check /tmp/gemma-preserved-token.patch && git apply /tmp/gemma-preserved-token.patch \
    && cmake --build /native --target llama-common --parallel 4 \
    && /tmp/gemma-native-test /src/server/templates/gemma4-small.jinja \
    && strip /native/bin/libllama-common.so*
# Generic tool-choice transport, leaving the tested native library layer cached.
FROM build AS tool-choice-build
COPY tool-choice.patch /tmp/
RUN echo '70dd8f868adc85edcf1ff0f8b2a577ee9de48a52a2dc67bc9893a348b088bbec  /tmp/tool-choice.patch' | sha256sum -c - \
    && git apply --check /tmp/tool-choice.patch && git apply /tmp/tool-choice.patch
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    git apply -R --include=llm/llama_server.go /tmp/tool-choice.patch \
    && if go test -count=1 ./llm/ -run '^TestNativeToolChoiceForwarding$' > /tmp/tool-choice-before.txt 2>&1; then cat /tmp/tool-choice-before.txt; exit 1; fi \
    && cat /tmp/tool-choice-before.txt && grep -q 'tool_choice dropped' /tmp/tool-choice-before.txt \
    && git apply --include=llm/llama_server.go /tmp/tool-choice.patch \
    && test -z "$(gofmt -l api/types.go openai/tool_choice.go openai/tool_choice_test.go llm/tool_choice_test.go server/tool_choice.go server/tool_choice_test.go)" \
    && go test -count=1 ./api/... ./openai/... ./llm/... ./server/... \
    && go vet ./api/... ./openai/... ./llm/... ./server/... \
    && CGO_ENABLED=1 go build -trimpath -buildmode=pie \
       -ldflags='-w -s -X github.com/ollama/ollama/version.Version=0.34.4-poc.tool-choice.2' \
       -o /out/ollama .
FROM ollama/ollama:0.34.4@sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551
COPY --from=tool-choice-build /out/ollama /usr/bin/ollama
COPY --from=native-build /native/bin/libllama-common.so* /usr/lib/ollama/
COPY --from=build /src/server/templates/gemma4-small.LICENSE /usr/share/licenses/ollama/gemma4-template.LICENSE
LABEL org.opencontainers.image.description="Ollama 0.34.4 with PRs 18391/17284 and native Gemma tool grammar"
