/**
 * Edge API — Lab 17 Cloudflare Worker
 */

type WorkerBindings = Env & {
	API_TOKEN: string;
	ADMIN_EMAIL: string;
};

export default {
	async fetch(request, env: WorkerBindings, _ctx): Promise<Response> {
		const url = new URL(request.url);
		console.log("request", url.pathname, "colo", request.cf?.colo);

		if (request.method === "OPTIONS") {
			return new Response(null, { status: 204 });
		}

		if (url.pathname === "/health") {
			return Response.json({ status: "ok", service: env.APP_NAME });
		}

		if (url.pathname === "/edge") {
			const cf = request.cf;
			return Response.json({
				colo: cf?.colo,
				country: cf?.country,
				city: cf?.city,
				asn: cf?.asn,
				httpProtocol: cf?.httpProtocol,
				tlsVersion: cf?.tlsVersion,
			});
		}

		if (url.pathname === "/deploy") {
			return Response.json({
				worker: "edge-api",
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				label: env.DEPLOYMENT_LABEL,
				adminContact: maskEmail(env.ADMIN_EMAIL),
				timestamp: new Date().toISOString(),
			});
		}

		if (url.pathname === "/counter") {
			if (request.method === "POST" && url.searchParams.get("reset") === "1") {
				const token = request.headers.get("Authorization")?.replace(/^Bearer\s+/i, "") ?? "";
				if (token !== env.API_TOKEN) {
					return Response.json({ error: "unauthorized" }, { status: 401 });
				}
				await env.SETTINGS.put("visits", "0");
				return Response.json({ visits: 0, reset: true });
			}
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return Response.json({ visits, storedKey: "visits" });
		}

		if (url.pathname === "/" || url.pathname === "") {
			return Response.json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				message: "Hello from Cloudflare Workers",
				routes: ["/", "/health", "/edge", "/deploy", "/counter"],
				timestamp: new Date().toISOString(),
			});
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<WorkerBindings>;

function maskEmail(email: string): string {
	if (!email || !email.includes("@")) return "(not set)";
	const [local, domain] = email.split("@");
	const safeLocal = local.length <= 2 ? "**" : `${local.slice(0, 2)}…`;
	return `${safeLocal}@${domain}`;
}
