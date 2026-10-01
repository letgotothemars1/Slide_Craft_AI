import type { Project } from '@/lib/project-api';
import {useLanguage} from '@/context/LanguageContext';
import { palettes } from '@/lib/slide-themes';

export default function DraftCanvas({project, slideId, grayscale = true, onSelectBlock}: {project: Project; slideId: string; grayscale?: boolean; onSelectBlock?: (key: 'title' | 'body' | 'source_label', column?: number) => void}) {
  const {language} = useLanguage();
  const editable = (key: 'title' | 'body' | 'source_label', column?: number) => onSelectBlock ? {
    role: 'button', tabIndex: 0, className: 'draft-editable',
    'aria-label': language === 'ru' ? key === 'title' ? 'Редактировать заголовок' : key === 'body' ? column === undefined ? 'Редактировать текст слайда' : `Редактировать колонку ${column + 1}` : 'Редактировать подпись источника' : key === 'title' ? 'Edit title' : key === 'body' ? column === undefined ? 'Edit slide text' : `Edit column ${column + 1}` : 'Edit source label',
    onClick: () => onSelectBlock(key, column),
    onKeyDown: (event: React.KeyboardEvent) => {if (event.key === 'Enter' || event.key === ' ') {event.preventDefault(); onSelectBlock(key, column);}},
  } : {};
  const item = project.outline.find(row => row.id === slideId);
  const slide = project.slides.find(row => row.id === slideId);
  if (!item) return null;
  const palette = grayscale ? {background: '#ffffff', foreground: '#18181b', muted: '#52525b', panel: '#f4f4f5', accent: '#71717a'} : palettes[project.theme];
  const title = slide?.blocks.title.text || item.title;
  const body = slide?.blocks.body.text ?? '';
  const parts = body.split('|');
  const visual = slide?.blocks.body.status === 'generating' ? undefined : slide?.visual;
  if (slide?.scene?.length && slide.design) return <div className="draft-canvas designed-canvas" aria-label={`Slide ${item.order} preview`}>
    {slide.scene.map((element,index) => <div key={index} {...(element.block_key ? editable(element.block_key,element.column ?? undefined) : {})} style={{position:'absolute',left:`${element.x}%`,top:`${element.y/56.25*100}%`,width:`${element.w}%`,height:`${element.h/56.25*100}%`,background:element.kind === 'rect' ? element.color : undefined,color:element.color,fontSize:`${element.size}cqw`,fontFamily:element.font,fontWeight:element.bold ? 700 : 400,lineHeight:1.16,whiteSpace:'pre-wrap',overflowWrap:'break-word',overflow:'hidden'}}>{element.kind === 'text' ? element.text : null}</div>)}
  </div>;
  return <div className="draft-canvas" style={{background: palette.background, color: palette.foreground}} aria-label={`Slide ${item.order} preview`}>
    <div className={`draft-canvas-content draft-${item.layout_type}`}>
      <h3 {...editable('title')}>{title}</h3>
      {item.layout_type === 'comparison' && !visual ? <div className="draft-comparison">{[0,1].map(index => <p key={index} {...editable('body', index)} style={{background: palette.panel}}>{parts[index]?.trim() || (slide?.status === 'ready' ? '' : '…')}</p>)}</div>
      : <p {...editable('body')} className={`draft-body ${visual ? "with-visual" : body.length > 250 ? "dense-body" : ""} ${onSelectBlock ? "draft-editable" : ""}`} style={{color: palette.muted}}>{(visual ? body.replace(/\|/g, ' / ') : body) || (slide?.status === 'error' ? 'Generation interrupted' : '…')}</p>}
      {visual?.kind === 'process' && <div className="draft-process">{visual.labels.map((label,index)=><div key={index} style={{background: palette.panel}}><span>{index + 1}</span><p>{label}</p></div>)}</div>}
      {visual?.kind === 'bars' && <div className="draft-bars">{visual.labels.map((label,index)=><div key={index}><span>{label}</span><div><i style={{width: `${visual.values[index] / Math.max(...visual.values) * 75}%`,background: palette.accent}}/><b>{visual.values[index]}{visual.unit}</b></div></div>)}</div>}
      {slide?.show_source && <p {...editable('source_label')} className={`draft-source ${onSelectBlock ? "draft-editable" : ""}`} style={{color: palette.muted, borderColor: palette.accent}}>{slide?.blocks.source_label.text || 'Source needed'}</p>}
    </div>
  </div>;
}
