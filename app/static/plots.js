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

export function visualize(report, selected) {
  const target = document.querySelector('#visual');
  const row = report.cases?.find(item=>item.case===selected && item.measure);
  target.replaceChildren();
  if (!row) { target.append(element('p','该分组暂无计算值')); return; }
  const {evidence:e, value, expected, unit} = row.measure;
  render(target, e, value, expected, unit);
}

function render(target,e,value,expected,unit) {
  const grid=zone(target,'coverage-grid');
  const size=value+e.gap_cells;
  const occupied=Math.round(40*value/Math.max(1,size));
  for(let i=0;i<40;i++) zone(grid,i<occupied?'coverage-filled':'coverage-hole');
  zone(target,'coverage-legend',`有效 ${value} · 缺口 ${e.gap_cells} · 重叠多计 ${e.overlap_excess_cells} 像元`);
}
