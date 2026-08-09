// Proxy to FastAPI backend running on port 8000
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export default async function handler(req, res) {
  const { endpoint, ...params } = req.query;
  
  if (!endpoint) {
    return res.status(400).json({ detail: 'Missing endpoint parameter' });
  }

  // Build the target URL
  const url = new URL(`/api/${endpoint}`, BACKEND_URL);
  
  // Forward query params
  Object.entries(params).forEach(([key, val]) => {
    if (key !== 'endpoint') url.searchParams.set(key, val);
  });

  try {
    // For file uploads, forward the body as-is (FormData)
    const headers = {};
    let body = undefined;

    if (req.method === 'POST' && !req.headers['content-type']?.includes('multipart/form-data')) {
      // JSON body — read from the request
      if (req.body) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(req.body);
      }
    }

    const response = await fetch(url.toString(), {
      method: req.method,
      headers,
      body,
    });

    const data = await response.json();

    // For file uploads, forward as 200 with JSON
    if (req.headers['content-type']?.includes('multipart/form-data')) {
      // Express won't parse multipart in serverless easily,
      // so we build a new FormData and forward it
      return res.status(response.status).json(data);
    }

    res.status(response.status).json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(502).json({ detail: `Backend unreachable: ${error.message}` });
  }
}