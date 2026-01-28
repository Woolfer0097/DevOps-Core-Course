package main

import (
	"encoding/json"
	"net"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
	OperatingSystem string `json:"operating_system"`
}

type RuntimeInfo struct {
	UptimeSeconds int64  `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ServiceInfo struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   RuntimeInfo `json:"runtime"`
	Request   RequestInfo `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

type Health struct {
	Status        string `json:"status"`
	Timestamp     string `json:"timestamp"`
	UptimeSeconds int64  `json:"uptime_seconds"`
}

var startTime = time.Now().UTC()

func getSystemInfo() System {
	hostname, _ := os.Hostname()

	return System{
		Hostname:       hostname,
		Platform:       runtime.GOOS,
		Architecture:   runtime.GOARCH,
		CPUCount:       runtime.NumCPU(),
		GoVersion:      runtime.Version(),
		OperatingSystem: runtime.GOOS,
	}
}

func getRuntimeInfo() RuntimeInfo {
	now := time.Now().UTC()
	delta := now.Sub(startTime)
	seconds := int64(delta.Seconds())
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60

	return RuntimeInfo{
		UptimeSeconds: seconds,
		UptimeHuman:   formatHumanDuration(hours, minutes),
		CurrentTime:   now.Format(time.RFC3339Nano),
		Timezone:      "UTC",
	}
}

func formatHumanDuration(hours, minutes int64) string {
	hLabel := "hours"
	if hours == 1 {
		hLabel = "hour"
	}
	mLabel := "minutes"
	if minutes == 1 {
		mLabel = "minute"
	}
	return strings.TrimSpace(
		strings.Join(
			[]string{
				formatInt(hours) + " " + hLabel + ",",
				formatInt(minutes) + " " + mLabel,
			},
			" ",
		),
	)
}

func formatInt(v int64) string {
	return strconv.FormatInt(v, 10)
}

func getRequestInfo(r *http.Request) RequestInfo {
	clientIP := r.RemoteAddr
	if host, _, err := net.SplitHostPort(r.RemoteAddr); err == nil {
		clientIP = host
	}

	return RequestInfo{
		ClientIP:  clientIP,
		UserAgent: r.UserAgent(),
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

func getEndpoints() []Endpoint {
	return []Endpoint{
		{Path: "/", Method: http.MethodGet, Description: "Service information"},
		{Path: "/health", Method: http.MethodGet, Description: "Health check"},
	}
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service (Go)",
			Framework:   "net/http",
		},
		System:    getSystemInfo(),
		Runtime:   getRuntimeInfo(),
		Request:   getRequestInfo(r),
		Endpoints: getEndpoints(),
	}

	writeJSON(w, http.StatusOK, info)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/health" {
		http.NotFound(w, r)
		return
	}

	runtimeInfo := getRuntimeInfo()
	resp := Health{
		Status:        "healthy",
		Timestamp:     time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: runtimeInfo.UptimeSeconds,
	}

	writeJSON(w, http.StatusOK, resp)
}

func writeJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	addr := host + ":" + port
	if err := http.ListenAndServe(addr, nil); err != nil {
		panic(err)
	}
}

