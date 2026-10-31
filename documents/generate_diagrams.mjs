import PImage from 'pureimage';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = __dirname;
const font = PImage.registerFont('C:/Windows/Fonts/arial.ttf', 'Arial');
const fontBold = PImage.registerFont('C:/Windows/Fonts/arialbd.ttf', 'ArialBold');
font.loadSync();
fontBold.loadSync();

function drawRoundRect(ctx, x, y, w, h, r, fillColor, strokeColor, strokeWidth = 2) {
  ctx.fillStyle = fillColor;
  ctx.fillRect(x, y, w, h);
  if (strokeColor) {
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = strokeWidth;
    ctx.strokeRect(x, y, w, h);
  }
}

function drawArrow(ctx, x1, y1, x2, y2, color = '#334155') {
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();

  // Arrowhead
  const headlen = 8;
  const angle = Math.atan2(y2 - y1, x2 - x1);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - headlen * Math.cos(angle - Math.PI / 6), y2 - headlen * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(x2 - headlen * Math.cos(angle + Math.PI / 6), y2 - headlen * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. Architecture Diagram
// ─────────────────────────────────────────────────────────────────────────────
async function makeArchitectureDiagram() {
  const W = 950, H = 580;
  const img = PImage.make(W, H);
  const ctx = img.getContext('2d');

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H);

  // Outer border
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1;
  ctx.strokeRect(5, 5, W - 10, H - 10);

  // Title
  ctx.fillStyle = '#0f172a';
  ctx.font = '20pt ArialBold';
  ctx.fillText('Figure: 3-Tier Layered Architecture of AI-Based Expense Tracker', 140, 40);

  const layers = [
    {
      name: 'Presentation Layer (Frontend UI)',
      color: '#eff6ff',
      border: '#3b82f6',
      y: 70,
      h: 90,
      boxes: [
        { title: 'Responsive Web UI', desc: 'HTML5 / CSS3 Dark Mode / Jinja2', x: 40, w: 260 },
        { title: 'AI Quick-Add Command Bar', desc: 'Real-time NLP Preview & Async Submit', x: 340, w: 270 },
        { title: 'Interactive Visualizations', desc: 'Chart.js Donut, Bar & Line Charts', x: 640, w: 270 }
      ]
    },
    {
      name: 'Application Layer (Flask Controller & Routing)',
      color: '#f0fdf4',
      border: '#22c55e',
      y: 195,
      h: 90,
      boxes: [
        { title: 'Auth Blueprint', desc: '/auth: Login, Register, Session', x: 40, w: 200 },
        { title: 'Expenses Blueprint', desc: '/expenses: CRUD, Filter, CSV', x: 265, w: 215 },
        { title: 'Budgets Blueprint', desc: '/budgets: Limits & Alert Engine', x: 505, w: 205 },
        { title: 'Dashboard Blueprint', desc: '/dashboard: KPIs & Insights', x: 735, w: 180 }
      ]
    },
    {
      name: 'Business Logic & Artificial Intelligence Layer',
      color: '#faf5ff',
      border: '#a855f7',
      y: 320,
      h: 110,
      boxes: [
        { title: 'Dual AI NLP Engine', desc: 'Gemini Cloud API + Offline ML Fallback', x: 40, w: 270 },
        { title: 'Deterministic Insights', desc: 'Month-over-Month Delta & Savings Tips', x: 335, w: 280 },
        { title: 'Budget Alert Engine', desc: '80% Warning & 100% Exceeded Badges', x: 640, w: 270 }
      ]
    },
    {
      name: 'Data Storage Layer (Persistence)',
      color: '#fffbeb',
      border: '#f59e0b',
      y: 460,
      h: 90,
      boxes: [
        { title: 'SQLite 3 Database (expenses.db)', desc: 'users, categories, expenses, budgets', x: 60, w: 380 },
        { title: 'Trained Machine Learning Model', desc: 'model.joblib (TF-IDF + Logistic Regression)', x: 480, w: 410 }
      ]
    }
  ];

  layers.forEach((layer, i) => {
    // Layer container
    drawRoundRect(ctx, 20, layer.y, W - 40, layer.h, 4, layer.color, layer.border, 2);
    ctx.fillStyle = '#1e293b';
    ctx.font = '12pt ArialBold';
    ctx.fillText(layer.name, 35, layer.y + 22);

    // Inner boxes
    layer.boxes.forEach(b => {
      drawRoundRect(ctx, b.x, layer.y + 30, b.w, layer.h - 40, 3, '#ffffff', '#94a3b8', 1);
      ctx.fillStyle = '#0f172a';
      ctx.font = '11pt ArialBold';
      ctx.fillText(b.title, b.x + 10, layer.y + 50);
      ctx.fillStyle = '#475569';
      ctx.font = '10pt Arial';
      ctx.fillText(b.desc, b.x + 10, layer.y + 68);
    });

    // Connecting arrows
    if (i < layers.length - 1) {
      drawArrow(ctx, W / 2 - 100, layer.y + layer.h, W / 2 - 100, layer.y + layer.h + 25, '#64748b');
      drawArrow(ctx, W / 2 + 100, layer.y + layer.h, W / 2 + 100, layer.y + layer.h + 25, '#64748b');
    }
  });

  await PImage.encodePNGToStream(img, fs.createWriteStream(path.join(DOCS_DIR, 'fig1_architecture.png')));
  console.log('✅ Figure 1 (Architecture) created');
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Level-0 DFD Diagram
// ─────────────────────────────────────────────────────────────────────────────
async function makeDFDDiagram() {
  const W = 950, H = 550;
  const img = PImage.make(W, H);
  const ctx = img.getContext('2d');

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H);

  // Outer border
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1;
  ctx.strokeRect(5, 5, W - 10, H - 10);

  // Title
  ctx.fillStyle = '#0f172a';
  ctx.font = '20pt ArialBold';
  ctx.fillText('Figure: Level-0 Data Flow Diagram (DFD) of Expense Tracker', 140, 40);

  // External Entity: User
  drawRoundRect(ctx, 30, 220, 140, 100, 4, '#e2e8f0', '#475569', 2);
  ctx.fillStyle = '#0f172a';
  ctx.font = '13pt ArialBold';
  ctx.fillText('User / Client', 50, 260);
  ctx.font = '10pt Arial';
  ctx.fillText('(Web Browser)', 50, 280);

  // Processes (P1 to P5)
  const processes = [
    { id: '1.0', name: 'Authentication & Session', y: 80 },
    { id: '2.0', name: 'AI & Manual Expense Logging', y: 175 },
    { id: '3.0', name: 'Budget Alert Monitoring', y: 270 },
    { id: '4.0', name: 'Dashboard Analytics Aggregation', y: 365 },
    { id: '5.0', name: 'Spending Insights Generator', y: 460 },
  ];

  processes.forEach(p => {
    drawRoundRect(ctx, 320, p.y, 300, 65, 4, '#f8fafc', '#2563eb', 2);
    ctx.fillStyle = '#1d4ed8';
    ctx.font = '12pt ArialBold';
    ctx.fillText(`Process ${p.id}:`, 335, p.y + 26);
    ctx.fillStyle = '#0f172a';
    ctx.font = '11pt Arial';
    ctx.fillText(p.name, 335, p.y + 48);

    // Arrows from User to Process
    drawArrow(ctx, 170, 270, 320, p.y + 32, '#64748b');
  });

  // Data Stores
  const stores = [
    { id: 'D1', name: 'Users Store (PBKDF2 Hashes)', y: 80 },
    { id: 'D2 & D3', name: 'Categories & Expenses Store', y: 175 },
    { id: 'D4', name: 'Monthly Budgets Store', y: 270 },
    { id: 'D5', name: 'ML Model Weights (model.joblib)', y: 365 },
    { id: 'D6', name: 'Gemini Cloud API Gateway', y: 460 },
  ];

  stores.forEach(s => {
    drawRoundRect(ctx, 700, s.y, 220, 65, 4, '#fef3c7', '#d97706', 2);
    ctx.fillStyle = '#b45309';
    ctx.font = '11pt ArialBold';
    ctx.fillText(`[${s.id}]`, 715, s.y + 26);
    ctx.fillStyle = '#1e293b';
    ctx.font = '10pt Arial';
    ctx.fillText(s.name, 715, s.y + 48);

    // Arrows from Process to Store
    drawArrow(ctx, 620, s.y + 32, 700, s.y + 32, '#d97706');
  });

  await PImage.encodePNGToStream(img, fs.createWriteStream(path.join(DOCS_DIR, 'fig2_dfd.png')));
  console.log('✅ Figure 2 (DFD) created');
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. ER Diagram
// ─────────────────────────────────────────────────────────────────────────────
async function makeERDiagram() {
  const W = 950, H = 550;
  const img = PImage.make(W, H);
  const ctx = img.getContext('2d');

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H);

  // Outer border
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1;
  ctx.strokeRect(5, 5, W - 10, H - 10);

  // Title
  ctx.fillStyle = '#0f172a';
  ctx.font = '20pt ArialBold';
  ctx.fillText('Figure: Entity-Relationship (ER) Schema Diagram', 220, 40);

  // Tables
  const tables = [
    {
      name: 'users',
      x: 60, y: 80, w: 340, h: 170,
      fields: [
        'id : INTEGER [PRIMARY KEY, AUTOINCREMENT]',
        'name : TEXT NOT NULL',
        'email : TEXT NOT NULL UNIQUE',
        'password_hash : TEXT NOT NULL',
        'created_at : TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
      ]
    },
    {
      name: 'categories',
      x: 550, y: 80, w: 340, h: 120,
      fields: [
        'id : INTEGER [PRIMARY KEY, AUTOINCREMENT]',
        'name : TEXT NOT NULL UNIQUE',
        '  (Food, Travel, Shopping, Bills, etc.)'
      ]
    },
    {
      name: 'expenses',
      x: 60, y: 320, w: 340, h: 190,
      fields: [
        'id : INTEGER [PRIMARY KEY, AUTOINCREMENT]',
        'user_id : INTEGER NOT NULL [FOREIGN KEY -> users(id)]',
        'category_id : INTEGER NOT NULL [FOREIGN KEY -> categories(id)]',
        'amount : REAL NOT NULL CHECK(amount > 0)',
        'expense_date : DATE NOT NULL',
        'note : TEXT',
        'created_at : TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
      ]
    },
    {
      name: 'budgets',
      x: 550, y: 320, w: 340, h: 170,
      fields: [
        'id : INTEGER [PRIMARY KEY, AUTOINCREMENT]',
        'user_id : INTEGER NOT NULL [FOREIGN KEY -> users(id)]',
        'category_id : INTEGER NOT NULL [FOREIGN KEY -> categories(id)]',
        'month : TEXT NOT NULL (YYYY-MM)',
        'limit_amount : REAL NOT NULL CHECK(limit_amount > 0)',
        'UNIQUE(user_id, category_id, month)'
      ]
    }
  ];

  tables.forEach(t => {
    // Header
    drawRoundRect(ctx, t.x, t.y, t.w, 35, 4, '#1e3a8a', '#1e3a8a', 2);
    ctx.fillStyle = '#ffffff';
    ctx.font = '13pt ArialBold';
    ctx.fillText(`TABLE: ${t.name}`, t.x + 15, t.y + 24);

    // Body
    drawRoundRect(ctx, t.x, t.y + 35, t.w, t.h - 35, 4, '#f8fafc', '#cbd5e1', 1);
    ctx.fillStyle = '#1e293b';
    ctx.font = '9pt Arial';
    t.fields.forEach((f, idx) => {
      ctx.fillText(`• ${f}`, t.x + 10, t.y + 55 + idx * 18);
    });
  });

  // Relationships lines
  drawArrow(ctx, 230, 250, 230, 320, '#dc2626'); // users -> expenses (1:N)
  ctx.fillStyle = '#dc2626';
  ctx.font = '10pt ArialBold';
  ctx.fillText('1 : N (logs)', 240, 290);

  drawArrow(ctx, 400, 160, 550, 400, '#dc2626'); // users -> budgets (1:N)
  ctx.fillText('1 : N (configures)', 420, 270);

  drawArrow(ctx, 550, 140, 400, 360, '#2563eb'); // categories -> expenses (1:N)
  ctx.fillStyle = '#2563eb';
  ctx.fillText('1 : N (categorizes)', 420, 230);

  drawArrow(ctx, 720, 200, 720, 320, '#2563eb'); // categories -> budgets (1:N)
  ctx.fillText('1 : N (assigned)', 730, 260);

  await PImage.encodePNGToStream(img, fs.createWriteStream(path.join(DOCS_DIR, 'fig3_er_diagram.png')));
  console.log('✅ Figure 3 (ER Diagram) created');
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. ML Pipeline Diagram
// ─────────────────────────────────────────────────────────────────────────────
async function makeMLPipelineDiagram() {
  const W = 950, H = 500;
  const img = PImage.make(W, H);
  const ctx = img.getContext('2d');

  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, W, H);

  // Outer border
  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 1;
  ctx.strokeRect(5, 5, W - 10, H - 10);

  // Title
  ctx.fillStyle = '#0f172a';
  ctx.font = '20pt ArialBold';
  ctx.fillText('Figure: Dual AI Natural Language Categorisation Pipeline', 160, 40);

  // Step 1: Input
  drawRoundRect(ctx, 30, 100, 240, 80, 4, '#eff6ff', '#3b82f6', 2);
  ctx.fillStyle = '#1e3a8a';
  ctx.font = '12pt ArialBold';
  ctx.fillText('1. Natural Language Input', 45, 125);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('e.g. "Swiggy 250", "petrol 500 rs",', 45, 145);
  ctx.fillText('"bus ticket 30", "paid 1200 bill"', 45, 165);

  drawArrow(ctx, 270, 140, 330, 140, '#3b82f6');

  // Step 2: Regex
  drawRoundRect(ctx, 330, 100, 260, 80, 4, '#f0fdf4', '#22c55e', 2);
  ctx.fillStyle = '#14532d';
  ctx.font = '12pt ArialBold';
  ctx.fillText('2. Multi-Pattern Regex', 345, 125);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('Extracts numeric amount: 250.0', 345, 145);
  ctx.fillText('Cleanses text: "Swiggy"', 345, 165);

  drawArrow(ctx, 590, 140, 650, 140, '#22c55e');

  // Step 3: Dual AI Router
  drawRoundRect(ctx, 650, 80, 260, 120, 4, '#faf5ff', '#a855f7', 2);
  ctx.fillStyle = '#581c87';
  ctx.font = '12pt ArialBold';
  ctx.fillText('3. Dual AI Classification', 665, 105);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('• Primary: Google Gemini Cloud API', 665, 130);
  ctx.fillText('• Check: Quota or Network error?', 665, 150);
  ctx.fillText('• Fallback: Offline Scikit-Learn ML', 665, 170);

  // Branch arrows
  drawArrow(ctx, 780, 200, 780, 260, '#a855f7');

  // Step 4: Offline ML Engine Box
  drawRoundRect(ctx, 520, 260, 390, 110, 4, '#fff7ed', '#ea580c', 2);
  ctx.fillStyle = '#7c2d12';
  ctx.font = '12pt ArialBold';
  ctx.fillText('4. Offline ML: TF-IDF + Logistic Regression', 535, 285);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('• Vectorizer: TF-IDF (1,2 n-grams, sublinear_tf)', 535, 308);
  ctx.fillText('• Classifier: Logistic Regression (C=3.0, lbfgs)', 535, 328);
  ctx.fillText('• Inference Latency: 0.54 ms | Accuracy: 100%', 535, 348);

  drawArrow(ctx, 520, 315, 380, 315, '#ea580c');

  // Step 5: Confidence Gate
  drawRoundRect(ctx, 160, 260, 220, 110, 4, '#fef2f2', '#ef4444', 2);
  ctx.fillStyle = '#7f1d1d';
  ctx.font = '12pt ArialBold';
  ctx.fillText('5. Confidence Gating', 175, 285);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('• Confidence >= 0.50 -> Category', 175, 310);
  ctx.fillText('• Confidence < 0.50 -> "Other"', 175, 330);
  ctx.fillText('• User can manually override', 175, 350);

  drawArrow(ctx, 270, 370, 270, 410, '#ef4444');

  // Step 6: Final DB Persistence
  drawRoundRect(ctx, 130, 410, 680, 65, 4, '#f0fdfa', '#0d9488', 2);
  ctx.fillStyle = '#134e4a';
  ctx.font = '12pt ArialBold';
  ctx.fillText('6. SQLite 3 Database Commit & Budget Recalculation', 145, 435);
  ctx.font = '10pt Arial';
  ctx.fillStyle = '#334155';
  ctx.fillText('Enforces user isolation (WHERE user_id = ?). Checks 80% warning & 100% exceeded thresholds instantly.', 145, 455);

  await PImage.encodePNGToStream(img, fs.createWriteStream(path.join(DOCS_DIR, 'fig4_ai_pipeline.png')));
  console.log('✅ Figure 4 (ML Pipeline) created');
}

async function run() {
  await makeArchitectureDiagram();
  await makeDFDDiagram();
  await makeERDiagram();
  await makeMLPipelineDiagram();
  console.log('🎉 All 4 figures generated successfully!');
}

run();
