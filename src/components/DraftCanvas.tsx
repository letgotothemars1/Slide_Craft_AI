import type { Project } from '@/lib/project-api';
import { palettes } from '@/lib/slide-themes';

export default function DraftCanvas({project, slideId, grayscale = true}: {project: Project; slideId: string; grayscale?: boolean}) {
  const item = project.outline.find(row => row.id === slideId);
  const slide = project.slides.find(row => row.id === slideId);
  if (!item) return null;
  const palette = grayscale ? {background: '#ffffff', foreground: '#18181b', muted: '#52525b', panel: '#f4f4f5', accent: '#71717a'} : palettes[project.theme];
  const title = slide?.blocks.title.text || item.title;
  const body = slide?.blocks.body.text ?? '';
  const parts = body.split('|');
  const visual = slide?.visual;
  return <div className="draft-canvas" style={{background: palette.background, color: palette.foreground}} aria-label={`Slide ${item.order} preview`}>
    <div className={`draft-canvas-content draft-${item.layout_type}`}>
      <h3>{title}</h3>
      {item.layout_type === 'comparison' && !visual ? <div className="draft-comparison">{[0,1].map(index => <p key={index} style={{background: palette.panel}}>{parts[index]?.trim() || (slide?.status === 'ready' ? '' : '…')}</p>)}</div>
      : <p className={`draft-body ${visual ? "with-visual" : ""}`} style={{color: palette.muted}}>{(visual ? body.replace(/\|/g, ' / ') : body) || (slide?.status === 'error' ? 'Generation interrupted' : '…')}</p>}
      {visual?.kind === 'process' && <div className="draft-process">{visual.labels.map((label,index)=><div key={index} style={{background: palette.panel}}><span>{index + 1}</span><p>{label}</p></div>)}</div>}
      {visual?.kind === 'bars' && <div className="draft-bars">{visual.labels.map((label,index)=><div key={index}><span>{label}</span><div><i style={{width: `${visual.values[index] / Math.max(...visual.values) * 75}%`,background: palette.accent}}/><b>{visual.values[index]}{visual.unit}</b></div></div>)}</div>}
      <p className="draft-source" style={{color: palette.muted, borderColor: palette.accent}}>{slide?.blocks.source_label.text || 'Source needed'}</p>
    </div>
  </div>;
}
