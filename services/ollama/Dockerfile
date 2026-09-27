# Preserve upstream inference libraries; rebuild only the server with PR #17284.
FROM golang:1.24.13-bookworm AS build
WORKDIR /src
ADD https://codeload.github.com/ollama/ollama/tar.gz/refs/tags/v0.13.5 /tmp/ollama.tar.gz
RUN echo '6b6bc20a52c11341aa296eecce5ee6782f05815224a4196983b0aa2f1453c19f  /tmp/ollama.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/ollama.tar.gz --strip-components=1 -C /src
COPY unparsed-tool-output.patch /tmp/backport.patch
RUN echo '5172a6b076ee7dfadb8052913de5d13fdf963cffb748d7e22eb67dad87fe964f  /tmp/backport.patch' | sha256sum -c - \
    && git apply --check /tmp/backport.patch && git apply /tmp/backport.patch
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    go test -count=1 ./tools/ && go vet ./tools/ \
    && CGO_ENABLED=1 go build -trimpath -buildmode=pie \
       -ldflags='-w -s -X github.com/ollama/ollama/version.Version=0.13.5-poc.17284' \
       -o /out/ollama .
FROM ollama/ollama:0.13.5
COPY --from=build /out/ollama /usr/bin/ollama
LABEL org.opencontainers.image.description="Ollama 0.13.5 with upstream PR 17284 unparsed tool output backport"
