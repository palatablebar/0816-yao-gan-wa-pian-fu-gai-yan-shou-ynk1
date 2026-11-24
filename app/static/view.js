import {element, pretty} from './client.js';

const labels = {
  READY:'正式可签', PROVISIONAL:'仅够代理', COVERAGE_GAP:'缺口待补', MISMATCH:'差异待复核',
  PENDING:'待复核', APPROVED:'已签发', HELD:'已暂缓',
};
const runLabels = {...labels, PROVISIONAL:'已代理交付'};
const headers = ['业务分组', '输入行', '全分辨率覆盖', '代理覆盖', '最低覆盖', '结论'];

const recommendations = {
  SIGN_FULL:'全分辨率齐备，可一次正式签发',
  DELIVER_PROXY:'先交临时代理，正式签发待全分辨率瓦片齐备',
  HOLD:'暂不能交付，需补齐覆盖或处理差异',
};

export function badge(status, label = labels) {
  return element('span', label[status] || status, {class:'badge', 'data-result':status, title: status});
}

function cell(row, title) {
  const tr = row.insertCell();
  if (title !== undefined) tr.title = title;
  return tr;
}

export function snapshot(report, selected, stage) {
  const stats = report.intake;
  document.querySelector('[data-metric="input"]').textContent = stats.input;
  document.querySelector('[data-metric="accepted"]').textContent = stats.accepted;
  document.querySelector('[data-metric="isolated"]').textContent = stats.rejected;
  document.querySelector('[data-metric="cases"]').textContent = report.cases?.length ?? '—';
  const table = document.querySelector('#rows');
  table.replaceChildren();
  const head = element('tr');
  const body = table.createTBody();
  if (stage === 'intake') {
    head.append(...['源行', '记录键', '业务分组', '原因码'].map(title => element('th', title, {scope:'col'})));
    for (const item of stats.isolation) {
      const tr = body.insertRow();
      tr.append(...[item.line,item.record,item.case,item.reason].map(value=>element('td',value)));
    }
    if (!stats.isolation.length) body.insertRow().insertCell().textContent = '当前文件没有隔离行';
  } else {
    head.append(...headers.map(title => element('th', title, {scope:'col'})));
    for (const row of report.cases || []) {
      const tr = body.insertRow();
      const button = element('button',row.case,{type:'button','data-case':row.case,'aria-pressed':String(row.case===selected)});
      cell(tr).append(button);
      cell(tr).textContent = row.records.length;
      const formal = row.formal ?? row.measure?.formal;
      const proxy = row.proxy ?? row.measure?.proxy;
      cell(tr, '每块瓦片裁到作业区后取并集，同一像元只计一次').textContent = formal?.covered_cells ?? '—';
      cell(tr, '全分辨率与低分辨率预览合并后的去重覆盖').textContent = proxy?.covered_cells ?? '—';
      cell(tr).textContent = row.measure?.expected ?? '—';
      const decided = row.recommendation !== undefined;
      cell(tr).append(decided ? badge(row.status) : element('span', '待判定', {class:'badge', 'data-result':'PENDING'}));
    }
  }
  table.createTHead().append(head);
  const picked = report.cases?.find(row=>row.case===selected);
  document.querySelector('#detail-title').textContent = picked ? `分组 ${picked.case}` : '采信摘要';
  document.querySelector('#detail').textContent = pretty(detailOf(picked) ?? stats.reasons);
  document.querySelector('#counts').textContent = report.balance ? counts(report.balance) : `采信 ${stats.accepted} 行 · 隔离 ${stats.rejected} 行`;
  renderDelivery(report.balance);
}

function detailOf(picked) {
  if (!picked) return null;
  if (!picked.measure) return picked.prep?.details ?? {原因:picked.status};
  return {
    结论: picked.status,
    建议: recommendations[picked.recommendation] ?? picked.recommendation ?? '—',
    判定依据: picked.basis,
    全分辨率: picked.formal,
    代理: picked.proxy,
    代理增量: picked.proxy_gain_cells,
    瓦片: picked.measure.tiles,
    越出作业区: picked.measure.excluded,
  };
}

function counts(checks) {
  const d = checks.delivery || {};
  return `行数 ${checks.accounted}/${checks.input} · 正式可签 ${checks.ready} 组 · 仅够代理 ${checks.provisional ?? 0} 组 · 待处理 ${checks.pending} 组`;
}

function renderDelivery(checks) {
  const box = document.querySelector('#delivery');
  if (!box) return;
  box.replaceChildren();
  if (!checks) { box.textContent = '先执行批次，再判定交付口径'; return; }
  const choice = checks.delivery?.choice ?? 'HOLD';
  const status = element('strong', recommendations[choice] ?? choice, {class:'delivery-choice', 'data-choice':choice});
  box.append(status);
  const ledger = checks.rows && checks.pixels
    ? `来源 ${checks.rows.source} = 采信 ${checks.rows.accepted} + 隔离 ${checks.rows.isolated} + 忽略 ${checks.rows.ignored} · 采信 ${checks.rows.accepted} = 分组 ${checks.rows.observed} · 像元账 ${checks.pixels.cases.length} 组${checks.pixels.balanced ? '对平' : '未对平'}`
    : '';
  if (ledger) box.append(element('span', ledger, {class:'delivery-ledger'}));
  const blocks = checks.blocks || [];
  if (blocks.length) box.append(element('span', `挡住签发：${blocks.join('；')}`, {class:'delivery-blocks'}));
}

export function history(items, active) {
  const target = document.querySelector('#history');
  target.replaceChildren();
  for (const run of items) {
    const button = element('button', run.id.slice(0,10), {'data-run':run.id,'aria-pressed':String(run.id===active),type:'button'});
    const item = element('li');
    item.append(button, badge(run.status, runLabels));
    target.append(item);
  }
  if (!items.length) target.append(element('li','尚无执行批次'));
}
