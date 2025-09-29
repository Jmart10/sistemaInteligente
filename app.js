const mapDiv = document.getElementById("map");

// 🔹 Lista de nodos (dataset completo)
const allNodes = [
  "A1","A2","A3","A4","A5","A6",
  "B1","B2","B3","B4","B5","B6",
  "C1","C2","C3","C4","C5","C6",
  "D1","D2","D3","D4",
  "E1","E2","E3"
];

// 🔹 Posiciones fijas para cada nodo (ejemplo visual, puedes ajustarlas)
const positions = {
  A1: { x: 50,  y: 50 },  A2: { x: 120, y: 50 },  A3: { x: 190, y: 50 },
  A4: { x: 260, y: 50 },  A5: { x: 330, y: 50 },  A6: { x: 400, y: 50 },

  B1: { x: 50,  y: 120 }, B2: { x: 120, y: 120 }, B3: { x: 190, y: 120 },
  B4: { x: 260, y: 120 }, B5: { x: 330, y: 120 }, B6: { x: 400, y: 120 },

  C1: { x: 50,  y: 190 }, C2: { x: 120, y: 190 }, C3: { x: 190, y: 190 },
  C4: { x: 260, y: 190 }, C5: { x: 330, y: 190 }, C6: { x: 400, y: 190 },

  D1: { x: 500, y: 50 },  D2: { x: 570, y: 50 },  D3: { x: 570, y: 120 },
  D4: { x: 500, y: 120 },

  E1: { x: 500, y: 200 }, E2: { x: 570, y: 200 }, E3: { x: 640, y: 200 },
};

// 🔹 Dibuja todos los nodos en el mapa
function drawNodes(route = [], transfers = []) {
  mapDiv.innerHTML = "";

  for (const [id, pos] of Object.entries(positions)) {
    const node = document.createElement("div");
    node.className = "node";
    node.style.left = pos.x + "px";
    node.style.top = pos.y + "px";
    node.innerText = id;

    if (route.includes(id)) node.classList.add("route");
    if (transfers.includes(id)) node.classList.add("transfer");

    mapDiv.appendChild(node);
  }

  // 🔹 Dibujar líneas entre nodos de la ruta
  for (let i = 0; i < route.length - 1; i++) {
    const a = positions[route[i]];
    const b = positions[route[i + 1]];
    if (!a || !b) continue;

    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * (180 / Math.PI);

    const line = document.createElement("div");
    line.className = "line";
    line.style.width = length + "px";
    line.style.height = "2px";
    line.style.left = a.x + 20 + "px";
    line.style.top = a.y + 20 + "px";
    line.style.transform = `rotate(${angle}deg)`;
    mapDiv.appendChild(line);
  }
}

// 🔹 Inicial (dibuja todos sin ruta)
drawNodes();

document.getElementById('btn').onclick = async () => {
  const origin = document.getElementById('origin').value;
  const destination = document.getElementById('destination').value;
  const prefs = {
    avoid_transfers: document.getElementById('avoid_transfers').checked,
    wheelchair: document.getElementById('wheelchair').checked,
    prefer_fastest: true,
    avoid_crowded: document.getElementById('avoid_crowded').checked,
    safe_priority: document.getElementById('safe_priority').checked,
    budget: parseInt(document.getElementById('budget').value) || null
  };

  const resDiv = document.getElementById('result');
  resDiv.innerHTML = 'Calculando...';

  try {
    const res = await fetch('http://127.0.0.1:8000/route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination, preferences: prefs })
    });
    const data = await res.json();
    if (!data.path || data.path.length === 0) {
      resDiv.innerHTML = '<b>No se encontró ruta</b>';
      drawNodes();
      return;
    }
    const html = [
      `<b>Ruta:</b> ${data.path.join(' → ')}`,
      `<b>Peso total (costo):</b> ${data.weight}`,
      `<b>Reglas aplicadas:</b> ${data.applied_rules.join(', ') || 'ninguna'}`
    ].join('<br>');
    resDiv.innerHTML = html;

    // 🔹 Dibujar ruta resaltada
    drawNodes(data.path);
  } catch (err) {
    resDiv.innerHTML = 'Error: ' + err.message;
  }
};
