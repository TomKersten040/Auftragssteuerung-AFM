"""
Motor Auftragssteuerung – Flask Web App
=======================================
Verwaltet Motor-/Statorzustände und koordiniert Abholaufträge.

Starten:        python app.py  →  http://localhost:5000
Abhängigkeiten: pip install flask
Datenbank:      SQLite, wird beim ersten Start automatisch erstellt (stator_status.db)

Haupttabellen:
  motor_entries   – ein Datensatz pro erfasstem Motor
  request_persons – Personen, die als Profil oder Abholverantwortliche wählbar sind
  person_groups   – optionale Gruppen zur Strukturierung der Personenliste

Wichtige Konstanten (oben in dieser Datei):
  MOTOR_TYPES       – gültige Motortypen (Dropdown + Validierung)
  STORAGE_LOCATIONS – gültige Lagerorte   (Dropdown + Validierung)
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from html import escape

from flask import Flask, flash, g, jsonify, redirect, render_template_string, request, send_file, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "stator_status.db"
SECRET_KEY = "stator-status-demo-secret-key-change-me"

# Motortypen und Lagerorte werden app-weit für Dropdowns und Validierung genutzt.
# Neue Einträge hier ergänzen – keine weiteren Anpassungen nötig.
MOTOR_TYPES = [
    "Ros",
    "Ran High RH",
    "Ran High RL",
    "Ran Mid RH",
    "Ran Mid RL",
]

STORAGE_LOCATIONS = ["Sperrfläche", "AirGap", "EoL", "Demontage"]
DEFAULT_REQUEST_PERSONS = [
    ("QS Team", ""),
    ("Logistik", ""),
]

FRONTEND_DIR = BASE_DIR / "frontend" / "dist"

app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR / "assets"),
    static_url_path="/assets",
)
app.config["SECRET_KEY"] = SECRET_KEY

# ---------------------------------------------------------------------------
# HTML-Template (Jinja2)
# ---------------------------------------------------------------------------
# Das gesamte Frontend ist in diesem einzigen String definiert.
# Variablen, die render_page() übergibt: current_view, current_profile,
# request_persons, groups, grouped_persons, motor_types, storage_locations,
# default_date, default_time, stats, status_by_location, entries.
# ---------------------------------------------------------------------------

TEMPLATE = r"""
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Motor Auftragssteuerung</title>
  <style>
    :root {
      --bg: #f1f5f9;
      --bg-strong: #e2e8f0;
      --card: rgba(255,255,255,0.94);
      --card-soft: rgba(255,255,255,0.78);
      --text: #0f172a;
      --muted: #64748b;
      --border: #dbe2ea;
      --line: #e5e7eb;
      --accent: #2563eb;
      --accent-strong: #1d4ed8;
      --ok: #16a34a;
      --warn: #f59e0b;
      --danger: #dc2626;
      --shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
      --radius: 22px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Inter, Arial, Helvetica, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(37,99,235,0.18), transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    }

    a { color: inherit; text-decoration: none; }

    .wrap {
      width: min(1380px, calc(100% - 28px));
      margin: 0 auto;
    }

    .topbar {
      background: linear-gradient(120deg, #0f172a, #1e293b);
      color: white;
      box-shadow: 0 10px 30px rgba(15,23,42,0.18);
    }

    .topbar-inner {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 18px;
      padding: 22px 0;
      flex-wrap: wrap;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.6rem, 3vw, 2.3rem);
      letter-spacing: -0.03em;
    }

    .subtitle {
      margin-top: 6px;
      color: rgba(255,255,255,0.78);
      font-size: 0.98rem;
      max-width: 760px;
    }

    .profile-box {
      min-width: min(100%, 420px);
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 20px;
      padding: 14px;
      backdrop-filter: blur(10px);
    }

    .profile-box small { color: rgba(255,255,255,0.7); }

    .inline-form {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 10px;
    }

    .nav {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 14px 0 22px;
    }

    .nav a {
      padding: 11px 15px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.1);
      color: rgba(255,255,255,0.9);
      font-weight: 600;
    }

    .nav a.active {
      background: white;
      color: var(--text);
      border-color: white;
    }

    .content {
      padding: 24px 0 36px;
      display: grid;
      gap: 22px;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 22px;
    }

    .cards-4 {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
    }

    .cards-2 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 14px;
    }

    .panel {
      background: var(--card);
      border-radius: var(--radius);
      border: 1px solid rgba(255,255,255,0.72);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(10px);
    }

    .panel.soft {
      background: var(--card-soft);
    }

    .panel-head {
      padding: 18px 22px 0;
    }

    .panel-body {
      padding: 22px;
    }

    .panel h2, .panel h3 {
      margin: 0;
      font-size: 1.12rem;
      letter-spacing: -0.02em;
    }

    .panel p.note {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .stat {
      background: white;
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 16px;
      box-shadow: 0 10px 25px rgba(15,23,42,0.04);
    }

    .stat .label {
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 8px;
    }

    .stat .value {
      font-size: 1.9rem;
      font-weight: 750;
      letter-spacing: -0.04em;
    }

    .stat.ok .value { color: var(--ok); }
    .stat.warn .value { color: var(--warn); }
    .stat.danger .value { color: var(--danger); }

    form { display: grid; gap: 16px; }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }

    .full { grid-column: 1 / -1; }

    label {
      display: block;
      font-size: 0.92rem;
      font-weight: 650;
      margin-bottom: 8px;
    }

    input, select, textarea, button {
      font: inherit;
    }

    input[type="text"],
    input[type="date"],
    input[type="time"],
    input[type="email"],
    select,
    textarea {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 13px 14px;
      background: white;
      outline: none;
      transition: 0.18s ease;
    }

    input[type="text"]:focus,
    input[type="date"]:focus,
    input[type="time"]:focus,
    input[type="email"]:focus,
    select:focus,
    textarea:focus {
      border-color: #93c5fd;
      box-shadow: 0 0 0 4px rgba(37,99,235,0.12);
    }

    textarea {
      min-height: 106px;
      resize: vertical;
    }

    .segmented {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    .segmented label {
      margin: 0;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: white;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-weight: 500;
    }

    .inline-check {
      display: flex;
      align-items: center;
      gap: 10px;
      border: 1px solid var(--border);
      background: white;
      border-radius: 14px;
      padding: 13px 14px;
      min-height: 50px;
    }

    .inline-check input {
      width: 18px;
      height: 18px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border: none;
      border-radius: 14px;
      padding: 12px 16px;
      cursor: pointer;
      transition: 0.2s ease;
      font-weight: 650;
      min-height: 44px;
    }

    .btn:hover { transform: translateY(-1px); }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      color: white;
      box-shadow: 0 10px 20px rgba(37,99,235,0.18);
    }

    .btn-secondary {
      background: white;
      color: var(--text);
      border: 1px solid var(--border);
    }

    .btn-danger {
      background: rgba(220,38,38,0.12);
      color: #991b1b;
      border: 1px solid rgba(220,38,38,0.2);
    }

    .btn-success {
      background: rgba(22,163,74,0.12);
      color: #166534;
      border: 1px solid rgba(22,163,74,0.2);
    }

    .btn-warning {
      background: rgba(245,158,11,0.12);
      color: #92400e;
      border: 1px solid rgba(245,158,11,0.22);
    }

    .btn-icon {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      padding: 0;
      font-size: 1rem;
    }

    .list {
      display: grid;
      gap: 12px;
    }

    .list-item {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: white;
      padding: 14px 16px;
    }

    .list-item small {
      color: var(--muted);
      display: block;
      margin-top: 4px;
    }

    .flash-list {
      display: grid;
      gap: 10px;
      margin-bottom: 18px;
    }

    .flash {
      padding: 12px 14px;
      border-radius: 14px;
      font-size: 0.95rem;
    }

    .flash-success {
      background: rgba(22,163,74,0.12);
      color: #166534;
      border: 1px solid rgba(22,163,74,0.22);
    }

    .flash-error {
      background: rgba(220,38,38,0.12);
      color: #991b1b;
      border: 1px solid rgba(220,38,38,0.22);
    }

    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: white;
    }

    table {
      border-collapse: collapse;
      width: 100%;
      min-width: 1180px;
    }

    th, td {
      border-bottom: 1px solid var(--line);
      padding: 13px 12px;
      text-align: left;
      vertical-align: top;
      font-size: 0.94rem;
    }

    th {
      background: #f8fafc;
      color: var(--muted);
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 700;
      white-space: nowrap;
    }

    .badge-ok { background: rgba(22,163,74,0.12); color: var(--ok); }
    .badge-nok { background: rgba(220,38,38,0.12); color: var(--danger); }
    .badge-open { background: rgba(148,163,184,0.18); color: #334155; }
    .badge-requested { background: rgba(37,99,235,0.12); color: var(--accent); }
    .badge-progress { background: rgba(245,158,11,0.14); color: #92400e; }
    .badge-done { background: rgba(22,163,74,0.12); color: #166534; }

    .muted { color: var(--muted); }
    .small { font-size: 0.9rem; }
    .empty {
      padding: 26px;
      text-align: center;
      color: var(--muted);
      background: white;
      border-radius: 18px;
      border: 1px solid var(--border);
    }

    details.editor {
      margin-top: 8px;
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 16px;
      overflow: hidden;
    }

    details.editor summary {
      list-style: none;
      cursor: pointer;
      padding: 12px 14px;
      font-weight: 650;
      color: var(--accent);
      display: flex;
      align-items: center;
      gap: 8px;
      user-select: none;
    }

    details.editor summary::-webkit-details-marker { display: none; }

    .editor-body {
      padding: 0 14px 14px;
      border-top: 1px solid var(--border);
    }

    .location-list {
      display: grid;
      gap: 10px;
      margin-top: 6px;
    }

    .location-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      background: white;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 14px 16px;
    }

    .danger-box {
      border: 1px solid rgba(220,38,38,0.2);
      background: rgba(254,242,242,0.9);
      border-radius: 18px;
      padding: 18px;
    }

    .hint {
      margin-top: 8px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .settings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 18px;
    }

    @media (max-width: 1100px) {
      .grid, .cards-4, .cards-2 { grid-template-columns: 1fr; }
    }

    @media (max-width: 760px) {
      .wrap { width: min(100% - 18px, 1280px); }
      .topbar-inner { padding: 18px 0; }
      .panel-body, .panel-head { padding-left: 16px; padding-right: 16px; }
      .form-grid { grid-template-columns: 1fr; }
    }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <header class="topbar">
    <div class="wrap">
      <div class="topbar-inner">
        <div>
          <h1>Motor Auftragssteuerung</h1>
          <div class="subtitle">
          </div>
        </div>

        <div class="profile-box">
          <div><strong>Aktuelles Benutzerprofil:</strong> {{ current_profile or 'Nicht gesetzt' }}</div>
          <small>Jeder Browser / Rechner kann ein eigenes Profil wählen. Dadurch funktionieren „Meine offenen Abholungen" pro Benutzer.</small>
          <form method="post" action="{{ url_for('set_profile') }}">
            <input type="hidden" name="next" value="{{ request.path }}">
            <div class="inline-form">
              <select name="profile_name" required>
                <option value="">Profil auswählen</option>
                {% if current_profile and current_profile not in person_names %}
                  <option value="{{ current_profile }}" selected>{{ current_profile }}</option>
                {% endif %}
                {% for person in request_persons %}
                  <option value="{{ person.name }}" {% if current_profile == person.name %}selected{% endif %}>{{ person.name }}</option>
                {% endfor %}
              </select>
              <button class="btn btn-primary" type="submit">Profil setzen</button>
            </div>
          </form>
        </div>
      </div>

      <nav class="nav">
        <a href="{{ url_for('dashboard') }}" class="{% if current_view == 'dashboard' %}active{% endif %}">Dashboard</a>
        <a href="{{ url_for('my_pickups') }}" class="{% if current_view == 'mine' %}active{% endif %}">Meine offenen Abholungen</a>
        <a href="{{ url_for('requested_pickups') }}" class="{% if current_view == 'requested' %}active{% endif %}">Alle angeforderten Abholungen</a>
        <a href="{{ url_for('completed_pickups') }}" class="{% if current_view == 'completed' %}active{% endif %}">Bereits abgeholte Motoren</a>
        <a href="{{ url_for('settings') }}" class="{% if current_view == 'settings' %}active{% endif %}">Menü / Einstellungen</a>
      </nav>
    </div>
  </header>

  <main class="wrap content">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="flash-list">
          {% for category, message in messages %}
            <div class="flash flash-{{ category }}">{{ message }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    {% if current_view == 'dashboard' %}
      <section class="grid">
        <section class="panel">
          <div class="panel-head">
            <h2>Neue Statusmeldung</h2>
            <p class="note">Motor erfassen und direkt in den gemeinsamen Auftragsfluss überführen.</p>
          </div>
          <div class="panel-body">
            <form method="post" action="{{ url_for('save_entry') }}">
              <div class="form-grid">

                <div class="full">
                  <label>Motoren <span style="color:var(--muted);font-weight:400;font-size:0.88rem;">– mehrere möglich</span></label>
                  <div id="motor-rows" style="display:grid;gap:8px;">
                    <div class="motor-row" style="display:grid;grid-template-columns:1fr 2fr 100px 40px;gap:8px;align-items:end;">
                      <div>
                        <div style="font-size:0.85rem;font-weight:600;margin-bottom:6px;">Motor</div>
                        <select name="motor_type">
                          {% for motor in motor_types %}
                            <option value="{{ motor }}">{{ motor }}</option>
                          {% endfor %}
                        </select>
                      </div>
                      <div>
                        <div style="font-size:0.85rem;font-weight:600;margin-bottom:6px;">Statornummer</div>
                        <input type="text" name="stator_number" placeholder="z. B. 178034055042516700016040" required>
                      </div>
                      <div>
                        <div style="font-size:0.85rem;font-weight:600;margin-bottom:6px;">Status</div>
                        <select name="status">
                          <option value="iO">iO</option>
                          <option value="niO">niO</option>
                          <option value="wiO">wiO</option>
                        </select>
                      </div>
                      <div>
                        <button type="button" class="btn btn-danger btn-icon remove-row-btn" onclick="removeMotorRow(this)" title="Zeile entfernen" disabled style="width:40px;height:50px;border-radius:10px;">✕</button>
                      </div>
                    </div>
                  </div>
                  <button type="button" onclick="addMotorRow()" class="btn btn-secondary"
                          style="margin-top:8px;width:100%;border-style:dashed;">+ Motor hinzufügen</button>
                </div>

                <div>
                  <label for="entry_date">Datum</label>
                  <input id="entry_date" name="entry_date" type="date" value="{{ default_date }}" required>
                </div>

                <div>
                  <label for="entry_time">Uhrzeit</label>
                  <input id="entry_time" name="entry_time" type="time" value="{{ default_time }}" required>
                </div>

                <div>
                  <label for="storage_location">Lagerort</label>
                  <select id="storage_location" name="storage_location" required>
                    {% for location in storage_locations %}
                      <option value="{{ location }}">{{ location }}</option>
                    {% endfor %}
                  </select>
                </div>

                <div>
                  <label>Aktueller Verantwortlicher</label>
                  <input type="text" value="{{ current_profile or 'Bitte Profil setzen' }}" disabled>
                </div>

                <div class="full">
                  <label for="pickup_assigned_to">Abholung zuweisen an</label>
                  <select id="pickup_assigned_to" name="pickup_assigned_to">
                    <option value="">Nicht zugewiesen</option>
                    {% if groups %}
                      {% for group in groups %}
                        <option value="__group__:{{ group.name }}">Gruppe: {{ group.name }}</option>
                      {% endfor %}
                      <option disabled>──────────────</option>
                    {% endif %}
                    {% for group_name, group_persons in grouped_persons %}
                      {% if group_name %}
                        <optgroup label="{{ group_name }}">
                          {% for person in group_persons %}
                            <option value="{{ person.name }}">{{ person.name }}</option>
                          {% endfor %}
                        </optgroup>
                      {% else %}
                        {% for person in group_persons %}
                          <option value="{{ person.name }}">{{ person.name }}</option>
                        {% endfor %}
                      {% endif %}
                    {% endfor %}
                  </select>
                </div>

                <div class="full">
                  <label for="remarks">Weitere Anmerkungen</label>
                  <textarea id="remarks" name="remarks" placeholder="Optional: Hinweise, Auffälligkeiten, nächste Schritte ..."></textarea>
                </div>

                <div class="full">
                  <label for="pickup_request_comment">Kommentar zur Abholung</label>
                  <textarea id="pickup_request_comment" name="pickup_request_comment" placeholder="Optional: Info für die abholende Person ..."></textarea>
                </div>
              </div>

              <div class="actions">
                <a class="btn btn-secondary" href="{{ url_for('export_csv') }}">CSV-Export</a>
                <button class="btn btn-primary" type="submit">Eintrag speichern</button>
              </div>
            </form>
            <script>
            (function() {
              function updateRemoveButtons() {
                var rows = document.querySelectorAll('#motor-rows .motor-row');
                rows.forEach(function(r) {
                  r.querySelector('.remove-row-btn').disabled = rows.length <= 1;
                });
              }
              window.addMotorRow = function() {
                var container = document.getElementById('motor-rows');
                var first = container.querySelector('.motor-row');
                var clone = first.cloneNode(true);
                clone.querySelectorAll('input[type="text"]').forEach(function(el) { el.value = ''; el.removeAttribute('required'); });
                clone.querySelectorAll('select').forEach(function(el) { el.selectedIndex = 0; });
                container.appendChild(clone);
                updateRemoveButtons();
                clone.querySelector('input[type="text"]').focus();
              };
              window.removeMotorRow = function(btn) {
                var rows = document.querySelectorAll('#motor-rows .motor-row');
                if (rows.length <= 1) return;
                btn.closest('.motor-row').remove();
                updateRemoveButtons();
              };
            })();
            </script>
          </div>
        </section>

        <aside class="panel soft">
          <div class="panel-head">
            <h2>Übersicht</h2>
          </div>
          <div class="panel-body">
            <div class="cards-4">
              <div class="stat">
                <div class="label">Gesamt</div>
                <div class="value">{{ stats.total }}</div>
              </div>
              <div class="stat ok">
                <div class="label">iO</div>
                <div class="value">{{ stats.io }}</div>
              </div>
              <div class="stat danger">
                <div class="label">niO</div>
                <div class="value">{{ stats.open_nio }}</div>
              </div>
              <div class="stat ok">
                <div class="label">wiO</div>
                <div class="value">{{ stats.open_wio }}</div>
              </div>
              <div class="stat warn">
                <div class="label">Meine offenen</div>
                <div class="value">{{ stats.my_open }}</div>
              </div>
            </div>

            <div style="margin-top: 20px;">
              <h3>Statusübersicht pro Lagerort</h3>

              <div class="table-wrap" style="margin-top: 14px;">
                <table style="min-width: 0;">
                  <thead>
                    <tr>
                      <th>Lagerort</th>
                      <th>iO</th>
                      <th>niO</th>
                      <th>wiO</th>
                      <th>Gesamt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for item in status_by_location %}
                      <tr>
                        <td><strong>{{ item.storage_location }}</strong></td>
                        <td>{{ item.io_count }}</td>
                        <td>{{ item.nio_count }}</td>
                        <td>{{ item.wio_count }}</td>
                        <td></strong>{{ item.total }}</strong></td>
                      </tr>
                    {% else %}
                      <tr>
                        <td colspan="5" class="muted">Keine Daten vorhanden.</td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>

              <div style="margin-top: 18px; background: white; border: 1px solid var(--border); border-radius: 18px; padding: 14px;">
                <canvas id="statusByLocationChart" height="220"></canvas>
              </div>
            </div>
          </div>
        </aside>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Aktuelle Vorgänge</h2>
          <p class="note">Bearbeiten, Abholung zuweisen, Bearbeitung übernehmen, per Mail informieren oder direkt als abgeholt markieren.</p>
        </div>
        <div class="panel-body">
          {{ entries_table(entries, current_profile, current_view) | safe }}
        </div>
      </section>
    {% elif current_view == 'mine' %}
      <section class="panel">
        <div class="panel-head">
          <h2>Meine offenen Abholungen</h2>
          <p class="note">Einträge, die dem aktuell gesetzten Profil zugewiesen sind und noch nicht abgeholt wurden.</p>
        </div>
        <div class="panel-body">
          {% if not current_profile %}
            <div class="empty">Bitte zuerst oben ein Benutzerprofil auswählen.</div>
          {% else %}
            {{ entries_table(entries, current_profile, current_view) | safe }}
          {% endif %}
        </div>
      </section>
    {% elif current_view == 'requested' %}
      <section class="panel">
        <div class="panel-head">
          <h2>Alle angeforderten Abholungen</h2>
          <p class="note">Zentrale Auftragsliste mit automatischem Status: Offen, Angefordert, In Bearbeitung, Abgeholt.</p>
        </div>
        <div class="panel-body">
          {{ entries_table(entries, current_profile, current_view) | safe }}
        </div>
      </section>
    {% elif current_view == 'completed' %}
      <section class="panel">
        <div class="panel-head">
          <h2>Bereits abgeholte Motoren</h2>
          <p class="note">Abgeschlossene Vorgänge mit dokumentierter Abholung.</p>
        </div>
        <div class="panel-body">
          {{ entries_table(entries, current_profile, current_view) | safe }}
        </div>
      </section>
    {% elif current_view == 'settings' %}
      <section class="panel">
        <div class="panel-head">
          <h2>Menü / Einstellungen</h2>
          <p class="note">Gruppen und Personen verwalten sowie Datenbankinhalte leeren.</p>
        </div>
        <div class="panel-body">
          <div class="settings-grid">

            {# ---- Gruppen verwalten ---- #}
            <section class="panel soft">
              <div class="panel-head">
                <h3>Gruppen verwalten</h3>
                <p class="note">Personen einer Gruppe zuweisen – direkt hier im Gruppenbereich.</p>
              </div>
              <div class="panel-body">
                <form method="post" action="{{ url_for('add_group') }}">
                  <div style="display:flex;gap:10px;align-items:flex-end;">
                    <div style="flex:1;">
                      <label for="group_name">Neue Gruppe</label>
                      <input id="group_name" name="group_name" type="text" placeholder="z. B. EoL, EMO, Messraum" required>
                    </div>
                    <button class="btn btn-primary" type="submit" style="white-space:nowrap;">Gruppe anlegen</button>
                  </div>
                </form>
                <div class="list" style="margin-top: 18px;">
                  {% for group in groups %}
                    {% set members = persons_by_group.get(group.id, []) %}
                    {% set unassigned = persons_by_group.get(none, []) %}
                    <div style="border:1px solid var(--border);border-radius:16px;background:white;padding:14px 16px;">
                      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                        <strong style="font-size:1rem;">{{ group.name }}</strong>
                        <form method="post" action="{{ url_for('delete_group', group_id=group.id) }}"
                              onsubmit="return confirm('Gruppe löschen? Personen werden keiner Gruppe zugewiesen.');">
                          <button class="btn btn-secondary btn-icon" type="submit" title="Gruppe löschen">🗑️</button>
                        </form>
                      </div>
                      {% if members %}
                        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">
                          {% for member in members %}
                            <form method="post" action="{{ url_for('update_person_group', person_id=member.id) }}" style="display:inline;">
                              <input type="hidden" name="group_id" value="">
                              <button type="submit" class="badge badge-requested"
                                      style="cursor:pointer;border:1px solid rgba(37,99,235,0.2);background:rgba(37,99,235,0.1);color:var(--accent);padding:6px 10px;border-radius:999px;font:inherit;font-size:0.84rem;font-weight:600;"
                                      title="Aus Gruppe entfernen">
                                {{ member.name }} &times;
                              </button>
                            </form>
                          {% endfor %}
                        </div>
                      {% else %}
                        <div style="color:var(--muted);font-size:0.88rem;margin-top:8px;">Noch keine Mitglieder</div>
                      {% endif %}
                      {% if unassigned %}
                        <form method="post" action="{{ url_for('add_person_to_group', group_id=group.id) }}"
                              style="display:flex;gap:8px;align-items:center;margin-top:12px;">
                          <select name="person_id"
                                  style="flex:1;padding:7px 10px;border-radius:10px;border:1px solid var(--border);font:inherit;font-size:0.9rem;background:white;">
                            <option value="">Person hinzufügen ...</option>
                            {% for person in unassigned %}
                              <option value="{{ person.id }}">{{ person.name }}</option>
                            {% endfor %}
                          </select>
                          <button class="btn btn-primary" type="submit"
                                  style="padding:7px 14px;font-size:0.9rem;min-height:auto;white-space:nowrap;">+ Hinzufügen</button>
                        </form>
                      {% endif %}
                    </div>
                  {% else %}
                    <div class="empty">Noch keine Gruppen angelegt.</div>
                  {% endfor %}
                </div>
              </div>
            </section>

            {# ---- Personen verwalten ---- #}
            <section class="panel soft">
              <div class="panel-head">
                <h3>Personen verwalten</h3>
                <p class="note">Diese Personen erscheinen als Profile und in Abholzuweisungen. Gruppe wird über den Gruppenbereich links vergeben.</p>
              </div>
              <div class="panel-body">
                <form method="post" action="{{ url_for('add_person') }}">
                  <div class="form-grid">
                    <div>
                      <label for="person_name">Name</label>
                      <input id="person_name" name="person_name" type="text" placeholder="z. B. Tom" required>
                    </div>
                    <div>
                      <label for="person_email">E-Mail (optional)</label>
                      <input id="person_email" name="person_email" type="email" placeholder="name@firma.de">
                    </div>
                  </div>
                  <div class="actions">
                    <button class="btn btn-primary" type="submit">Person anlegen</button>
                  </div>
                </form>

                <div class="list" style="margin-top: 18px;">
                  {% for person in request_persons %}
                    <div class="list-item">
                      <div style="flex:1;min-width:120px;">
                        <strong>{{ person.name }}</strong>
                        <small>
                          {{ person.email or 'Keine E-Mail' }}
                          {% if person.group_name %}&nbsp;· Gruppe: {{ person.group_name }}{% endif %}
                        </small>
                      </div>
                      <form method="post" action="{{ url_for('delete_person', person_id=person.id) }}"
                            onsubmit="return confirm('Person wirklich löschen?');">
                        <button class="btn btn-secondary btn-icon" type="submit" title="Person löschen">🗑️</button>
                      </form>
                    </div>
                  {% else %}
                    <div class="empty">Noch keine Personen angelegt.</div>
                  {% endfor %}
                </div>
              </div>
            </section>

            {# ---- Datenbank verwalten ---- #}
            <section class="panel soft">
              <div class="panel-head">
                <h3>Datenbank verwalten</h3>
                <p class="note">Leert alle Motor- und Abholdaten. Personen/Profile bleiben erhalten.</p>
              </div>
              <div class="panel-body">
                <div class="danger-box">
                  <form method="post" action="{{ url_for('reset_database') }}" onsubmit="return confirm('Alle Motor- und Abholdaten wirklich löschen?');">
                    <label class="inline-check">
                      <input type="checkbox" name="confirm_reset" value="yes" required>
                      <span>Ich bestätige das Zurücksetzen der Datenbankinhalte.</span>
                    </label>
                    <div class="actions" style="margin-top: 14px; justify-content: flex-start;">
                      <button class="btn btn-danger" type="submit">Datenbank leeren</button>
                    </div>
                  </form>
                  <div class="hint">Die Tabellenstruktur bleibt bestehen. Die App ist danach sofort wieder einsatzbereit.</div>
                </div>
              </div>
            </section>

          </div>
        </div>
      </section>
    {% endif %}
  </main>
  {% if current_view == 'dashboard' %}
  <script>
    const statusByLocationData = {{ status_by_location | tojson }};
    const chartCanvas = document.getElementById('statusByLocationChart');

    if (chartCanvas && statusByLocationData.length) {
      const labels = statusByLocationData.map(item => item.storage_location);
      const ioData = statusByLocationData.map(item => item.io_count);
      const nioData = statusByLocationData.map(item => item.nio_count);
      const wioData = statusByLocationData.map(item => item.wio_count);

      new Chart(chartCanvas, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'iO',
              data: ioData,
              backgroundColor: 'rgba(22, 163, 74, 0.75)',
              borderColor: 'rgba(22, 163, 74, 1)',
              borderWidth: 1,
              borderRadius: 8
            },
            {
              label: 'niO',
              data: nioData,
              backgroundColor: 'rgba(220, 38, 38, 0.75)',
              borderColor: 'rgba(220, 38, 38, 1)',
              borderWidth: 1,
              borderRadius: 8
            },
            {
              label: 'wiO',
              data: wioData,
              backgroundColor: 'rgba(37, 99, 235, 0.75)',
              borderColor: 'rgba(37, 99, 235, 1)',
              borderWidth: 1,
              borderRadius: 8
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top'
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0,
                stepSize: 1
              }
            }
          }
        }
      });
    }
  </script>
  {% endif %}
</body>
</html>

"""


# ---------------------------------------------------------------------------
# Datenbankzugriff
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Gibt die DB-Verbindung für den aktuellen Request-Kontext zurück (lazy init)."""
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    if not table_exists(conn, table_name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    """Fügt eine Spalte hinzu, falls sie noch nicht existiert (idempotent, sicher für Migrationen)."""
    columns = get_columns(conn, table_name)
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def seed_default_persons(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM request_persons").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO request_persons (name, email, created_at) VALUES (?, ?, ?)",
            [(name, email, datetime.now().isoformat(timespec="seconds")) for name, email in DEFAULT_REQUEST_PERSONS],
        )


def migrate_old_entries(conn: sqlite3.Connection) -> None:
    """Migriert Altdaten aus der früheren Tabelle stator_entries in motor_entries (einmalig)."""
    if not table_exists(conn, "stator_entries"):
        return
    existing = conn.execute("SELECT COUNT(*) FROM motor_entries").fetchone()[0]
    if existing:
        return

    old_columns = get_columns(conn, "stator_entries")
    required = {"stator_type", "sachnummer", "status", "entry_date", "entry_time", "storage_location", "operator_name"}
    if not required.issubset(old_columns):
        return

    rows = conn.execute(
        "SELECT * FROM stator_entries ORDER BY id"
    ).fetchall()
    for row in rows:
        conn.execute(
            """
            INSERT INTO motor_entries (
                motor_type, stator_number, status, entry_date, entry_time,
                storage_location, remarks, responsible_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["stator_type"],
                row["sachnummer"],
                row["status"],
                row["entry_date"],
                row["entry_time"],
                row["storage_location"],
                row["remarks"] if "remarks" in old_columns else "",
                row["operator_name"],
                row["created_at"] if "created_at" in old_columns else datetime.now().isoformat(timespec="seconds"),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        if row["operator_name"]:
            conn.execute(
                "INSERT OR IGNORE INTO request_persons (name, email, created_at) VALUES (?, '', ?)",
                (row["operator_name"], datetime.now().isoformat(timespec="seconds")),
            )


def init_db() -> None:
    """
    Erstellt alle Tabellen beim ersten Start und führt Migrationen durch.

    Tabellen:
      motor_entries   – Kerntabelle; ein Eintrag pro Motor mit Abholverlauf
      request_persons – Personen für Profil-Auswahl und Abholzuweisung
      person_groups   – optionale Gruppen zur Strukturierung der Personenliste
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS motor_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motor_type TEXT NOT NULL,
            stator_number TEXT NOT NULL,
            status TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_time TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            remarks TEXT,
            responsible_name TEXT NOT NULL,
            pickup_assigned_to TEXT,
            pickup_assigned_email TEXT,
            pickup_requested_by TEXT,
            pickup_requested_date TEXT,
            pickup_requested_time TEXT,
            pickup_request_comment TEXT,
            pickup_started_by TEXT,
            pickup_started_date TEXT,
            pickup_started_time TEXT,
            picked_up INTEGER NOT NULL DEFAULT 0,
            pickup_done_by TEXT,
            pickup_done_date TEXT,
            pickup_done_time TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS request_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            email TEXT,
            group_id INTEGER REFERENCES person_groups(id),
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS person_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )

    for column_name, definition in {
        "pickup_assigned_to": "TEXT",
        "pickup_assigned_email": "TEXT",
        "pickup_assigned_group": "TEXT",
        "pickup_requested_by": "TEXT",
        "pickup_requested_date": "TEXT",
        "pickup_requested_time": "TEXT",
        "pickup_request_comment": "TEXT",
        "pickup_started_by": "TEXT",
        "pickup_started_date": "TEXT",
        "pickup_started_time": "TEXT",
        "picked_up": "INTEGER NOT NULL DEFAULT 0",
        "pickup_done_by": "TEXT",
        "pickup_done_date": "TEXT",
        "pickup_done_time": "TEXT",
        "updated_at": "TEXT",
    }.items():
        ensure_column(conn, "motor_entries", column_name, definition)

    # group_id-Spalte nachrüsten falls DB aus älterer Version stammt
    ensure_column(conn, "request_persons", "group_id", "INTEGER REFERENCES person_groups(id)")

    migrate_old_entries(conn)
    seed_default_persons(conn)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Template-Global: HTML-Tabelle für Einträge
# ---------------------------------------------------------------------------

@app.template_global()
def entries_table(entries: list[dict[str, Any]], current_profile: str | None, current_view: str) -> str:
    """
    Rendert die Eintrags-Tabelle als HTML-String (wird per |safe im Template ausgegeben).
    Enthält Mehrfachauswahl per Checkbox, eine Sammelaktions-Leiste sowie
    für jeden Eintrag einen aufklappbaren Editor mit Abholsteuerung.
    """
    if not entries:
        return '<div class="empty">Keine passenden Einträge vorhanden.</div>'

    persons = get_request_persons()
    groups = get_groups()
    next_val = f"/{current_view}"

    assign_opts_html = _assignment_options_html(None, None, persons, groups, placeholder="Person/Gruppe auswählen ...")

    bulk_bar = (
        '<div id="bulk-bar" style="display:none;align-items:center;gap:12px;flex-wrap:wrap;'
        'background:white;border:1px solid var(--border);border-radius:16px;'
        'padding:12px 16px;margin-bottom:12px;">'
        '<span id="bulk-count" style="font-weight:650;color:var(--accent);min-width:100px;">0 ausgewählt</span>'
        f'<form id="bulk-form" method="post" action="{url_for("bulk_action")}" style="display:contents;">'
        f'<input type="hidden" name="next" value="{next_val}">'
        '<input type="hidden" id="bulk-action-input" name="action" value="">'
        '<button type="button" class="btn btn-success" onclick="bulkSubmit(\'picked_up\')"'
        ' style="padding:8px 14px;font-size:0.9rem;min-height:auto;">&#9745; Als abgeholt markieren</button>'
        '<div style="display:flex;gap:8px;align-items:center;">'
        f'<select name="assign_to" id="bulk-assign-sel"'
        f' style="padding:7px 10px;border-radius:10px;border:1px solid var(--border);font:inherit;font-size:0.9rem;">'
        f'{assign_opts_html}</select>'
        '<button type="button" class="btn btn-primary" onclick="bulkSubmit(\'assign\')"'
        ' style="padding:8px 14px;font-size:0.9rem;min-height:auto;">Zuweisen</button>'
        '</div>'
        '</form>'
        '</div>'
    )

    rows = []
    for entry in entries:
        status_badge = {
            "iO": '<span class="badge badge-ok">iO</span>',
            "niO": '<span class="badge badge-nok">niO</span>',
            "wiO": '<span class="badge badge-ok">wiO</span>',
        }.get(entry["status"], f'<span class="badge badge-open">{entry["status"]}</span>')

        pickup_status = entry["pickup_status"]
        pickup_badge = {
            "Offen": '<span class="badge badge-open">Offen</span>',
            "Angefordert": '<span class="badge badge-requested">Angefordert</span>',
            "In Bearbeitung": '<span class="badge badge-progress">In Bearbeitung</span>',
            "Abgeholt": '<span class="badge badge-done">Abgeholt</span>',
            "Nicht erforderlich": '<span class="badge badge-ok">Nicht erforderlich</span>',
        }[pickup_status]

        action_bits = []
        if not entry["picked_up"] and current_profile and entry["pickup_assigned_to"] == current_profile and not entry["pickup_started_by"]:
            action_bits.append(
                f'''<form method="post" action="{url_for('start_pickup', entry_id=entry['id'])}" style="display:inline;">
<input type="hidden" name="next" value="{next_val}">
<button class="btn btn-warning btn-icon" title="Bearbeitung übernehmen" type="submit">▶</button>
</form>'''
            )
        if entry["pickup_assigned_email"]:
            action_bits.append(
                f'<a class="btn btn-secondary btn-icon" title="Manuelle E-Mail öffnen" href="{entry["mailto_url"]}">✉️</a>'
            )
        if entry["picked_up"]:
            action_bits.append('<span class="btn btn-secondary btn-icon" title="Bereits abgeholt">☑</span>')
        else:
            action_bits.append(
                f'''<form method="post" action="{url_for('toggle_picked_up', entry_id=entry['id'])}" style="display:inline;">
<input type="hidden" name="next" value="{next_val}">
<label class="btn btn-secondary btn-icon" title="Als abgeholt markieren" style="cursor:pointer;">☐<input type="checkbox" checked onchange="this.form.submit()" style="display:none"></label>
</form>'''
            )

        action_html = "".join(action_bits) or '<span class="muted">—</span>'
        pickup_meta = []
        if entry.get("pickup_assigned_group"):
            pickup_meta.append(f'Zugewiesen an Gruppe: <strong>{escape(entry["pickup_assigned_group"])}</strong>')
        elif entry["pickup_assigned_to"]:
            pickup_meta.append(f'Zugewiesen an: <strong>{escape(entry["pickup_assigned_to"] or "")}</strong>')
        if entry["pickup_requested_by"]:
            pickup_meta.append(f'Angefordert von: {escape(entry["pickup_requested_by"] or "")}')
        if entry["pickup_started_by"]:
            pickup_meta.append(f'In Bearbeitung durch: {escape(entry["pickup_started_by"] or "")}')
        if entry["pickup_done_by"]:
            pickup_meta.append(f'Abgeholt durch: {escape(entry["pickup_done_by"] or "")}')

        pickup_details = '<br>'.join(pickup_meta) if pickup_meta else '—'
        request_time = ' '.join(part for part in [entry["pickup_requested_date"], entry["pickup_requested_time"]] if part) or '—'
        done_time = ' '.join(part for part in [entry["pickup_done_date"], entry["pickup_done_time"]] if part) or '—'

        editor = f'''
<details class="editor">
  <summary>✏️ Bearbeiten &amp; Abholung steuern</summary>
  <div class="editor-body">
    <form method="post" action="{url_for('update_entry', entry_id=entry['id'])}">
      <input type="hidden" name="next" value="{next_val}">
      <div class="form-grid">
        <div>
          <label>Motor</label>
          <select name="motor_type" required>
            {''.join(f'<option value="{motor}" {"selected" if entry["motor_type"] == motor else ""}>{motor}</option>' for motor in MOTOR_TYPES)}
          </select>
        </div>
        <div>
          <label>Statornummer</label>
          <input type="text" name="stator_number" required value="{entry['stator_number']}">
        </div>
        <div>
          <label>Lagerort</label>
          <select name="storage_location" required>
            {''.join(f'<option value="{loc}" {"selected" if entry["storage_location"] == loc else ""}>{loc}</option>' for loc in STORAGE_LOCATIONS)}
          </select>
        </div>
        <div>
          <label>Status Motor</label>
          <select name="status" required>
            <option value="iO" {'selected' if entry['status'] == 'iO' else ''}>iO</option>
            <option value="niO" {'selected' if entry['status'] == 'niO' else ''}>niO</option>
            <option value="wiO" {'selected' if entry['status'] == 'wiO' else ''}>wiO</option>
          </select>
        </div>
        <div>
          <label>Datum</label>
          <input type="date" name="entry_date" value="{entry['entry_date']}" required>
        </div>
        <div>
          <label>Uhrzeit</label>
          <input type="time" name="entry_time" value="{entry['entry_time']}" required>
        </div>
        <div class="full">
          <label>Anmerkungen</label>
          <textarea name="remarks">{(entry['remarks'] or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</textarea>
        </div>
        <div>
          <label>Abholung zuweisen an</label>
          <select name="pickup_assigned_to">
            {_assignment_options_html(entry['pickup_assigned_to'], entry.get('pickup_assigned_group'), persons, groups)}
          </select>
        </div>
        <div class="full">
          <label>Kommentar zur Abholung</label>
          <textarea name="pickup_request_comment">{(entry['pickup_request_comment'] or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</textarea>
        </div>
        <div class="full">
          <label class="inline-check">
            <input type="checkbox" name="picked_up" value="1" {'checked' if entry['picked_up'] else ''}>
            <span>Motor wurde abgeholt (1 Klick)</span>
          </label>
        </div>
        <div>
          <label>Verantwortlicher Abholung</label>
          <input type="text" name="pickup_done_by" value="{entry['pickup_done_by'] or ''}" placeholder="Name der abholenden Person">
        </div>
        <div>
          <label>Abhol-Datum</label>
          <input type="date" name="pickup_done_date" value="{entry['pickup_done_date'] or ''}">
        </div>
        <div>
          <label>Abhol-Uhrzeit</label>
          <input type="time" name="pickup_done_time" value="{entry['pickup_done_time'] or ''}">
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-primary" type="submit">Änderungen speichern</button>
      </div>
    </form>
  </div>
</details>'''

        rows.append(f'''
<tr>
  <td style="width:40px;text-align:center;"><input type="checkbox" class="row-sel" value="{entry['id']}" style="width:18px;height:18px;cursor:pointer;"></td>
  <td>{entry['entry_date']} {entry['entry_time']}</td>
  <td>{entry['motor_type']}</td>
  <td><strong>{entry['stator_number']}</strong></td>
  <td>{status_badge}</td>
  <td>{entry['storage_location']}</td>
  <td>{entry['responsible_name']}</td>
  <td>{pickup_badge}</td>
  <td>{pickup_details}</td>
  <td>{request_time}</td>
  <td>{done_time}</td>
  <td>{action_html}</td>
</tr>
<tr>
  <td colspan="12">
    <div class="small muted" style="margin-bottom: 8px;">Anmerkungen: {escape(entry['remarks'] or '—')}<br>Abhol-Kommentar: {escape(entry['pickup_request_comment'] or '—')}</div>
    {editor}
  </td>
</tr>
''')

    js = '''<script>
(function() {
  var bar = document.getElementById('bulk-bar');
  var allCb = document.getElementById('select-all-cb');
  var countEl = document.getElementById('bulk-count');
  function getChecked() { return document.querySelectorAll('.row-sel:checked'); }
  function getAllCbs() { return document.querySelectorAll('.row-sel'); }
  function updateBar() {
    var n = getChecked().length;
    countEl.textContent = n + ' ausgewählt';
    bar.style.display = n > 0 ? 'flex' : 'none';
  }
  if (allCb) {
    allCb.addEventListener('change', function() {
      getAllCbs().forEach(function(cb) { cb.checked = allCb.checked; });
      updateBar();
    });
  }
  getAllCbs().forEach(function(cb) {
    cb.addEventListener('change', function() {
      var all = getAllCbs();
      if (allCb) allCb.checked = all.length > 0 && Array.from(all).every(function(c) { return c.checked; });
      updateBar();
    });
  });
  window.bulkSubmit = function(action) {
    var checked = getChecked();
    if (!checked.length) { return; }
    if (action === 'assign') {
      var sel = document.getElementById('bulk-assign-sel');
      if (!sel || !sel.value) { alert('Bitte eine Person auswählen.'); return; }
    }
    var form = document.getElementById('bulk-form');
    document.getElementById('bulk-action-input').value = action;
    form.querySelectorAll('input[name="entry_ids"]').forEach(function(el) { el.remove(); });
    checked.forEach(function(cb) {
      var inp = document.createElement('input');
      inp.type = 'hidden';
      inp.name = 'entry_ids';
      inp.value = cb.value;
      form.appendChild(inp);
    });
    form.submit();
  };
})();
</script>'''

    return f'''
<div>
  {bulk_bar}
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th style="width:40px;text-align:center;"><input type="checkbox" id="select-all-cb" style="width:18px;height:18px;cursor:pointer;" title="Alle auswählen"></th>
          <th>Erfasst am</th>
          <th>Motor</th>
          <th>Statornummer</th>
          <th>Status Motor</th>
          <th>Lagerort</th>
          <th>Verantwortlicher</th>
          <th>Abholstatus</th>
          <th>Abholinfos</th>
          <th>Angefordert am</th>
          <th>Abgeholt am</th>
          <th>Aktionen</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</div>
{js}
'''


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def get_request_persons() -> list[sqlite3.Row]:
    """Gibt alle Personen inkl. Gruppenname zurück, sortiert nach Gruppe → Name."""
    db = get_db()
    return db.execute(
        """
        SELECT r.id, r.name, r.email, r.group_id, g.name AS group_name
        FROM request_persons r
        LEFT JOIN person_groups g ON r.group_id = g.id
        ORDER BY g.name COLLATE NOCASE, r.name COLLATE NOCASE
        """
    ).fetchall()


def get_groups() -> list[sqlite3.Row]:
    """Gibt alle Gruppen alphabetisch sortiert zurück."""
    db = get_db()
    return db.execute(
        "SELECT id, name FROM person_groups ORDER BY name COLLATE NOCASE"
    ).fetchall()


def _group_persons(persons: list[sqlite3.Row]) -> list[tuple[str | None, list]]:
    """
    Gruppiert eine sortierte Personenliste für Dropdown-Rendering.
    None = ungrupiert → flache <option>-Elemente; String = Gruppenname → <optgroup>.
    """
    result: list[tuple[str | None, list]] = []
    current_group: str | None = "\x00"  # Sentinel
    current_list: list = []
    for person in persons:
        group: str | None = person["group_name"]
        if group != current_group:
            if current_list:
                result.append((current_group, current_list))
            current_group = group
            current_list = []
        current_list.append(person)
    if current_list:
        result.append((current_group, current_list))
    return result


def _person_options_html(selected: str | None, persons: list[sqlite3.Row]) -> str:
    """
    Erzeugt <option>/<optgroup>-HTML für einen Personen-Dropdown.
    Ungrupierte Personen erscheinen als flache <option>-Elemente ohne Wrapper.
    """
    html = ['<option value="">Nicht zugewiesen</option>']
    for group_name, group_persons in _group_persons(persons):
        if group_name:
            html.append(f'<optgroup label="{escape(group_name)}">')
        for person in group_persons:
            sel = " selected" if selected == person["name"] else ""
            html.append(f'<option value="{escape(person["name"])}"{sel}>{escape(person["name"])}</option>')
        if group_name:
            html.append("</optgroup>")
    return "".join(html)


def _assignment_options_html(
    selected_person: str | None,
    selected_group: str | None,
    persons: list[sqlite3.Row],
    groups: list[sqlite3.Row],
    placeholder: str = "Nicht zugewiesen",
) -> str:
    """Dropdown mit Gruppen oben (Wert '__group__:Name'), dann Einzelpersonen."""
    html = [f'<option value="">{escape(placeholder)}</option>']
    if groups:
        for g in groups:
            sel = " selected" if selected_group == g["name"] else ""
            html.append(f'<option value="__group__:{escape(g["name"])}"{sel}>Gruppe: {escape(g["name"])}</option>')
        html.append('<option disabled>──────────────</option>')
    for group_name, group_persons in _group_persons(persons):
        if group_name:
            html.append(f'<optgroup label="{escape(group_name)}">')
        for person in group_persons:
            sel = " selected" if selected_person == person["name"] else ""
            html.append(f'<option value="{escape(person["name"])}"{sel}>{escape(person["name"])}</option>')
        if group_name:
            html.append("</optgroup>")
    return "".join(html)


def get_person_group_name(person_name: str) -> str | None:
    """Gibt den Gruppennamen der Person zurück (oder None wenn keine Gruppe)."""
    if not person_name:
        return None
    db = get_db()
    row = db.execute(
        "SELECT g.name FROM request_persons r LEFT JOIN person_groups g ON r.group_id = g.id WHERE r.name = ?",
        (person_name,),
    ).fetchone()
    return row[0] if row else None


def get_persons_by_group() -> dict[int | None, list]:
    """Gibt Personen gruppiert nach group_id zurück (None = ohne Gruppe)."""
    persons = get_request_persons()
    result: dict[int | None, list] = {}
    for person in persons:
        gid = person["group_id"]
        result.setdefault(gid, []).append(person)
    return result


def current_profile() -> str:
    return session.get("profile_name", "").strip()


def lookup_person_email(name: str) -> str:
    if not name:
        return ""
    db = get_db()
    row = db.execute("SELECT email FROM request_persons WHERE name = ?", (name,)).fetchone()
    return (row["email"] if row and row["email"] else "").strip()


def now_parts() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M")


def derive_pickup_status(row: sqlite3.Row | dict[str, Any]) -> str:
    """
    Leitet den Abholstatus aus den DB-Feldern ab (kein eigenes Statusfeld).
    Reihenfolge: picked_up → started → assigned (Person oder Gruppe) → Offen
    """
    if int(row["picked_up"] or 0) == 1:
        return "Abgeholt"
    if row["pickup_started_by"]:
        return "In Bearbeitung"
    assigned_group = row.get("pickup_assigned_group") if isinstance(row, dict) else None
    if row["pickup_assigned_to"] or assigned_group:
        return "Angefordert"
    return "Offen"


def build_mailto_url(entry: sqlite3.Row | dict[str, Any]) -> str:
    email = (entry["pickup_assigned_email"] or "").strip()
    if not email:
        return "#"
    subject = f"Abholung angefordert – {entry['motor_type']} – {entry['stator_number']}"
    body = (
        "Für folgenden Motor wurde eine Abholung angefordert:\r\n\r\n"
        f"Motor: {entry['motor_type']}\r\n"
        f"Statornummer: {entry['stator_number']}\r\n"
        f"Lagerort: {entry['storage_location']}\r\n"
        f"Verantwortlicher: {entry['responsible_name']}\r\n"
        f"Abholung zugewiesen an: {entry['pickup_assigned_to'] or '-'}\r\n"
        f"Kommentar: {entry['pickup_request_comment'] or '-'}\r\n"
    )
    return f"mailto:{quote(email)}?subject={quote(subject)}&body={quote(body)}"


def fetch_entries_for_view(view: str, profile_name: str | None) -> list[dict[str, Any]]:
    """
    Lädt und filtert Einträge je nach aktiver View:
      dashboard  – neueste 40 Einträge
      mine       – offen + dem aktuellen Profil zugewiesen
      requested  – alle offenen mit Zuweisung
      completed  – bereits abgeholt
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT *
        FROM motor_entries
        ORDER BY entry_date DESC, entry_time DESC, id DESC
        """
    ).fetchall()

    prepared: list[dict[str, Any]] = []
    for row in rows:
        entry = dict(row)
        entry["pickup_status"] = derive_pickup_status(entry)
        entry["mailto_url"] = build_mailto_url(entry)
        prepared.append(entry)

    if view == "dashboard":
        return prepared[:40]
    if view == "mine":
        if not profile_name:
            return []
        person_group = get_person_group_name(profile_name)
        return [
            e for e in prepared
            if int(e["picked_up"] or 0) == 0
            and (
                e["pickup_assigned_to"] == profile_name
                or (person_group and e.get("pickup_assigned_group") == person_group)
            )
        ]
    if view == "requested":
        return [e for e in prepared if int(e["picked_up"] or 0) == 0 and e["pickup_assigned_to"]]
    if view == "completed":
        return [e for e in prepared if int(e["picked_up"] or 0) == 1]
    return prepared


def fetch_stats(profile_name: str) -> dict[str, int]:
    """Berechnet die Kennzahlen für die Dashboard-Übersichtskarten."""
    db = get_db()
    rows = db.execute("SELECT * FROM motor_entries").fetchall()
    total = len(rows)
    io = sum(1 for row in rows if row["status"] == "iO")
    # niO / wiO zählen nach Motor-Status, unabhängig vom Abholstatus
    open_nio = sum(1 for row in rows if row["status"] == "niO")
    open_wio = sum(1 for row in rows if row["status"] == "wiO")
    my_open = sum(
        1 for row in rows
        if int(row["picked_up"] or 0) == 0 and row["pickup_assigned_to"] == profile_name
    ) if profile_name else 0
    return {"total": total, "io": io, "open_nio": open_nio, "open_wio": open_wio, "my_open": my_open}


def fetch_status_by_location() -> list[dict[str, int | str]]:
    db = get_db()
    rows = db.execute(
        """
        SELECT
            storage_location,
            SUM(CASE WHEN LOWER(status) = 'io' THEN 1 ELSE 0 END) AS io_count,
            SUM(CASE WHEN LOWER(status) = 'nio' THEN 1 ELSE 0 END) AS nio_count,
            SUM(CASE WHEN LOWER(status) = 'wio' THEN 1 ELSE 0 END) AS wio_count,
            COUNT(*) AS total
        FROM motor_entries
        GROUP BY storage_location
        ORDER BY storage_location
        """
    ).fetchall()

    row_map = {
        (row["storage_location"] or "Unbekannt"): {
            "storage_location": row["storage_location"] or "Unbekannt",
            "io_count": int(row["io_count"] or 0),
            "nio_count": int(row["nio_count"] or 0),
            "wio_count": int(row["wio_count"] or 0),
            "total": int(row["total"] or 0),
        }
        for row in rows
    }

    result: list[dict[str, int | str]] = []
    for location in STORAGE_LOCATIONS:
        result.append(
            row_map.get(
                location,
                {
                    "storage_location": location,
                    "io_count": 0,
                    "nio_count": 0,
                    "wio_count": 0,
                    "total": 0,
                },
            )
        )

    for location, values in row_map.items():
        if location not in STORAGE_LOCATIONS:
            result.append(values)

    return result


def render_page(view: str) -> str:
    now = datetime.now()
    profile_name = current_profile()
    persons = get_request_persons()
    all_groups = get_groups()
    return render_template_string(
        TEMPLATE,
        current_view=view,
        current_profile=profile_name,
        request_persons=persons,
        person_names=[p["name"] for p in persons],
        groups=all_groups,
        grouped_persons=_group_persons(persons),
        persons_by_group=get_persons_by_group(),
        motor_types=MOTOR_TYPES,
        storage_locations=STORAGE_LOCATIONS,
        default_date=now.strftime("%Y-%m-%d"),
        default_time=now.strftime("%H:%M"),
        stats=fetch_stats(profile_name),
        status_by_location=fetch_status_by_location(),
        entries=fetch_entries_for_view(view, profile_name),
        request=request,
    )


def valid_next(default_endpoint: str = "dashboard") -> str:
    nxt = request.form.get("next", "").strip()
    allowed = {"/dashboard", "/mine", "/requested", "/completed", "/settings", "/"}
    if nxt in allowed:
        return nxt
    return url_for(default_endpoint)


# ---------------------------------------------------------------------------
# Routen – Seiten
# ---------------------------------------------------------------------------

@app.route("/")
def root() -> Any:
    """Liefert das React-Frontend (index.html) für alle Seiten-Routen."""
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        return "Frontend nicht gebaut. Bitte 'npm run build' in frontend/ ausführen.", 404
    return send_file(index_file)


# ---------------------------------------------------------------------------
# Routen – Profil
# ---------------------------------------------------------------------------

@app.route("/set-profile", methods=["POST"])
def set_profile() -> Any:
    profile_name = request.form.get("profile_name", "").strip()
    if not profile_name:
        flash("Bitte ein Benutzerprofil auswählen.", "error")
    else:
        session["profile_name"] = profile_name
        flash(f"Benutzerprofil auf '{profile_name}' gesetzt.", "success")
    return redirect(valid_next())


# ---------------------------------------------------------------------------
# Routen – Motor-Einträge
# ---------------------------------------------------------------------------

@app.route("/save", methods=["POST"])
def save_entry() -> Any:
    responsible_name = current_profile()
    if not responsible_name:
        flash("Bitte zuerst oben ein Benutzerprofil setzen.", "error")
        return redirect(url_for("dashboard"))

    entry_date = request.form.get("entry_date", "").strip()
    entry_time = request.form.get("entry_time", "").strip()
    storage_location = request.form.get("storage_location", "").strip()
    remarks = request.form.get("remarks", "").strip()
    pickup_request_comment = request.form.get("pickup_request_comment", "").strip()

    raw_assigned = request.form.get("pickup_assigned_to", "").strip()
    if raw_assigned.startswith("__group__:"):
        pickup_assigned_group = raw_assigned[len("__group__:"):]
        pickup_assigned_to = ""
        pickup_assigned_email = ""
    else:
        pickup_assigned_to = raw_assigned
        pickup_assigned_group = ""
        pickup_assigned_email = lookup_person_email(pickup_assigned_to) if pickup_assigned_to else ""

    has_assignment = bool(pickup_assigned_to or pickup_assigned_group)

    if storage_location not in STORAGE_LOCATIONS:
        flash("Ungültiger Lagerort.", "error")
        return redirect(url_for("dashboard"))
    if not entry_date or not entry_time:
        flash("Bitte alle Pflichtfelder ausfüllen.", "error")
        return redirect(url_for("dashboard"))

    motor_types_list = request.form.getlist("motor_type")
    stator_numbers_list = request.form.getlist("stator_number")
    statuses_list = request.form.getlist("status")

    rows_to_insert = []
    for motor_type, stator_number, status in zip(motor_types_list, stator_numbers_list, statuses_list):
        motor_type = motor_type.strip()
        stator_number = stator_number.strip()
        status = status.strip()
        if not stator_number:
            continue
        if motor_type not in MOTOR_TYPES:
            flash(f"Ungültiger Motor: {motor_type}", "error")
            return redirect(url_for("dashboard"))
        if status not in {"iO", "niO", "wiO"}:
            flash(f"Ungültiger Status: {status}", "error")
            return redirect(url_for("dashboard"))
        rows_to_insert.append((motor_type, stator_number, status))

    if not rows_to_insert:
        flash("Bitte mindestens eine Statornummer eingeben.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    now = datetime.now().isoformat(timespec="seconds")
    for motor_type, stator_number, status in rows_to_insert:
        db.execute(
            """
            INSERT INTO motor_entries (
                motor_type, stator_number, status, entry_date, entry_time,
                storage_location, remarks, responsible_name,
                pickup_assigned_to, pickup_assigned_email, pickup_assigned_group,
                pickup_requested_by, pickup_requested_date, pickup_requested_time,
                pickup_request_comment, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                motor_type, stator_number, status, entry_date, entry_time,
                storage_location, remarks, responsible_name,
                pickup_assigned_to, pickup_assigned_email, pickup_assigned_group,
                responsible_name if has_assignment else "",
                entry_date if has_assignment else "",
                entry_time if has_assignment else "",
                pickup_request_comment, now, now,
            ),
        )
    db.commit()
    count = len(rows_to_insert)
    flash(f"{count} Eintrag/Einträge erfolgreich gespeichert.", "success")
    return redirect(url_for("dashboard"))


@app.route("/entry/<int:entry_id>/update", methods=["POST"])
def update_entry(entry_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        flash("Eintrag nicht gefunden.", "error")
        return redirect(valid_next())

    motor_type = request.form.get("motor_type", "").strip()
    stator_number = request.form.get("stator_number", "").strip()
    status = request.form.get("status", "").strip()
    entry_date = request.form.get("entry_date", "").strip()
    entry_time = request.form.get("entry_time", "").strip()
    storage_location = request.form.get("storage_location", "").strip()
    remarks = request.form.get("remarks", "").strip()
    pickup_request_comment = request.form.get("pickup_request_comment", "").strip()
    picked_up = 1 if request.form.get("picked_up") == "1" else 0
    pickup_done_by = request.form.get("pickup_done_by", "").strip()
    pickup_done_date = request.form.get("pickup_done_date", "").strip()
    pickup_done_time = request.form.get("pickup_done_time", "").strip()

    raw_assigned = request.form.get("pickup_assigned_to", "").strip()
    if raw_assigned.startswith("__group__:"):
        pickup_assigned_group = raw_assigned[len("__group__:"):]
        pickup_assigned_to = ""
        pickup_assigned_email = ""
    else:
        pickup_assigned_to = raw_assigned
        pickup_assigned_group = ""
        pickup_assigned_email = lookup_person_email(pickup_assigned_to) if pickup_assigned_to else ""

    if motor_type not in MOTOR_TYPES or status not in {"iO", "niO", "wiO"} or storage_location not in STORAGE_LOCATIONS:
        flash("Ungültige Eingabedaten erkannt.", "error")
        return redirect(valid_next())

    pickup_requested_by = row["pickup_requested_by"] or ""
    pickup_requested_date = row["pickup_requested_date"] or ""
    pickup_requested_time = row["pickup_requested_time"] or ""
    pickup_started_by = row["pickup_started_by"] or ""
    pickup_started_date = row["pickup_started_date"] or ""
    pickup_started_time = row["pickup_started_time"] or ""

    prev_assigned_to = row["pickup_assigned_to"] or ""
    prev_assigned_group = row["pickup_assigned_group"] or "" if "pickup_assigned_group" in dict(row) else ""
    has_prev = bool(prev_assigned_to or prev_assigned_group)
    has_new = bool(pickup_assigned_to or pickup_assigned_group)

    if has_new and not has_prev:
        pickup_requested_by = current_profile() or row["responsible_name"]
        pickup_requested_date, pickup_requested_time = now_parts()
    elif not has_new:
        pickup_requested_by = ""
        pickup_requested_date = ""
        pickup_requested_time = ""
        pickup_started_by = ""
        pickup_started_date = ""
        pickup_started_time = ""
        picked_up = 0
        if not pickup_done_by:
            pickup_done_date = ""
            pickup_done_time = ""
    elif pickup_assigned_to != prev_assigned_to or pickup_assigned_group != prev_assigned_group:
        pickup_requested_by = current_profile() or row["responsible_name"]
        pickup_requested_date, pickup_requested_time = now_parts()
        pickup_started_by = ""
        pickup_started_date = ""
        pickup_started_time = ""
        if not picked_up:
            pickup_done_by = ""
            pickup_done_date = ""
            pickup_done_time = ""

    if picked_up and not pickup_done_date:
        pickup_done_date, pickup_done_time = now_parts()
        if not pickup_done_by:
            pickup_done_by = current_profile() or pickup_started_by or pickup_assigned_to or row["responsible_name"]
    elif not picked_up:
        pickup_done_by = ""
        pickup_done_date = ""
        pickup_done_time = ""

    db.execute(
        """
        UPDATE motor_entries
        SET motor_type = ?,
            stator_number = ?,
            status = ?,
            entry_date = ?,
            entry_time = ?,
            storage_location = ?,
            remarks = ?,
            pickup_assigned_to = ?,
            pickup_assigned_email = ?,
            pickup_assigned_group = ?,
            pickup_requested_by = ?,
            pickup_requested_date = ?,
            pickup_requested_time = ?,
            pickup_request_comment = ?,
            pickup_started_by = ?,
            pickup_started_date = ?,
            pickup_started_time = ?,
            picked_up = ?,
            pickup_done_by = ?,
            pickup_done_date = ?,
            pickup_done_time = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            motor_type,
            stator_number,
            status,
            entry_date,
            entry_time,
            storage_location,
            remarks,
            pickup_assigned_to,
            pickup_assigned_email,
            pickup_assigned_group,
            pickup_requested_by,
            pickup_requested_date,
            pickup_requested_time,
            pickup_request_comment,
            pickup_started_by,
            pickup_started_date,
            pickup_started_time,
            picked_up,
            pickup_done_by,
            pickup_done_date,
            pickup_done_time,
            datetime.now().isoformat(timespec="seconds"),
            entry_id,
        ),
    )
    db.commit()
    flash("Eintrag erfolgreich aktualisiert.", "success")
    return redirect(valid_next())


@app.route("/entry/<int:entry_id>/start", methods=["POST"])
def start_pickup(entry_id: int) -> Any:
    profile_name = current_profile()
    if not profile_name:
        flash("Bitte zuerst ein Benutzerprofil setzen.", "error")
        return redirect(valid_next())

    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        flash("Eintrag nicht gefunden.", "error")
        return redirect(valid_next())
    if row["pickup_assigned_to"] != profile_name:
        flash("Die Abholung ist nicht deinem Profil zugewiesen.", "error")
        return redirect(valid_next())

    start_date, start_time = now_parts()
    db.execute(
        """
        UPDATE motor_entries
        SET pickup_started_by = ?, pickup_started_date = ?, pickup_started_time = ?, updated_at = ?
        WHERE id = ?
        """,
        (profile_name, start_date, start_time, datetime.now().isoformat(timespec="seconds"), entry_id),
    )
    db.commit()
    flash("Abholung auf 'In Bearbeitung' gesetzt.", "success")
    return redirect(valid_next())


@app.route("/entry/<int:entry_id>/toggle-picked-up", methods=["POST"])
def toggle_picked_up(entry_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        flash("Eintrag nicht gefunden.", "error")
        return redirect(valid_next())

    if int(row["picked_up"] or 0) == 1:
        flash("Motor wurde bereits als abgeholt markiert.", "success")
        return redirect(valid_next())

    done_date, done_time = now_parts()
    done_by = current_profile() or row["pickup_started_by"] or row["pickup_assigned_to"] or row["responsible_name"]
    db.execute(
        """
        UPDATE motor_entries
        SET picked_up = 1,
            pickup_done_by = ?,
            pickup_done_date = ?,
            pickup_done_time = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (done_by, done_date, done_time, datetime.now().isoformat(timespec="seconds"), entry_id),
    )
    db.commit()
    flash("Motor als abgeholt markiert.", "success")
    return redirect(valid_next())


# ---------------------------------------------------------------------------
# Routen – Sammelaktionen
# ---------------------------------------------------------------------------

@app.route("/entries/bulk", methods=["POST"])
def bulk_action() -> Any:
    """Führt eine Sammelaktion (abgeholt markieren oder zuweisen) auf mehreren Einträgen durch."""
    action = request.form.get("action", "").strip()
    ids_raw = request.form.getlist("entry_ids")
    entry_ids = [int(i) for i in ids_raw if i.isdigit()]

    if not entry_ids:
        flash("Keine Einträge ausgewählt.", "error")
        return redirect(valid_next())

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")
    done_date, done_time = now_parts()
    profile_name = current_profile()

    if action == "picked_up":
        count = 0
        for eid in entry_ids:
            row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (eid,)).fetchone()
            if not row or int(row["picked_up"] or 0) == 1:
                continue
            done_by = profile_name or row["pickup_started_by"] or row["pickup_assigned_to"] or row["responsible_name"]
            db.execute(
                """UPDATE motor_entries
                   SET picked_up = 1, pickup_done_by = ?, pickup_done_date = ?,
                       pickup_done_time = ?, updated_at = ?
                   WHERE id = ?""",
                (done_by, done_date, done_time, now_str, eid),
            )
            count += 1
        db.commit()
        flash(f"{count} Motor(en) als abgeholt markiert.", "success")

    elif action == "assign":
        raw_assign = request.form.get("assign_to", "").strip()
        if not raw_assign:
            flash("Bitte eine Person oder Gruppe für die Zuweisung auswählen.", "error")
            return redirect(valid_next())
        if raw_assign.startswith("__group__:"):
            assign_group = raw_assign[len("__group__:"):]
            assign_to = ""
            assign_email = ""
            label = f"Gruppe '{escape(assign_group)}'"
        else:
            assign_to = raw_assign
            assign_group = ""
            assign_email = lookup_person_email(assign_to)
            label = f"'{escape(assign_to)}'"
        req_date, req_time = now_parts()
        for eid in entry_ids:
            row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (eid,)).fetchone()
            if not row:
                continue
            db.execute(
                """UPDATE motor_entries
                   SET pickup_assigned_to = ?, pickup_assigned_email = ?, pickup_assigned_group = ?,
                       pickup_requested_by = ?, pickup_requested_date = ?, pickup_requested_time = ?,
                       pickup_started_by = '', pickup_started_date = '', pickup_started_time = '',
                       updated_at = ?
                   WHERE id = ?""",
                (assign_to, assign_email, assign_group,
                 profile_name or row["responsible_name"],
                 req_date, req_time, now_str, eid),
            )
        db.commit()
        flash(f"{len(entry_ids)} Motor(en) zugewiesen an {label}.", "success")

    else:
        flash("Unbekannte Sammelaktion.", "error")

    return redirect(valid_next())


# ---------------------------------------------------------------------------
# Routen – Personen und Gruppen (Einstellungen)
# ---------------------------------------------------------------------------

@app.route("/settings/persons/add", methods=["POST"])
def add_person() -> Any:
    name = request.form.get("person_name", "").strip()
    email = request.form.get("person_email", "").strip()
    group_id_str = request.form.get("group_id", "").strip()
    group_id = int(group_id_str) if group_id_str else None

    if not name:
        flash("Bitte einen Namen eingeben.", "error")
        return redirect(url_for("settings"))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO request_persons (name, email, group_id, created_at) VALUES (?, ?, ?, ?)",
            (name, email, group_id, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        flash(f"Person '{name}' gespeichert.", "success")
    except sqlite3.IntegrityError:
        flash("Diese Person existiert bereits.", "error")
    return redirect(url_for("settings"))


@app.route("/settings/persons/<int:person_id>/delete", methods=["POST"])
def delete_person(person_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT name FROM request_persons WHERE id = ?", (person_id,)).fetchone()
    if not row:
        flash("Person nicht gefunden.", "error")
        return redirect(url_for("settings"))
    db.execute("DELETE FROM request_persons WHERE id = ?", (person_id,))
    db.commit()
    flash(f"Person '{row['name']}' gelöscht.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/persons/<int:person_id>/group", methods=["POST"])
def update_person_group(person_id: int) -> Any:
    """Weist einer Person eine (andere) Gruppe zu oder entfernt die Gruppenzuweisung."""
    group_id_str = request.form.get("group_id", "").strip()
    group_id = int(group_id_str) if group_id_str else None
    db = get_db()
    db.execute("UPDATE request_persons SET group_id = ? WHERE id = ?", (group_id, person_id))
    db.commit()
    flash("Gruppe aktualisiert.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/groups/add", methods=["POST"])
def add_group() -> Any:
    name = request.form.get("group_name", "").strip()
    if not name:
        flash("Bitte einen Gruppennamen eingeben.", "error")
        return redirect(url_for("settings"))
    db = get_db()
    try:
        db.execute(
            "INSERT INTO person_groups (name, created_at) VALUES (?, ?)",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        flash(f"Gruppe '{name}' angelegt.", "success")
    except sqlite3.IntegrityError:
        flash("Diese Gruppe existiert bereits.", "error")
    return redirect(url_for("settings"))


@app.route("/settings/groups/<int:group_id>/delete", methods=["POST"])
def delete_group(group_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT name FROM person_groups WHERE id = ?", (group_id,)).fetchone()
    if not row:
        flash("Gruppe nicht gefunden.", "error")
        return redirect(url_for("settings"))
    db.execute("UPDATE request_persons SET group_id = NULL WHERE group_id = ?", (group_id,))
    db.execute("DELETE FROM person_groups WHERE id = ?", (group_id,))
    db.commit()
    flash(f"Gruppe '{row['name']}' gelöscht. Betroffene Personen wurden keiner Gruppe zugewiesen.", "success")
    return redirect(url_for("settings"))


@app.route("/settings/groups/<int:group_id>/add-person", methods=["POST"])
def add_person_to_group(group_id: int) -> Any:
    person_id_str = request.form.get("person_id", "").strip()
    if not person_id_str or not person_id_str.isdigit():
        flash("Bitte eine Person auswählen.", "error")
        return redirect(url_for("settings"))
    db = get_db()
    db.execute("UPDATE request_persons SET group_id = ? WHERE id = ?", (group_id, int(person_id_str)))
    db.commit()
    flash("Person zur Gruppe hinzugefügt.", "success")
    return redirect(url_for("settings"))


# ---------------------------------------------------------------------------
# Routen – Datenbank & Export
# ---------------------------------------------------------------------------

@app.route("/settings/reset-db", methods=["POST"])
def reset_database() -> Any:
    if request.form.get("confirm_reset") != "yes":
        flash("Bitte das Zurücksetzen bestätigen.", "error")
        return redirect(url_for("settings"))

    db = get_db()
    db.execute("DELETE FROM motor_entries")
    db.execute("DELETE FROM sqlite_sequence WHERE name = 'motor_entries'")
    db.commit()
    flash("Motor- und Abholdaten wurden gelöscht. Personen/Profile bleiben erhalten.", "success")
    return redirect(url_for("settings"))


@app.route("/export")
def export_csv() -> Any:
    db = get_db()
    rows = db.execute(
        "SELECT * FROM motor_entries ORDER BY entry_date DESC, entry_time DESC, id DESC"
    ).fetchall()

    export_path = BASE_DIR / "motor_auftragssteuerung_export.csv"
    header = [
        "Datum",
        "Uhrzeit",
        "Motor",
        "Statornummer",
        "Status Motor",
        "Lagerort",
        "Verantwortlicher",
        "Anmerkungen",
        "Abholstatus",
        "Zugewiesen an",
        "E-Mail Abholung",
        "Angefordert von",
        "Anforderungsdatum",
        "Anforderungsuhrzeit",
        "Abhol-Kommentar",
        "In Bearbeitung durch",
        "Abgeholt",
        "Verantwortlicher Abholung",
        "Abholdatum",
        "Abholuhrzeit",
    ]

    with export_path.open("w", encoding="utf-8", newline="") as f:
        f.write(";".join(header) + "\n")
        for row in rows:
            prepared = dict(row)
            prepared["pickup_status"] = derive_pickup_status(prepared)
            values = [
                prepared["entry_date"],
                prepared["entry_time"],
                prepared["motor_type"],
                prepared["stator_number"],
                prepared["status"],
                prepared["storage_location"],
                prepared["responsible_name"],
                prepared["remarks"] or "",
                prepared["pickup_status"],
                prepared["pickup_assigned_to"] or "",
                prepared["pickup_assigned_email"] or "",
                prepared["pickup_requested_by"] or "",
                prepared["pickup_requested_date"] or "",
                prepared["pickup_requested_time"] or "",
                prepared["pickup_request_comment"] or "",
                prepared["pickup_started_by"] or "",
                "Ja" if int(prepared["picked_up"] or 0) == 1 else "Nein",
                prepared["pickup_done_by"] or "",
                prepared["pickup_done_date"] or "",
                prepared["pickup_done_time"] or "",
            ]
            sanitized = [str(value).replace(";", ",") for value in values]
            f.write(";".join(sanitized) + "\n")

    return send_file(export_path, as_attachment=True, download_name="motor_auftragssteuerung_export.csv")


# ---------------------------------------------------------------------------
# REST-API für React-Frontend
# ---------------------------------------------------------------------------

@app.route("/api/profile", methods=["GET"])
def api_get_profile() -> Any:
    persons = get_request_persons()
    return jsonify({
        "profile": current_profile(),
        "persons": [p["name"] for p in persons],
    })


@app.route("/api/profile", methods=["POST"])
def api_set_profile() -> Any:
    name = request.form.get("profile_name", "").strip()
    if name:
        session["profile_name"] = name
    return jsonify({"profile": current_profile()})


@app.route("/api/page/<view>")
def api_page_data(view: str) -> Any:
    allowed_views = {"dashboard", "mine", "requested", "completed", "settings"}
    if view not in allowed_views:
        return jsonify({"error": "Unknown view"}), 400
    profile_name = current_profile()
    persons = get_request_persons()
    all_groups = get_groups()
    now = datetime.now()
    entries = fetch_entries_for_view(view, profile_name)
    return jsonify({
        "entries": [dict(e) for e in entries],
        "stats": fetch_stats(profile_name),
        "status_by_location": fetch_status_by_location(),
        "request_persons": [dict(p) for p in persons],
        "groups": [dict(g) for g in all_groups],
        "motor_types": MOTOR_TYPES,
        "storage_locations": STORAGE_LOCATIONS,
        "current_profile": profile_name,
        "current_view": view,
        "default_date": now.strftime("%Y-%m-%d"),
        "default_time": now.strftime("%H:%M"),
    })


@app.route("/api/save", methods=["POST"])
def api_save_entry() -> Any:
    responsible_name = current_profile()
    if not responsible_name:
        return jsonify({"error": "Kein Profil gesetzt"}), 400

    entry_date = request.form.get("entry_date", "").strip()
    entry_time = request.form.get("entry_time", "").strip()
    storage_location = request.form.get("storage_location", "").strip()
    remarks = request.form.get("remarks", "").strip()
    pickup_request_comment = request.form.get("pickup_request_comment", "").strip()

    raw_assigned = request.form.get("pickup_assigned_to", "").strip()
    if raw_assigned.startswith("__group__:"):
        pickup_assigned_group = raw_assigned[len("__group__:"):]
        pickup_assigned_to = ""
        pickup_assigned_email = ""
    else:
        pickup_assigned_to = raw_assigned
        pickup_assigned_group = ""
        pickup_assigned_email = lookup_person_email(pickup_assigned_to) if pickup_assigned_to else ""

    has_assignment = bool(pickup_assigned_to or pickup_assigned_group)

    if storage_location not in STORAGE_LOCATIONS:
        return jsonify({"error": "Ungültiger Lagerort"}), 400
    if not entry_date or not entry_time:
        return jsonify({"error": "Pflichtfelder fehlen"}), 400

    motor_types_list = request.form.getlist("motor_type")
    stator_numbers_list = request.form.getlist("stator_number")
    statuses_list = request.form.getlist("status")

    rows_to_insert = []
    for motor_type, stator_number, status in zip(motor_types_list, stator_numbers_list, statuses_list):
        motor_type = motor_type.strip()
        stator_number = stator_number.strip()
        status = status.strip()
        if not stator_number:
            continue
        if motor_type not in MOTOR_TYPES or status not in {"iO", "niO", "wiO"}:
            return jsonify({"error": f"Ungültige Daten: {motor_type}/{status}"}), 400
        rows_to_insert.append((motor_type, stator_number, status))

    if not rows_to_insert:
        return jsonify({"error": "Mindestens eine Statornummer erforderlich"}), 400

    db = get_db()
    now = datetime.now().isoformat(timespec="seconds")
    for motor_type, stator_number, status in rows_to_insert:
        db.execute(
            """
            INSERT INTO motor_entries (
                motor_type, stator_number, status, entry_date, entry_time,
                storage_location, remarks, responsible_name,
                pickup_assigned_to, pickup_assigned_email, pickup_assigned_group,
                pickup_requested_by, pickup_requested_date, pickup_requested_time,
                pickup_request_comment, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                motor_type, stator_number, status, entry_date, entry_time,
                storage_location, remarks, responsible_name,
                pickup_assigned_to, pickup_assigned_email, pickup_assigned_group,
                responsible_name if has_assignment else "",
                entry_date if has_assignment else "",
                entry_time if has_assignment else "",
                pickup_request_comment, now, now,
            ),
        )
    db.commit()
    return jsonify({"saved": len(rows_to_insert)})


@app.route("/api/entry/<int:entry_id>/update", methods=["POST"])
def api_update_entry(entry_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        return jsonify({"error": "Nicht gefunden"}), 404

    motor_type = request.form.get("motor_type", "").strip()
    stator_number = request.form.get("stator_number", "").strip()
    status = request.form.get("status", "").strip()
    entry_date = request.form.get("entry_date", "").strip()
    entry_time = request.form.get("entry_time", "").strip()
    storage_location = request.form.get("storage_location", "").strip()
    remarks = request.form.get("remarks", "").strip()
    pickup_request_comment = request.form.get("pickup_request_comment", "").strip()
    picked_up = 1 if request.form.get("picked_up") in ("1", "true") else 0
    pickup_done_by = request.form.get("pickup_done_by", "").strip()
    pickup_done_date = request.form.get("pickup_done_date", "").strip()
    pickup_done_time = request.form.get("pickup_done_time", "").strip()

    raw_assigned = request.form.get("pickup_assigned_to", "").strip()
    if raw_assigned.startswith("__group__:"):
        pickup_assigned_group = raw_assigned[len("__group__:"):]
        pickup_assigned_to = ""
        pickup_assigned_email = ""
    else:
        pickup_assigned_to = raw_assigned
        pickup_assigned_group = ""
        pickup_assigned_email = lookup_person_email(pickup_assigned_to) if pickup_assigned_to else ""

    if motor_type not in MOTOR_TYPES or status not in {"iO", "niO", "wiO"} or storage_location not in STORAGE_LOCATIONS:
        return jsonify({"error": "Ungültige Eingabedaten"}), 400

    pickup_requested_by = row["pickup_requested_by"] or ""
    pickup_requested_date = row["pickup_requested_date"] or ""
    pickup_requested_time = row["pickup_requested_time"] or ""
    pickup_started_by = row["pickup_started_by"] or ""
    pickup_started_date = row["pickup_started_date"] or ""
    pickup_started_time = row["pickup_started_time"] or ""

    prev_assigned_to = row["pickup_assigned_to"] or ""
    prev_assigned_group = row["pickup_assigned_group"] or "" if "pickup_assigned_group" in dict(row) else ""
    has_prev = bool(prev_assigned_to or prev_assigned_group)
    has_new = bool(pickup_assigned_to or pickup_assigned_group)

    if has_new and not has_prev:
        pickup_requested_by = current_profile() or row["responsible_name"]
        pickup_requested_date, pickup_requested_time = now_parts()
    elif not has_new:
        pickup_requested_by = ""
        pickup_requested_date = ""
        pickup_requested_time = ""
        pickup_started_by = ""
        pickup_started_date = ""
        pickup_started_time = ""
        picked_up = 0
        if not pickup_done_by:
            pickup_done_date = ""
            pickup_done_time = ""
    elif pickup_assigned_to != prev_assigned_to or pickup_assigned_group != prev_assigned_group:
        pickup_requested_by = current_profile() or row["responsible_name"]
        pickup_requested_date, pickup_requested_time = now_parts()
        pickup_started_by = ""
        pickup_started_date = ""
        pickup_started_time = ""
        if not picked_up:
            pickup_done_by = ""
            pickup_done_date = ""
            pickup_done_time = ""

    if picked_up and not pickup_done_date:
        pickup_done_date, pickup_done_time = now_parts()
        if not pickup_done_by:
            pickup_done_by = current_profile() or pickup_started_by or pickup_assigned_to or row["responsible_name"]
    elif not picked_up:
        pickup_done_by = ""
        pickup_done_date = ""
        pickup_done_time = ""

    db.execute(
        """
        UPDATE motor_entries
        SET motor_type=?, stator_number=?, status=?, entry_date=?, entry_time=?,
            storage_location=?, remarks=?, pickup_assigned_to=?, pickup_assigned_email=?,
            pickup_assigned_group=?, pickup_requested_by=?, pickup_requested_date=?,
            pickup_requested_time=?, pickup_request_comment=?, pickup_started_by=?,
            pickup_started_date=?, pickup_started_time=?, picked_up=?, pickup_done_by=?,
            pickup_done_date=?, pickup_done_time=?, updated_at=?
        WHERE id=?
        """,
        (
            motor_type, stator_number, status, entry_date, entry_time,
            storage_location, remarks, pickup_assigned_to, pickup_assigned_email,
            pickup_assigned_group, pickup_requested_by, pickup_requested_date,
            pickup_requested_time, pickup_request_comment, pickup_started_by,
            pickup_started_date, pickup_started_time, picked_up, pickup_done_by,
            pickup_done_date, pickup_done_time,
            datetime.now().isoformat(timespec="seconds"), entry_id,
        ),
    )
    db.commit()
    return jsonify({"updated": True})


@app.route("/api/entry/<int:entry_id>/start", methods=["POST"])
def api_start_pickup(entry_id: int) -> Any:
    profile_name = current_profile()
    if not profile_name:
        return jsonify({"error": "Kein Profil gesetzt"}), 400
    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        return jsonify({"error": "Nicht gefunden"}), 404
    if row["pickup_assigned_to"] != profile_name:
        return jsonify({"error": "Nicht zugewiesen"}), 403
    start_date, start_time = now_parts()
    db.execute(
        "UPDATE motor_entries SET pickup_started_by=?, pickup_started_date=?, pickup_started_time=?, updated_at=? WHERE id=?",
        (profile_name, start_date, start_time, datetime.now().isoformat(timespec="seconds"), entry_id),
    )
    db.commit()
    return jsonify({"started": True})


@app.route("/api/entry/<int:entry_id>/toggle-picked-up", methods=["POST"])
def api_toggle_picked_up(entry_id: int) -> Any:
    db = get_db()
    row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (entry_id,)).fetchone()
    if not row:
        return jsonify({"error": "Nicht gefunden"}), 404
    if int(row["picked_up"] or 0) == 1:
        return jsonify({"already_picked_up": True})
    done_date, done_time = now_parts()
    done_by = current_profile() or row["pickup_started_by"] or row["pickup_assigned_to"] or row["responsible_name"]
    db.execute(
        "UPDATE motor_entries SET picked_up=1, pickup_done_by=?, pickup_done_date=?, pickup_done_time=?, updated_at=? WHERE id=?",
        (done_by, done_date, done_time, datetime.now().isoformat(timespec="seconds"), entry_id),
    )
    db.commit()
    return jsonify({"picked_up": True})


@app.route("/api/entries/bulk", methods=["POST"])
def api_bulk_action() -> Any:
    action = request.form.get("action", "").strip()
    ids_raw = request.form.getlist("entry_ids")
    entry_ids = [int(i) for i in ids_raw if i.isdigit()]
    if not entry_ids:
        return jsonify({"error": "Keine IDs angegeben"}), 400

    db = get_db()
    now_str = datetime.now().isoformat(timespec="seconds")
    done_date, done_time = now_parts()
    profile_name = current_profile()

    if action == "picked_up":
        count = 0
        for eid in entry_ids:
            row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (eid,)).fetchone()
            if not row or int(row["picked_up"] or 0) == 1:
                continue
            done_by = profile_name or row["pickup_started_by"] or row["pickup_assigned_to"] or row["responsible_name"]
            db.execute(
                "UPDATE motor_entries SET picked_up=1, pickup_done_by=?, pickup_done_date=?, pickup_done_time=?, updated_at=? WHERE id=?",
                (done_by, done_date, done_time, now_str, eid),
            )
            count += 1
        db.commit()
        return jsonify({"updated": count})

    elif action == "assign":
        raw_assign = request.form.get("assign_to", "").strip()
        if not raw_assign:
            return jsonify({"error": "Ziel fehlt"}), 400
        if raw_assign.startswith("__group__:"):
            assign_group = raw_assign[len("__group__:"):]
            assign_to = ""
            assign_email = ""
        else:
            assign_to = raw_assign
            assign_group = ""
            assign_email = lookup_person_email(assign_to)
        req_date, req_time = now_parts()
        for eid in entry_ids:
            row = db.execute("SELECT * FROM motor_entries WHERE id = ?", (eid,)).fetchone()
            if not row:
                continue
            db.execute(
                """UPDATE motor_entries
                   SET pickup_assigned_to=?, pickup_assigned_email=?, pickup_assigned_group=?,
                       pickup_requested_by=?, pickup_requested_date=?, pickup_requested_time=?,
                       pickup_started_by='', pickup_started_date='', pickup_started_time='', updated_at=?
                   WHERE id=?""",
                (assign_to, assign_email, assign_group,
                 profile_name or row["responsible_name"], req_date, req_time, now_str, eid),
            )
        db.commit()
        return jsonify({"assigned": len(entry_ids)})

    return jsonify({"error": "Unbekannte Aktion"}), 400


@app.route("/api/settings/persons/add", methods=["POST"])
def api_add_person() -> Any:
    name = request.form.get("person_name", "").strip()
    email = request.form.get("person_email", "").strip()
    group_id_str = request.form.get("group_id", "").strip()
    group_id = int(group_id_str) if group_id_str else None
    if not name:
        return jsonify({"error": "Name fehlt"}), 400
    db = get_db()
    try:
        db.execute(
            "INSERT INTO request_persons (name, email, group_id, created_at) VALUES (?, ?, ?, ?)",
            (name, email, group_id, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return jsonify({"added": True})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Person existiert bereits"}), 409


@app.route("/api/settings/persons/<int:person_id>/delete", methods=["POST"])
def api_delete_person(person_id: int) -> Any:
    db = get_db()
    db.execute("DELETE FROM request_persons WHERE id = ?", (person_id,))
    db.commit()
    return jsonify({"deleted": True})


@app.route("/api/settings/persons/<int:person_id>/group", methods=["POST"])
def api_update_person_group(person_id: int) -> Any:
    group_id_str = request.form.get("group_id", "").strip()
    group_id = int(group_id_str) if group_id_str else None
    db = get_db()
    db.execute("UPDATE request_persons SET group_id = ? WHERE id = ?", (group_id, person_id))
    db.commit()
    return jsonify({"updated": True})


@app.route("/api/settings/groups/add", methods=["POST"])
def api_add_group() -> Any:
    name = request.form.get("group_name", "").strip()
    if not name:
        return jsonify({"error": "Name fehlt"}), 400
    db = get_db()
    try:
        db.execute(
            "INSERT INTO person_groups (name, created_at) VALUES (?, ?)",
            (name, datetime.now().isoformat(timespec="seconds")),
        )
        db.commit()
        return jsonify({"added": True})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Gruppe existiert bereits"}), 409


@app.route("/api/settings/groups/<int:group_id>/delete", methods=["POST"])
def api_delete_group(group_id: int) -> Any:
    db = get_db()
    db.execute("UPDATE request_persons SET group_id = NULL WHERE group_id = ?", (group_id,))
    db.execute("DELETE FROM person_groups WHERE id = ?", (group_id,))
    db.commit()
    return jsonify({"deleted": True})


@app.route("/api/settings/reset-db", methods=["POST"])
def api_reset_database() -> Any:
    if request.form.get("confirm_reset") != "yes":
        return jsonify({"error": "Bestätigung fehlt"}), 400
    db = get_db()
    db.execute("DELETE FROM motor_entries")
    db.execute("DELETE FROM sqlite_sequence WHERE name = 'motor_entries'")
    db.commit()
    return jsonify({"reset": True})


@app.route("/api/export")
def api_export_csv() -> Any:
    return export_csv()




if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
