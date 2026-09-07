/* Interactivity for the benchmark report: chart switching, and paging,
   filtering and CSV export of the per-file table.

   The first page of rows and every chart are rendered server-side, so the
   report still shows its data if scripts are blocked. This script only
   enhances what is already there. `__DATA__` is replaced by report.py with
   the full result set as JSON. */

const DATA = __DATA__;

const $ = (id) => document.getElementById(id);

const fmtBytes = (n) => {
  if (n == null) return '-';
  if (n >= 1048576) return (n / 1048576).toFixed(2) + ' MB';
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB';
  return n + ' B';
};

const fmtPct = (v) => (v == null ? '-' : v.toFixed(1) + '%');

const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
  }[c]));

let page = 1;
let savedPageSize = null;

/* Chart picker: every profile's chart is pre-rendered, so switching is just
   a matter of toggling which one is visible. */
function initChartPicker() {
  const picker = $('chartProfile');
  if (!picker) return;
  picker.onchange = () => {
    document.querySelectorAll('.chartbox').forEach((el) => {
      el.hidden = el.getAttribute('data-chart') !== picker.value;
    });
  };
}

function filteredRows() {
  const profile = $('fVariant') ? $('fVariant').value : '';
  const status = $('fStatus').value;
  return DATA.filter((r) => (!profile || r.profile === profile) && (!status || r.status === status));
}

function rowHtml(r, index) {
  const ok = r.status === 'success';
  const status = ok
    ? '<span class="ok">&#9679; success</span>'
    : '<span class="bad">&#9679; failed</span>';
  const detail = ok
    ? ''
    : `HTTP ${r.http_status ?? '-'} &middot; ${esc(r.error_type || '')} &middot; ` +
      `${esc(r.error_message || '')} &middot; req ${esc(r.request_id || '-')}`;
  const reduction = ok ? `<b>${fmtPct(r.reduction_pct)}</b>` : '-';
  return (
    `<tr class="${ok ? '' : 'fail'}"><td>${index}</td><td>${esc(r.file)}</td>` +
    `<td><span class="pill">${esc(r.profile)}</span></td><td>${status}</td>` +
    `<td>${fmtBytes(r.input_bytes)}</td><td>${fmtBytes(r.output_bytes)}</td>` +
    `<td>${reduction}</td><td>${r.duration_s} s</td><td>${detail}</td></tr>`
  );
}

function render() {
  const rows = filteredRows();
  const sizeValue = $('pageSize').value;
  const size = sizeValue === 'all' ? rows.length || 1 : parseInt(sizeValue, 10);
  const pages = Math.max(1, Math.ceil(rows.length / size));
  page = Math.min(page, pages);

  const start = (page - 1) * size;
  const slice = rows.slice(start, start + size);

  $('rows').innerHTML =
    slice.map((r, i) => rowHtml(r, start + i + 1)).join('') ||
    '<tr><td colspan="9" style="color:#888">No rows match.</td></tr>';

  const shown = `Showing ${start + 1}-${Math.min(start + size, rows.length)} of ${rows.length}`;
  $('range').textContent = rows.length ? shown : '0 rows';
  $('pageInfo').textContent = `Page ${page} / ${pages}`;
  $('prev').disabled = page <= 1;
  $('next').disabled = page >= pages;
}

function toCsv(rows) {
  const cols = Object.keys(rows[0]);
  const quote = (v) => {
    const s = v == null ? '' : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const body = rows.map((r) => cols.map((c) => quote(r[c])).join(','));
  return [cols.join(',')].concat(body).join('\n');
}

function initControls() {
  $('prev').onclick = () => {
    page--;
    render();
  };
  $('next').onclick = () => {
    page++;
    render();
  };
  const reset = () => {
    page = 1;
    render();
  };
  $('pageSize').onchange = reset;
  $('fStatus').onchange = reset;
  if ($('fVariant')) $('fVariant').onchange = reset;

  $('dl').onclick = () => {
    const rows = filteredRows();
    if (!rows.length) return;
    const blob = new Blob([toCsv(rows)], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'nitro_optimize_results.csv';
    link.click();
  };
}

/* If the report is printed from the browser menu, show every row first so the
   printed copy is complete, then put the page size back afterwards. */
function initPrintHandlers() {
  window.addEventListener('beforeprint', () => {
    savedPageSize = $('pageSize').value;
    $('pageSize').value = 'all';
    page = 1;
    render();
  });
  window.addEventListener('afterprint', () => {
    if (savedPageSize === null) return;
    $('pageSize').value = savedPageSize;
    savedPageSize = null;
    render();
  });
}

initChartPicker();
initControls();
initPrintHandlers();
render();
