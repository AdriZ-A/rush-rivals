# rush-rivals
Jeu de course multijoueur compétitif

<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RUSH RIVALS</title>
<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #10152b;
  color: white;
  font-family: Arial, sans-serif;
  text-align: center;
}
h1 { color: #39e6d0; font-size: 38px; margin: 22px 0 5px; }
p { color: #c6cee8; }
.info {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
  margin: 15px;
  font-weight: bold;
}
canvas {
  display: block;
  width: min(95vw, 850px);
  height: auto;
  margin: auto;
  border: 3px solid #39e6d0;
  border-radius: 12px;
}
button {
  background: #39e6d0;
  color: #10152b;
  border: 0;
  border-radius: 9px;
  padding: 13px 25px;
  font-weight: bold;
  cursor: pointer;
  margin: 15px 5px;
}
.controls { color: #c6cee8; font-size: 14px; padding: 0 12px 20px; }
</style>
</head>
<body>

<h1>RUSH RIVALS</h1>
<p>La compétition commence maintenant !</p>

<div class="info">
  <span>TOURS : <span id="laps">0 / 3</span></span>
  <span>TEMPS : <span id="timer">00:00</span></span>
  <span>VITESSE : <span id="speed">0</span></span>
</div>

<canvas id="game" width="850" height="600"></canvas>

<button id="start">DÉMARRER LA COURSE</button>
<button id="restart">RECOMMENCER</button>

<p class="controls">
  Flèches du clavier ou ZQSD pour conduire.
  <br>Haut : accélérer · Bas : freiner · Gauche/Droite : tourner
</p>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const lapsText = document.getElementById("laps");
const timerText = document.getElementById("timer");
const speedText = document.getElementById("speed");

const cx = 425, cy = 300;
let running = false;
let finished = false;
let elapsed = 0;
let lastTime = 0;
let lastAngle = -Math.PI / 2;
let progress = 0;
let laps = 0;

const car = {
  x: 425,
  y: 80,
  angle: 0,
  speed: 0
};

const keys = {};

const rivals = [
  { angle: 0, speed: 0.65, color: "#ff5470" },
  { angle: Math.PI / 2, speed: 0.58, color: "#ffc857" },
  { angle: Math.PI, speed: 0.72, color: "#a78bfa" }
];

document.addEventListener("keydown", e => {
  keys[e.key.toLowerCase()] = true;
  if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key)) {
    e.preventDefault();
  }
});

document.addEventListener("keyup", e => {
  keys[e.key.toLowerCase()] = false;
});

function onTrack(x, y) {
  const dx = x - cx;
  const dy = y - cy;

  const outer = (dx * dx) / (410 * 410) + (dy * dy) / (330 * 330);
  const inner = (dx * dx) / (190 * 190) + (dy * dy) / (110 * 110);

  return outer <= 1 && inner >= 1;
}

function drawCar(x, y, angle, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);

  ctx.fillStyle = "#111";
  ctx.fillRect(-13, -12, 9, 6);
  ctx.fillRect(5, -12, 9, 6);
  ctx.fillRect(-13, 6, 9, 6);
  ctx.fillRect(5, 6, 9, 6);

  ctx.fillStyle = color;
  ctx.fillRect(-15, -9, 30, 18);

  ctx.fillStyle = "#d9f6ff";
  ctx.fillRect(1, -6, 8, 12);

  ctx.fillStyle = "#fff";
  ctx.fillRect(11, -6, 3, 4);
  ctx.fillRect(11, 2, 3, 4);

  ctx.restore();
}

function drawTrack() {
  ctx.fillStyle = "#246b45";
  ctx.fillRect(0, 0, 850, 600);

  ctx.fillStyle = "#2d8755";
  for (let i = 0; i < 35; i++) {
    const x = (i * 137) % 850;
    const y = (i * 83) % 600;
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.beginPath();
  ctx.ellipse(cx, cy, 300, 220, 0, 0, Math.PI * 2);
  ctx.strokeStyle = "#172033";
  ctx.lineWidth = 226;
  ctx.stroke();

  ctx.beginPath();
  ctx.ellipse(cx, cy, 300, 220, 0, 0, Math.PI * 2);
  ctx.strokeStyle = "#687486";
  ctx.lineWidth = 210;
  ctx.stroke();

  ctx.beginPath();
  ctx.ellipse(cx, cy, 190, 110, 0, 0, Math.PI * 2);
  ctx.fillStyle = "#246b45";
  ctx.fill();

  ctx.fillStyle = "white";
  ctx.font = "bold 18px Arial";
  ctx.textAlign = "center";
  ctx.fillText("RUSH RIVALS", cx, cy + 5);

  // Ligne de départ
  for (let i = 0; i < 12; i++) {
    ctx.fillStyle = i % 2 === 0 ? "white" : "#111";
    ctx.fillRect(418, -25 + i * 18, 14, 18);
    ctx.fillStyle = i % 2 === 0 ? "#111" : "white";
    ctx.fillRect(432, -25 + i * 18, 14, 18);
  }
}

function update(dt) {
  if (!running || finished) return;

  elapsed += dt;

  if (keys["arrowup"] || keys["z"] || keys["w"]) {
    car.speed += 210 * dt;
  }

  if (keys["arrowdown"] || keys["s"]) {
    car.speed -= 260 * dt;
  }

  car.speed *= Math.pow(0.985, dt * 60);
  car.speed = Math.max(-100, Math.min(260, car.speed));

  const steering = (keys["arrowright"] || keys["d"] ? 1 : 0)
                 - (keys["arrowleft"] || keys["q"] || keys["a"] ? 1 : 0);

  car.angle += steering * 2.5 * dt * Math.min(1, Math.abs(car.speed) / 80)
               * (car.speed < 0 ? -1 : 1);

  car.x += Math.cos(car.angle) * car.speed * dt;
  car.y += Math.sin(car.angle) * car.speed * dt;

  if (!onTrack(car.x, car.y)) {
    car.speed *= 0.94;
  }

  car.x = Math.max(10, Math.min(840, car.x));
  car.y = Math.max(10, Math.min(590, car.y));

  // Progression du tour autour du circuit
  const angle = Math.atan2((car.y - cy) / 220, (car.x - cx) / 300);
  let delta = angle - lastAngle;

  while (delta > Math.PI) delta -= Math.PI * 2;
  while (delta < -Math.PI) delta += Math.PI * 2;

  if (delta > 0) progress += delta;
  lastAngle = angle;

  if (progress >= Math.PI * 2) {
    progress -= Math.PI * 2;
    laps++;
    lapsText.textContent = laps + " / 3";

    if (laps >= 3) {
      finished = true;
      running = false;
    }
  }

  rivals.forEach(r => {
    r.angle += r.speed * dt;
  });

  speedText.textContent = Math.round(Math.abs(car.speed));
  timerText.textContent = formatTime(elapsed);
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
}

function draw() {
  drawTrack();

  rivals.forEach(r => {
    const x = cx + Math.cos(r.angle) * 300;
    const y = cy + Math.sin(r.angle) * 220;
    const direction = Math.atan2(
      Math.cos(r.angle) * 220,
      -Math.sin(r.angle) * 300
    );
    drawCar(x, y, direction, r.color);
  });

  drawCar(car.x, car.y, car.angle, "#39e6d0");

  if (!running) {
    ctx.fillStyle = "rgba(10,15,35,0.72)";
    ctx.fillRect(180, 245, 490, 100);
    ctx.fillStyle = "white";
    ctx.font = "bold 27px Arial";
    ctx.textAlign = "center";

    if (finished) {
      ctx.fillText("COURSE TERMINÉE !", cx, 285);
      ctx.font = "18px Arial";
      ctx.fillText("Temps : " + formatTime(elapsed), cx, 318);
    } else {
      ctx.fillText("PRÊT À COURIR ?", cx, 305);
    }
  }
}

function loop(timestamp) {
  const dt = Math.min((timestamp - lastTime) / 1000 || 0, 0.04);
  lastTime = timestamp;

  update(dt);
  draw();

  requestAnimationFrame(loop);
}

function reset() {
  running = false;
  finished = false;
  elapsed = 0;
  laps = 0;
  progress = 0;
  lastAngle = -Math.PI / 2;

  car.x = 425;
  car.y = 80;
  car.angle = 0;
  car.speed = 0;

  rivals[0].angle = 0;
  rivals[1].angle = Math.PI / 2;
  rivals[2].angle = Math.PI;

  lapsText.textContent = "0 / 3";
  timerText.textContent = "00:00";
  speedText.textContent = "0";
  draw();
}

document.getElementById("start").addEventListener("click", () => {
  if (finished) reset();
  running = true;
});

document.getElementById("restart").addEventListener("click", reset);

reset();
requestAnimationFrame(loop);
</script>

</body>
</html>

