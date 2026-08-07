/** Next.js API proxy to the FastAPI backend.
 *
 * Maps /api/proxy/* to the FastAPI server at http://localhost:8000/*.
 * Handles both JSON and multipart/form-data requests.
 */

export default async function handler(req, res) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

  // Extract the path after /api/proxy/
  const path = req.url.replace(/^\/api\/proxy/, "");
  const url = `${backendUrl}${path}`;

  try {
    const headers = { ...req.headers };

    // Remove hop-by-hop headers
    delete headers.host;
    delete headers["content-length"];

    const options = {
      method: req.method,
      headers,
      body: req.method !== "GET" && req.method !== "HEAD"
        ? JSON.stringify(req.body)
        : undefined,
    };

    // For multipart uploads, don't stringify the body
    if (req.headers["content-type"]?.includes("multipart/form-data")) {
      // Forward the raw body as a buffer
      const rawBody = await new Promise((resolve) => {
        const chunks = [];
        req.on("data", (chunk) => chunks.push(chunk));
        req.on("end", () => resolve(Buffer.concat(chunks)));
      });
      options.body = rawBody;
      // Remove content-type so fetch auto-sets the boundary
      delete options.headers["content-type"];
      // Set raw content-type
      options.headers["Content-Type"] = req.headers["content-type"];
    } else if (req.method !== "GET" && req.method !== "HEAD") {
      options.body = JSON.stringify(req.body);
      options.headers["Content-Type"] = "application/json";
    }

    const backendRes = await fetch(url, options);
    const data = await backendRes.json();

    res.status(backendRes.status).json(data);
  } catch (err) {
    res.status(502).json({
      error: "Backend proxy error",
      detail: err.message,
    });
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};