import {
	env,
	createExecutionContext,
	waitOnExecutionContext,
	SELF,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("edge-api worker", () => {
	it("GET / returns app JSON (unit style)", async () => {
		const request = new IncomingRequest("http://example.com/");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(200);
		const body = JSON.parse(await response.text()) as Record<string, unknown>;
		expect(body).toMatchObject({
			app: "edge-api",
			course: "devops-core",
			message: "Hello from Cloudflare Workers",
		});
		expect(body.routes).toEqual(["/", "/health", "/edge", "/deploy", "/counter"]);
		expect(typeof body.timestamp).toBe("string");
	});

	it("GET / returns app JSON (integration style)", async () => {
		const response = await SELF.fetch("https://example.com/");
		expect(response.status).toBe(200);
		const body = JSON.parse(await response.text()) as Record<string, unknown>;
		expect(body.app).toBe("edge-api");
	});

	it("GET /health", async () => {
		const request = new IncomingRequest("http://example.com/health");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({ status: "ok", service: "edge-api" });
	});

	it("GET /counter increments KV", async () => {
		const request = new IncomingRequest("http://example.com/counter");
		const ctx = createExecutionContext();
		const a = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);
		const ja = (await a.json()) as { visits: number };
		const b = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);
		const jb = (await b.json()) as { visits: number };
		expect(jb.visits).toBe(ja.visits + 1);
	});
});
