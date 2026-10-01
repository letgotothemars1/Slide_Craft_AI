import {useCallback, useEffect, useRef, useState} from 'react';
import {ArrowUp, ArrowDown} from 'lucide-react';
import {Skeleton} from '@/components/ui/skeleton';
import {Textarea} from '@/components/ui/textarea';
import {Button} from '@/components/ui/button';
import {useLanguage} from '@/context/LanguageContext';
import ThemePicker from '@/components/ThemePicker';
import DraftCanvas from '@/components/DraftCanvas';
import {BlockEditor} from '@/components/SlideWorkspace';
import {regenerateWholeSlide, setSlideSourceVisibility, confirmDraftSource, changeSlideComposition, hideSlideVisual, approveOutline, startLiveDraft, retryDraftSlide, saveOutline, getProject, downloadProjectPptx, type Project} from '@/lib/project-api';

export default function LiveDraftEditor({project,onChange}: {project: Project; onChange: (p: Project)=>void}) {
  const {language} = useLanguage();
  const tr = (en: string,ru: string)=>language === 'ru' ? ru : en;
  const railRef = useRef<HTMLElement>(null);
  const [selected,setSelected] = useState(project.outline[0]?.id || '');
  const [theme,setTheme] = useState(project.theme);
  const [inspector,setInspector] = useState<'content' | 'sources'>('content');
  const [editTarget,setEditTarget] = useState<'title' | 'body'>('body');
  const [instructions,setInstructions] = useState<Record<string,string>>({});
  const [dirtyBlocks,setDirtyBlocks] = useState<Record<string,boolean>>({});
  const trackDirty = useCallback((slideId: string, key: string, dirty: boolean) => {
    setDirtyBlocks(previous => previous[`${slideId}-${key}`] === dirty ? previous : {...previous,[`${slideId}-${key}`]:dirty});
  }, []);
  const [focusRequest,setFocusRequest] = useState<{id: string; sequence: number} | null>(null);
  const selectBlock = (key: 'title' | 'body' | 'source_label', column?: number) => {
    setInspector(key === 'source_label' ? 'sources' : 'content');
    if (key !== 'source_label') setEditTarget(key);
    setFocusRequest(previous => ({id: key === 'body' && item?.layout_type === 'comparison' ? `comparison-${column ?? 0}` : `block-${key}`, sequence: (previous?.sequence ?? 0) + 1}));
  };
  useEffect(() => {
    if (!focusRequest) return;
    const field = document.getElementById(focusRequest.id);
    field?.scrollIntoView?.({block: 'nearest', behavior: 'auto'});
    field?.focus({preventScroll: true});
  }, [focusRequest]);
  const [styling,setStyling] = useState(false);
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  useEffect(()=> {if (!project.outline.some(row=>row.id === selected)) setSelected(project.outline[0]?.id || '');},[project.outline,selected]);
  useEffect(()=> {
    const revealSelection = ()=> {
      const rail = railRef.current;
      const active = rail?.querySelector<HTMLElement>('[aria-pressed="true"]');
      if (!rail || !active || !window.matchMedia('(max-width: 640px)').matches) return;
      const left = active.getBoundingClientRect().left - rail.getBoundingClientRect().left + rail.scrollLeft;
      rail.scrollTo({left: left - (rail.clientWidth - active.clientWidth) / 2, behavior: 'auto'});
    };
    revealSelection();
    window.addEventListener('resize',revealSelection);
    return ()=>window.removeEventListener('resize',revealSelection);
  },[selected]);
  const item = project.outline.find(row=>row.id === selected);
  const slide = project.slides.find(row=>row.id === selected);
  const revising = slide?.blocks.title.status === 'generating' || slide?.blocks.body.status === 'generating';
  const instruction = instructions[selected] ?? slide?.revision_instruction ?? '';
  const hasUnsavedText = dirtyBlocks[`${selected}-title`] || dirtyBlocks[`${selected}-body`];
  const drafting = project.phase === 'drafting';
  const count = project.slides.filter(row=>row.status === 'ready').length;
  const pending = project.slides.some(row=>Object.values(row.blocks).some(block=>block.status === 'generating'));
  const run = async (action: ()=>Promise<Project | void>)=> {
    setBusy(true); setError('');
    try {const result = await action(); if (result) onChange(result);}
    catch(reason) {setError(reason instanceof Error ? reason.message : tr('Request failed. Try again.','Не удалось выполнить запрос. Повторите.')); getProject(project.id).then(onChange).catch(()=>undefined);}
    finally {setBusy(false);}
  };
  const moveSlide = (slideId: string, direction: -1 | 1)=> {
    const rows = [...project.outline].sort((a,b)=>a.order-b.order);
    const index = rows.findIndex(row=>row.id === slideId);
    if (index < 0 || index + direction < 0 || index + direction >= rows.length) return;
    [rows[index],rows[index+direction]] = [rows[index+direction],rows[index]];
    void run(()=>saveOutline(project,rows.map((row,i)=>({...row,order:i+1}))));
  };
  const confirmSource = async ()=> {
    if (!item?.suggested_refs.length) return;
    return confirmDraftSource(project,selected,item.suggested_refs[0]);
  };
  return <section aria-label={tr('Visual draft editor','Редактор черновика')} className="live-draft">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b pb-5">
      <div><h1 className="font-display text-2xl font-bold">{tr('Presentation draft','Черновик презентации')}</h1><p role="status" className="mt-1 text-sm text-muted-foreground">{drafting ? project.outline.length ? tr('Writing slide content live','Содержание появляется по мере генерации') : tr('Planning five slides…','Планируем пять слайдов…') : project.phase === 'ready' ? tr('Accepted content · edits are included in PowerPoint','Содержание утверждено · правки попадут в PowerPoint') : tr('Review the content before applying a theme','Проверьте содержание перед применением темы')} {project.slides.length > 0 && `· ${count}/5`}</p></div>
      {project.phase === 'outline_draft' && <Button aria-expanded={styling} aria-controls="presentation-finish" variant={styling ? 'outline' : 'default'} disabled={busy || count !== 5 || pending} onClick={()=>setStyling(true)}>{tr('Approve & style','Утвердить и оформить')}</Button>}
      {project.phase === 'ready' && <Button disabled={busy || pending} onClick={()=>void run(()=>downloadProjectPptx(project.id))}>{tr('Download PowerPoint','Скачать PowerPoint')}</Button>}
    </header>
    {error && <p role="alert" className="py-3 text-destructive">{error}</p>}
    {styling && <section id="presentation-finish" aria-label={tr('Finish your presentation','Завершить презентацию')} className="my-6 space-y-5 rounded-xl border border-primary/30 bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-lg font-semibold">{tr('Finish your presentation','Завершить презентацию')}</h2><p className="mt-1 text-sm text-muted-foreground">{tr('Choose a theme. Your presentation will then be ready to download as PowerPoint.','Выберите тему. Затем презентацию можно будет скачать в PowerPoint.')}</p></div><Button size="lg" className="w-full sm:w-auto" disabled={busy || pending || count !== 5} onClick={()=>void run(async()=> {const fresh = await approveOutline(project,theme); setStyling(false);return fresh;})}>{busy ? tr('Finishing…','Завершаем…') : tr('Finish presentation','Завершить презентацию')}</Button></div><ThemePicker value={theme} onChange={setTheme} disabled={busy}/></section>}
    {(project.phase === 'intake' || (project.phase === 'error' && !project.outline.length)) ? <div className="mx-auto max-w-xl py-20">{project.phase === 'error' && <p role="alert" className="mb-4 text-destructive">{tr('The model could not create the structure. Retry or use a key-free draft.','Модель не смогла создать структуру. Повторите или используйте черновик без API.')}</p>}<h2 className="text-xl font-semibold">{tr('See the content take shape','Наблюдайте, как появляется содержание')}</h2><p className="my-4 leading-relaxed text-muted-foreground">{tr('First the structure, then actual slide text. Ready elements can be edited while the next slide is being written.','Сначала структура, затем текст на слайдах. Готовые элементы можно менять, пока создаются следующие слайды.')}</p><div className="flex flex-wrap gap-3"><Button disabled={busy} onClick={()=>void run(()=>startLiveDraft(project,'model'))}>{tr('Generate live draft with AI','Создать живой черновик с AI')}</Button><Button variant="outline" disabled={busy} onClick={()=>void run(()=>startLiveDraft(project,'template'))}>{tr('Use key-free draft','Черновик без API')}</Button></div></div>
    : !item ? <div role="status" aria-label={tr('Preparing your slides','Готовим слайды')} className="draft-editor-grid" aria-busy="true"><span className="sr-only">{tr('Preparing your slides','Готовим слайды')}</span><div aria-hidden="true" className="draft-thumbnails">{Array.from({length:5},(_,index)=><Skeleton key={index} className="aspect-video w-full shrink-0 motion-reduce:animate-none max-sm:w-[140px]"/>)}</div><div aria-hidden="true" className="min-w-0"><Skeleton className="mb-3 h-4 w-28 motion-reduce:animate-none"/><div className="aspect-video border bg-card p-[6%]"><Skeleton className="mb-4 h-7 w-3/4 motion-reduce:animate-none"/><Skeleton className="mb-8 h-7 w-1/2 motion-reduce:animate-none"/><div className="space-y-3">{[1,2,3].map(index=><Skeleton key={index} className="h-4 w-full motion-reduce:animate-none"/>)}</div></div></div><div aria-hidden="true" className="draft-inspector space-y-5"><Skeleton className="h-5 w-32 motion-reduce:animate-none"/><Skeleton className="h-20 w-full motion-reduce:animate-none"/><Skeleton className="h-40 w-full motion-reduce:animate-none"/></div></div>
    : <div className="draft-editor-grid">
      <nav ref={railRef} aria-label={tr('Choose a slide','Выбор слайда')} className="draft-thumbnails">{project.outline.map(row=> {
        const savedSlide = project.slides.find(s=>s.id === row.id);
        const state = savedSlide?.status || 'queued';
        const displayTitle = savedSlide?.blocks.title.text || row.title;
        return <div key={row.id} className="draft-thumbnail-row"><button type="button" aria-pressed={row.id === selected} aria-label={`${tr('Slide','Слайд')} ${row.order}: ${displayTitle}`} className={`draft-thumbnail ${row.id === selected ? 'is-selected' : ''}`} onClick={()=>setSelected(row.id)}><DraftCanvas project={project} slideId={row.id} grayscale={project.phase !== 'ready'}/><span className="mt-2 flex justify-between gap-2 text-xs"><span>{row.order}. {displayTitle}</span><span className="text-muted-foreground">{state === 'ready' ? tr('Ready','Готов') : state === 'generating' ? tr('Writing','Создаётся') : state === 'error' ? tr('Error','Ошибка') : tr('Queued','В очереди')}</span></span></button>{project.phase === 'outline_draft' && <div className="draft-reorder">{([-1,1] as const).map(direction => <button key={direction} type="button" aria-label={tr(`Move slide ${row.order} ${direction === -1 ? 'up' : 'down'}`, `Переместить слайд ${row.order} ${direction === -1 ? 'выше' : 'ниже'}`)} disabled={busy || pending || row.order === (direction === -1 ? 1 : project.outline.length)} onClick={() => moveSlide(row.id,direction)}>{direction === -1 ? <ArrowUp size={16}/> : <ArrowDown size={16}/>}</button>)}</div>}</div>;
      })}</nav>
      <div className="min-w-0"><div className="mb-3 flex justify-between gap-3 text-sm text-muted-foreground"><span>{tr('Slide','Слайд')} {item.order} / 5</span><span>{project.phase === 'ready' ? tr('Styled','Оформлен') : tr('Content draft · grayscale','Черновик содержания')}</span></div><DraftCanvas project={project} slideId={selected} grayscale={project.phase !== 'ready'} onSelectBlock={selectBlock}/>{slide?.status === 'generating' && <p role="status" className="mt-4 text-sm text-muted-foreground">{tr('Actual model text is arriving. This body is editable when complete.','Поступает настоящий текст модели. Его можно редактировать после завершения.')}</p>}{slide?.status === 'error' && <div role="alert" className="mt-4 space-y-3"><p>{tr('This slide could not be completed. Other slides are kept.','Этот слайд не удалось завершить. Остальные сохранены.')}</p><Button disabled={busy || drafting} onClick={()=>void run(()=>retryDraftSlide(project,selected))}>{tr('Retry this slide','Повторить этот слайд')}</Button></div>}{slide && ['outline_draft','ready'].includes(project.phase) && <section className="mt-6 space-y-3 border-t pt-5" aria-label={tr('Revise this slide','Изменить этот слайд')}><label className="block text-sm font-medium" htmlFor="slide-revision-instruction">{tr('What should change on this slide?','Что нужно изменить на этом слайде?')}</label><Textarea id="slide-revision-instruction" rows={3} maxLength={1000} value={instruction} disabled={busy || revising} placeholder={tr('For example: focus on the limitations, shorten the text and replace the diagram with clear steps.','Например: сделай акцент на ограничениях, сократи текст и замени схему понятными шагами.')} onChange={event=>setInstructions(previous=>({...previous,[selected]:event.target.value}))}/><div className="flex flex-wrap items-center gap-3"><Button disabled={busy || revising || hasUnsavedText || !instruction.trim()} onClick={()=>void run(()=>regenerateWholeSlide(project,selected,instruction))}>{revising ? tr('Revising slide…','Меняем слайд…') : tr('Regenerate this slide with AI','Перегенерировать этот слайд с AI')}</Button><p className="text-xs text-muted-foreground">{hasUnsavedText ? tr('Save or discard your text edits first.','Сначала сохраните или отмените правки текста.') : tr('Updates this slide’s title, text and visual.','Обновит заголовок, текст и визуал этого слайда.')}</p></div>{slide.blocks.body.error?.startsWith('Slide revision failed') && <p role="alert" className="text-sm text-destructive">{tr('Slide revision failed. Your previous content is kept. Try again.','Не удалось изменить слайд. Прежнее содержание сохранено. Повторите попытку.')}</p>}</section>}</div>
      <aside className="draft-inspector"><h2 className="font-semibold">{tr('Slide settings','Настройки слайда')}</h2><p className="mt-2 text-sm text-muted-foreground">{item.purpose}</p><p className="mt-3 text-xs text-muted-foreground">{tr('Composition','Композиция')}: {item.layout_type}</p>
        <div className="my-4 flex gap-2 border-b pb-3"><Button size="sm" variant={inspector === 'content' ? 'default' : 'ghost'} onClick={()=>setInspector('content')}>{tr('Content','Содержание')}</Button><Button size="sm" variant={inspector === 'sources' ? 'default' : 'ghost'} onClick={()=>setInspector('sources')}>{tr('Sources','Источники')}</Button></div>
        {inspector === 'content' && <><fieldset className="mt-4"><legend className="mb-2 text-xs text-muted-foreground">{tr('Choose composition','Выбрать композицию')}</legend><div className="flex flex-wrap gap-2">{(['title','content','comparison'] as const).map(layout=><Button key={layout} size="sm" variant={item.layout_type === layout && !slide?.visual ? 'default' : 'outline'} disabled={busy || drafting || slide?.status !== 'ready'} onClick={()=>void run(()=>changeSlideComposition(project,selected,layout))}>{layout === 'title' ? tr('Cover','Обложка') : layout === 'content' ? tr('Text','Текст') : tr('Two columns','Две колонки')}</Button>)}</div></fieldset>

        {slide?.visual && <div className="mt-4"><p className="text-sm">{slide.visual.kind === 'process' ? tr('Process diagram','Схема процесса') : tr('Bar comparison · check the PDF context','Сравнение чисел · проверьте контекст в PDF')}</p><Button className="mt-2" size="sm" variant="outline" disabled={busy || slide.status !== 'ready'} onClick={()=>void run(()=>hideSlideVisual(project,selected))}>{tr('Use text only','Оставить только текст')}</Button></div>}
        </>}
        {inspector === 'sources' && <details open className="mt-6 border-t pt-4"><summary className="cursor-pointer text-sm font-medium">{tr('Shared PDF & sources','Общий PDF и источники')}</summary><label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={Boolean(slide?.show_source)} disabled={busy} onChange={event=>void run(()=>setSlideSourceVisibility(project,selected,event.target.checked))}/>{tr('Show source label on this slide','Показывать подпись источника на этом слайде')}</label><p className="mt-3 break-words text-xs text-muted-foreground">{project.source_filename || tr('No PDF uploaded','PDF не загружен')}</p>{item.suggested_refs.map((ref,index)=><div key={index} className="mt-4 space-y-2 text-sm"><p className="font-medium">{tr('Suggested page','Предложенная страница')} {ref.page_number}</p><p className="draft-source-excerpt text-sm leading-relaxed text-muted-foreground">{ref.excerpt}</p><p className="text-xs">{tr('Check that the excerpt supports this slide.','Проверьте, подтверждает ли фрагмент содержание слайда.')}</p><Button size="sm" variant="outline" disabled={busy || drafting || project.phase !== 'outline_draft' || slide?.status !== 'ready' || item.evidence_refs.some(r=>r.page_number === ref.page_number && r.excerpt === ref.excerpt)} onClick={()=>void run(confirmSource)}>{item.evidence_refs.some(r=>r.page_number === ref.page_number && r.excerpt === ref.excerpt) ? tr('Source confirmed','Источник подтверждён') : tr('Confirm this source','Подтвердить источник')}</Button></div>)}</details>}
        {slide && <div className="mt-6 space-y-5 border-t pt-4">{inspector === 'content' && <div className="flex gap-2"><Button size="sm" variant={editTarget === 'title' ? 'default' : 'ghost'} onClick={()=>setEditTarget('title')}>{tr('Title','Заголовок')}</Button><Button size="sm" variant={editTarget === 'body' ? 'default' : 'ghost'} onClick={()=>setEditTarget('body')}>{tr('Slide text','Текст слайда')}</Button></div>}{(['title','body','source_label'] as const).map(key => <div key={`${selected}-${key}`} hidden={key !== (inspector === 'sources' ? 'source_label' : editTarget)}>{slide.blocks[key].status === 'ready' || slide.status === 'ready' ? <BlockEditor project={project} slideId={selected} blockKey={key} onChange={onChange} roomy onDirtyChange={trackDirty}/> : <p role="status" className="text-sm text-muted-foreground">{tr('This element is still being written.','Этот элемент ещё создаётся.')}</p>}</div>)}</div>}

      </aside>
    </div>}
  </section>;
}
