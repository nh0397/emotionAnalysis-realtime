import React, { useState } from 'react';

export default function ChatbotPanel() {
  const [q, setQ] = useState('');
  const [resp, setResp] = useState(null);
  const ask = async () => {
    const r = await fetch('http://localhost:9000/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ question: q })
    });
    setResp(await r.json());
  };
  return (
    <div style={{padding: 12, border: '1px solid #ddd'}}>
      <input style={{width: '70%'}} value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask in English..." />
      <button onClick={ask} style={{marginLeft: 8}}>Ask</button>
      <pre style={{marginTop: 12}}>{resp ? JSON.stringify(resp, null, 2) : null}</pre>
    </div>
  );
}
