## Stage 1: Builder
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Cache modules first
COPY go.mod ./
RUN go mod download

# Copy source
COPY . .

# Build statically-linked binary (simple CGO-disabled build)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o devops-info-service-go .

## Stage 2: Runtime
FROM alpine:3.20

WORKDIR /app

# Non-root user for security
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only the compiled binary from builder image
COPY --from=builder /app/devops-info-service-go /app/devops-info-service-go

USER appuser

EXPOSE 8080

ENV HOST=0.0.0.0
ENV PORT=8080

ENTRYPOINT ["/app/devops-info-service-go"]

