import {element} from './client.js';

function zone(target, className, text) {
  const box = element('div', undefined, {class:className});
  if (text) box.append(element('span',text));
  target.append(box);
  return box;
}

function fill(layer, value, max, label) {
  const mark = zone(layer, 'mark-piece', label);
  mark.style.setProperty('--part', `${Math.max(0,Math.min(100,100*value/Math.max(1,max)))}%`);
  return mark;
}

function bar(target, label, covered, region, tier) {
  const row = zone(target, 'coverage-row', `${label} ${covered}/${region}`);
  row.dataset.tier = tier;
  const track = zone(row, 'coverage-track');
  const fill = zone(track, 'coverage-filled');
  fill.style.width = `${Math.max(0,Math.min(100,100*covered/Math.max(1,region)))}%`;
  return row;
}

export function visualize(report, selected) {
  const target = document.querySelector('#visual');
  const row = report.cases?.find(item=>item.case===selected && item.measure);
  target.replaceChildren();
  if (!row) { target.append(element('p','该分组暂无计算值')); return; }
  const measure = row.measure;
  const formal = row.formal ?? measure.formal;
  const proxy = row.proxy ?? measure.proxy;
  const region = formal?.region_cells ?? (measure.value + measure.evidence.gap_cells);
  if (formal && proxy) {
    bar(target, '全分辨率瓦片', formal.covered_cells, region, 'formal');
    bar(target, '代理覆盖（全分辨率+低分辨率预览）', proxy.covered_cells, region, 'proxy');
    const gain = proxy.covered_cells - formal.covered_cells;
    zone(target, 'coverage-legend',
      `最低覆盖 ${measure.expected} · 全分辨率缺口 ${formal.gap_cells} · 代理增量 ${gain} · 越出作业区 ${measure.excluded?.outside_cells ?? 0} 像元（不计入覆盖）`);
    return;
  }
  const grid=zone(target,'coverage-grid');
  const size=measure.value+measure.evidence.gap_cells;
  const occupied=Math.round(40*measure.value/Math.max(1,size));
  for(let i=0;i<40;i++) zone(grid,i<occupied?'coverage-filled':'coverage-hole');
  zone(target,'coverage-legend',`有效 ${measure.value} · 缺口 ${measure.evidence.gap_cells} · 重叠多计 ${measure.evidence.overlap_excess_cells} 像元`);
}
