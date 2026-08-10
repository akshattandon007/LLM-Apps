/** Proxy API requests to the FastAPI backend. */
export default async function handler(req, res) {
  const { path } = req.query;
  const apiPath = Array.isArray(path) ? path.join('/') : path;
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  try {
    const response = await fetch(`${backendUrl}/${apiPath}`, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
    });

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (err) {
    res.status(500).json({ error: `Backend request failed: ${err.message}` });
  }
}