// Proxy to FastAPI backend
export default async function handler(req, res) {
  const { endpoint, ...params } = req.query;
  const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

  if (!endpoint) {
    return res.status(400).json({ error: 'Missing endpoint parameter' });
  }

  const url = `${backend}/api/${endpoint}`;

  try {
    if (req.method === 'POST') {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body),
      });
      const data = await response.json();
      return res.status(response.status).json(data);
    }

    // GET
    const response = await fetch(url);
    const data = await response.json();
    return res.status(response.status).json(data);
  } catch (error) {
    return res.status(502).json({ detail: `Backend connection failed: ${error.message}` });
  }
}
