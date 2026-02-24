from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["gallery"])


@router.get("/", response_class=HTMLResponse)
def onboarding_gallery() -> str:
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Onboarding Hub</title>
  <style>
    :root {
      --bg: #f5f6f8;
      --surface: #ffffff;
      --text: #181818;
      --muted: #5f6368;
      --brand: #e62117;
      --shadow: 0 8px 25px rgba(22, 22, 22, 0.08);
      --radius: 14px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Inter, Segoe UI, Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    header {
      position: sticky;
      top: 0;
      z-index: 10;
      background: var(--surface);
      border-bottom: 1px solid #eceff1;
    }

    .topbar {
      max-width: 1240px;
      margin: 0 auto;
      padding: 14px 24px;
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .brand {
      font-weight: 700;
      font-size: 1.1rem;
      letter-spacing: 0.2px;
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 170px;
    }

    .brand span:first-child {
      background: var(--brand);
      color: #fff;
      border-radius: 7px;
      padding: 2px 8px;
      font-size: 0.95rem;
    }

    .search {
      flex: 1;
      display: flex;
      border: 1px solid #d8dce0;
      border-radius: 999px;
      overflow: hidden;
      background: #fff;
    }

    .search input {
      border: none;
      padding: 11px 14px;
      width: 100%;
      font-size: 0.95rem;
      outline: none;
    }

    .search button {
      border: none;
      padding: 0 18px;
      background: #f7f8f9;
      color: #30343a;
      cursor: pointer;
      border-left: 1px solid #e1e4e8;
    }

    .upload {
      border: none;
      background: #101318;
      color: #fff;
      border-radius: 999px;
      padding: 11px 16px;
      font-weight: 600;
      cursor: pointer;
    }

    .container {
      max-width: 1240px;
      margin: 0 auto;
      padding: 28px 24px 38px;
    }

    .hero {
      background: linear-gradient(130deg, #161f2f 0%, #243955 100%);
      color: #fff;
      border-radius: var(--radius);
      padding: 26px;
      margin-bottom: 24px;
      box-shadow: var(--shadow);
    }

    .hero h1 {
      margin: 0 0 8px;
      font-size: clamp(1.35rem, 2.4vw, 1.9rem);
    }

    .hero p {
      margin: 0;
      color: #dce7fb;
      max-width: 720px;
      line-height: 1.45;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 22px;
    }

    .card {
      background: var(--surface);
      border-radius: var(--radius);
      overflow: hidden;
      box-shadow: var(--shadow);
      transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    .card:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 28px rgba(18, 18, 18, 0.14);
    }

    .thumb {
      position: relative;
      aspect-ratio: 16 / 9;
      overflow: hidden;
      background: #d8dee6;
    }

    .thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .duration {
      position: absolute;
      right: 10px;
      bottom: 10px;
      font-size: 0.8rem;
      color: #fff;
      background: rgba(0, 0, 0, 0.72);
      border-radius: 6px;
      padding: 4px 6px;
    }

    .card-body {
      padding: 14px 14px 16px;
    }

    .title {
      margin: 0 0 6px;
      font-size: 1rem;
      line-height: 1.35;
      font-weight: 650;
    }

    .meta {
      margin: 0;
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.4;
    }
  </style>
</head>
<body>
<header>
  <div class="topbar">
    <div class="brand"><span>Play</span><span>Onboarding Hub</span></div>
    <div class="search">
      <input placeholder="Buscar tutoriales por equipo, proceso o herramienta..." />
      <button>Buscar</button>
    </div>
    <button class="upload">+ Subir tutorial</button>
  </div>
</header>

<main class="container">
  <section class="hero">
    <h1>Tutoriales internos para acelerar el onboarding</h1>
    <p>Explora videos creados por tus compañeros sobre herramientas, procesos y buenas prácticas. Comparte tu conocimiento subiendo tu propio tutorial cuando quieras.</p>
  </section>

  <section class="grid">
    <article class="card">
      <div class="thumb">
        <img src="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80" alt="Tutorial de bienvenida al stack" />
        <span class="duration">08:34</span>
      </div>
      <div class="card-body">
        <h2 class="title">Bienvenida al stack técnico de la empresa</h2>
        <p class="meta">Equipo Ingeniería · 1.2K visualizaciones · Hace 1 semana</p>
      </div>
    </article>

    <article class="card">
      <div class="thumb">
        <img src="https://images.unsplash.com/photo-1461749280684-dccba630e2f6?auto=format&fit=crop&w=1200&q=80" alt="Tutorial de flujo de tickets" />
        <span class="duration">06:12</span>
      </div>
      <div class="card-body">
        <h2 class="title">Cómo gestionamos tickets de soporte paso a paso</h2>
        <p class="meta">Customer Success · 910 visualizaciones · Hace 3 días</p>
      </div>
    </article>

    <article class="card">
      <div class="thumb">
        <img src="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80" alt="Tutorial de cultura y valores" />
        <span class="duration">10:05</span>
      </div>
      <div class="card-body">
        <h2 class="title">Cultura, valores y dinámica de trabajo entre equipos</h2>
        <p class="meta">People Ops · 2K visualizaciones · Hace 2 semanas</p>
      </div>
    </article>

    <article class="card">
      <div class="thumb">
        <img src="https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80" alt="Tutorial de dashboards internos" />
        <span class="duration">07:41</span>
      </div>
      <div class="card-body">
        <h2 class="title">Uso de dashboards internos para reportes semanales</h2>
        <p class="meta">Business Ops · 790 visualizaciones · Hace 5 días</p>
      </div>
    </article>
  </section>
</main>
</body>
</html>
    """
