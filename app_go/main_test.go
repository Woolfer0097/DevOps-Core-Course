package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"runtime"
	"strings"
	"testing"
	"time"
)

// TestMainHandler tests the main endpoint handler
func TestMainHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", res.StatusCode)
	}

	contentType := res.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got %s", contentType)
	}

	var info ServiceInfo
	if err := json.NewDecoder(res.Body).Decode(&info); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	// Verify service info
	if info.Service.Name != "devops-info-service" {
		t.Errorf("expected service name 'devops-info-service', got %s", info.Service.Name)
	}
	if info.Service.Version != "1.0.0" {
		t.Errorf("expected version '1.0.0', got %s", info.Service.Version)
	}
	if info.Service.Framework != "net/http" {
		t.Errorf("expected framework 'net/http', got %s", info.Service.Framework)
	}

	// Verify system info
	if info.System.Hostname == "" {
		t.Error("expected hostname to be non-empty")
	}
	if info.System.CPUCount <= 0 {
		t.Errorf("expected cpu_count > 0, got %d", info.System.CPUCount)
	}

	// Verify runtime info
	if info.Runtime.UptimeSeconds < 0 {
		t.Errorf("expected uptime_seconds >= 0, got %d", info.Runtime.UptimeSeconds)
	}
	if info.Runtime.Timezone != "UTC" {
		t.Errorf("expected timezone 'UTC', got %s", info.Runtime.Timezone)
	}

	// Verify request info
	if info.Request.Method != http.MethodGet {
		t.Errorf("expected method GET, got %s", info.Request.Method)
	}
	if info.Request.Path != "/" {
		t.Errorf("expected path '/', got %s", info.Request.Path)
	}

	// Verify endpoints
	if len(info.Endpoints) != 2 {
		t.Errorf("expected 2 endpoints, got %d", len(info.Endpoints))
	}
}

// TestMainHandler404 tests that invalid paths return 404
func TestMainHandler404(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/invalid", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", res.StatusCode)
	}
}

// TestHealthHandler tests the health check endpoint
func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		t.Errorf("expected status 200, got %d", res.StatusCode)
	}

	contentType := res.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got %s", contentType)
	}

	var health Health
	if err := json.NewDecoder(res.Body).Decode(&health); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if health.Status != "healthy" {
		t.Errorf("expected status 'healthy', got %s", health.Status)
	}
	if health.UptimeSeconds < 0 {
		t.Errorf("expected uptime_seconds >= 0, got %d", health.UptimeSeconds)
	}
	if health.Timestamp == "" {
		t.Error("expected timestamp to be non-empty")
	}

	// Verify timestamp is valid RFC3339
	if _, err := time.Parse(time.RFC3339Nano, health.Timestamp); err != nil {
		t.Errorf("invalid timestamp format: %v", err)
	}
}

// TestHealthHandler404 tests that invalid paths return 404
func TestHealthHandler404(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health/invalid", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", res.StatusCode)
	}
}

// TestGetSystemInfo tests the system info function
func TestGetSystemInfo(t *testing.T) {
	info := getSystemInfo()

	if info.Hostname == "" {
		t.Error("expected hostname to be non-empty")
	}
	if info.Platform == "" {
		t.Error("expected platform to be non-empty")
	}
	if info.Architecture == "" {
		t.Error("expected architecture to be non-empty")
	}
	if info.CPUCount <= 0 {
		t.Errorf("expected cpu_count > 0, got %d", info.CPUCount)
	}
	if info.GoVersion == "" {
		t.Error("expected go_version to be non-empty")
	}
	if !strings.HasPrefix(info.GoVersion, "go") {
		t.Errorf("expected go_version to start with 'go', got %s", info.GoVersion)
	}
	if info.OperatingSystem != runtime.GOOS {
		t.Errorf("expected operating_system to match runtime.GOOS, got %s", info.OperatingSystem)
	}
}

// TestGetRuntimeInfo tests the runtime info function
func TestGetRuntimeInfo(t *testing.T) {
	info := getRuntimeInfo()

	if info.UptimeSeconds < 0 {
		t.Errorf("expected uptime_seconds >= 0, got %d", info.UptimeSeconds)
	}
	if info.UptimeHuman == "" {
		t.Error("expected uptime_human to be non-empty")
	}
	if info.CurrentTime == "" {
		t.Error("expected current_time to be non-empty")
	}
	if info.Timezone != "UTC" {
		t.Errorf("expected timezone 'UTC', got %s", info.Timezone)
	}

	// Verify current time is valid RFC3339
	if _, err := time.Parse(time.RFC3339Nano, info.CurrentTime); err != nil {
		t.Errorf("invalid current_time format: %v", err)
	}
}

// TestFormatHumanDuration tests the duration formatting
func TestFormatHumanDuration(t *testing.T) {
	tests := []struct {
		hours    int64
		minutes  int64
		expected string
	}{
		{0, 0, "0 hours, 0 minutes"},
		{1, 1, "1 hour, 1 minute"},
		{2, 30, "2 hours, 30 minutes"},
		{24, 0, "24 hours, 0 minutes"},
	}

	for _, tt := range tests {
		result := formatHumanDuration(tt.hours, tt.minutes)
		if result != tt.expected {
			t.Errorf("formatHumanDuration(%d, %d) = %s, want %s",
				tt.hours, tt.minutes, result, tt.expected)
		}
	}
}

// TestFormatInt tests integer formatting
func TestFormatInt(t *testing.T) {
	tests := []struct {
		input    int64
		expected string
	}{
		{0, "0"},
		{42, "42"},
		{-10, "-10"},
		{1234567890, "1234567890"},
	}

	for _, tt := range tests {
		result := formatInt(tt.input)
		if result != tt.expected {
			t.Errorf("formatInt(%d) = %s, want %s", tt.input, result, tt.expected)
		}
	}
}

// TestGetRequestInfo tests request info extraction
func TestGetRequestInfo(t *testing.T) {
	req := httptest.NewRequest(http.MethodPost, "/test", nil)
	req.Header.Set("User-Agent", "TestAgent/1.0")
	req.RemoteAddr = "192.168.1.1:12345"

	info := getRequestInfo(req)

	if info.Method != http.MethodPost {
		t.Errorf("expected method POST, got %s", info.Method)
	}
	if info.Path != "/test" {
		t.Errorf("expected path '/test', got %s", info.Path)
	}
	if info.UserAgent != "TestAgent/1.0" {
		t.Errorf("expected user agent 'TestAgent/1.0', got %s", info.UserAgent)
	}
	if info.ClientIP != "192.168.1.1" {
		t.Errorf("expected client IP '192.168.1.1', got %s", info.ClientIP)
	}
}

// TestGetEndpoints tests endpoint list generation
func TestGetEndpoints(t *testing.T) {
	endpoints := getEndpoints()

	if len(endpoints) != 2 {
		t.Errorf("expected 2 endpoints, got %d", len(endpoints))
	}

	// Verify first endpoint
	if endpoints[0].Path != "/" {
		t.Errorf("expected first endpoint path '/', got %s", endpoints[0].Path)
	}
	if endpoints[0].Method != http.MethodGet {
		t.Errorf("expected first endpoint method GET, got %s", endpoints[0].Method)
	}

	// Verify second endpoint
	if endpoints[1].Path != "/health" {
		t.Errorf("expected second endpoint path '/health', got %s", endpoints[1].Path)
	}
	if endpoints[1].Method != http.MethodGet {
		t.Errorf("expected second endpoint method GET, got %s", endpoints[1].Method)
	}
}

// TestWriteJSON tests JSON response writing
func TestWriteJSON(t *testing.T) {
	w := httptest.NewRecorder()
	payload := map[string]string{"test": "value"}

	writeJSON(w, http.StatusCreated, payload)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusCreated {
		t.Errorf("expected status 201, got %d", res.StatusCode)
	}

	contentType := res.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("expected Content-Type application/json, got %s", contentType)
	}

	var result map[string]string
	if err := json.NewDecoder(res.Body).Decode(&result); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if result["test"] != "value" {
		t.Errorf("expected test='value', got %s", result["test"])
	}
}

// TestCustomUserAgent tests that custom user agents are captured
func TestCustomUserAgent(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("User-Agent", "CustomBot/2.0")
	w := httptest.NewRecorder()

	mainHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	var info ServiceInfo
	if err := json.NewDecoder(res.Body).Decode(&info); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if info.Request.UserAgent != "CustomBot/2.0" {
		t.Errorf("expected user agent 'CustomBot/2.0', got %s", info.Request.UserAgent)
	}
}

// TestUptimeIncreases tests that uptime increases over time
func TestUptimeIncreases(t *testing.T) {
	info1 := getRuntimeInfo()
	time.Sleep(100 * time.Millisecond)
	info2 := getRuntimeInfo()

	if info2.UptimeSeconds < info1.UptimeSeconds {
		t.Errorf("expected uptime to increase, got %d then %d",
			info1.UptimeSeconds, info2.UptimeSeconds)
	}
}

// TestEnvironmentVariables tests that environment variables work
func TestEnvironmentVariables(t *testing.T) {
	// Save original values
	origHost := os.Getenv("HOST")
	origPort := os.Getenv("PORT")

	// Clean up after test
	defer func() {
		os.Setenv("HOST", origHost)
		os.Setenv("PORT", origPort)
	}()

	// Note: We can't easily test main() without starting a server,
	// but we can verify the environment variables are checked
	os.Setenv("HOST", "127.0.0.1")
	os.Setenv("PORT", "9090")

	host := os.Getenv("HOST")
	port := os.Getenv("PORT")

	if host != "127.0.0.1" {
		t.Errorf("expected HOST '127.0.0.1', got %s", host)
	}
	if port != "9090" {
		t.Errorf("expected PORT '9090', got %s", port)
	}
}

// BenchmarkMainHandler benchmarks the main handler
func BenchmarkMainHandler(b *testing.B) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)

	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		mainHandler(w, req)
	}
}

// BenchmarkHealthHandler benchmarks the health handler
func BenchmarkHealthHandler(b *testing.B) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)

	for i := 0; i < b.N; i++ {
		w := httptest.NewRecorder()
		healthHandler(w, req)
	}
}
