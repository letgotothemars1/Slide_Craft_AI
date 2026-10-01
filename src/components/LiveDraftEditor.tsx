import {useEffect, useRef, useState} from 'react';
import {Button} from '@/components/ui/button';
import {useLanguage} from '@/context/LanguageContext';
import ThemePicker from '@/components/ThemePicker';
import DraftCanvas from '@/components/DraftCanvas';
import {BlockEditor} from '@/components/SlideWorkspace';
import {confirmDraftSource, changeSlideComposition, hideSlideVisual, approveOutline, startLiveDraft, retryDraftSlide, saveOutline, getProject, downloadProjectPptx, type Project} from '@/lib/project-api';

export default function LiveDraftEditor({project,onChange}: {project: Project; onChange: (p: Project)=>void}) {
  const {language} = useLanguage();
  const tr = (en: string,ru: string)=>language === 'ru' ? ru : en;
  const railRef = useRef<HTMLElement>(null);
  const [selected,setSelected] = useState(project.outline[0]?.id || '');
  const [theme,setTheme] = useState(project.theme);
  const [inspector,setInspector] = useState<'content' | 'sources'>('content');
  const [editTarget,setEditTarget] = useState<'title' | 'body'>('body');
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
  const drafting = project.phase === 'drafting';
  const count = project.slides.filter(row=>row.status === 'ready').length;
  const pending = project.slides.some(row=>Object.values(row.blocks).some(block=>block.status === 'generating'));
  const run = async (action: ()=>Promise<Project | void>)=> {
    setBusy(true); setError('');
    try {const result = await action(); if (result) onChange(result);}
    catch(reason) {setError(reason instanceof Error ? reason.message : tr('Request failed. Try again.','Не удалось выполнить запрос. Повторите.')); getProject(project.id).then(onChange).catch(()=>undefined);}
    finally {setBusy(false);}
  };
  const moveSlide = (direction: -1 | 1)=> {
    if (!item) return;
    const rows = [...project.outline].sort((a,b)=>a.order-b.order);
    const index = rows.findIndex(row=>row.id === selected);
    if (index + direction < 0 || index + direction >= rows.length) return;
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
      {project.phase === 'outline_draft' && <Button disabled={busy || count !== 5 || pending} onClick={()=>setStyling(!styling)}>{tr('Approve & style','Утвердить и оформить')}</Button>}
      {project.phase === 'ready' && <Button disabled={busy || pending} onClick={()=>void run(()=>downloadProjectPptx(project.id))}>{tr('Download PowerPoint','Скачать PowerPoint')}</Button>}
    </header>
    {error && <p role="alert" className="py-3 text-destructive">{error}</p>}
    {styling && <section className="my-6 space-y-4"><h2 className="font-semibold">{tr('Apply a theme to the accepted content','Применить тему к утверждённому содержанию')}</h2><ThemePicker value={theme} onChange={setTheme} disabled={busy}/><Button disabled={busy || pending || count !== 5} onClick={()=>void run(async()=> {const fresh = await approveOutline(project,theme); setStyling(false);return fresh;})}>{tr('Apply theme without regenerating','Применить тему без повторной генерации')}</Button></section>}
    {(project.phase === 'intake' || (project.phase === 'error' && !project.outline.length)) ? <div className="mx-auto max-w-xl py-20">{project.phase === 'error' && <p role="alert" className="mb-4 text-destructive">{tr('The model could not create the structure. Retry or use a key-free draft.','Модель не смогла создать структуру. Повторите или используйте черновик без API.')}</p>}<h2 className="text-xl font-semibold">{tr('See the content take shape','Наблюдайте, как появляется содержание')}</h2><p className="my-4 leading-relaxed text-muted-foreground">{tr('First the structure, then actual slide text. Ready elements can be edited while the next slide is being written.','Сначала структура, затем текст на слайдах. Готовые элементы можно менять, пока создаются следующие слайды.')}</p><div className="flex flex-wrap gap-3"><Button disabled={busy} onClick={()=>void run(()=>startLiveDraft(project,'model'))}>{tr('Generate live draft with AI','Создать живой черновик с AI')}</Button><Button variant="outline" disabled={busy} onClick={()=>void run(()=>startLiveDraft(project,'template'))}>{tr('Use key-free draft','Черновик без API')}</Button></div></div>
    : !item ? <div role="status" className="py-24 text-center text-muted-foreground">{project.build_mode === 'template' ? tr('Preparing a draft from your inputs…','Готовим черновик из ваших материалов…') : tr('Waiting for the model’s structure. No content has arrived yet.','Ожидаем структуру от модели. Содержание ещё не получено.')}</div>
    : <div className="draft-editor-grid">
      <nav ref={railRef} aria-label={tr('Choose a slide','Выбор слайда')} className="draft-thumbnails">{project.outline.map(row=> {
        const savedSlide = project.slides.find(s=>s.id === row.id);
        const state = savedSlide?.status || 'queued';
        const displayTitle = savedSlide?.blocks.title.text || row.title;
        return <button key={row.id} type="button" aria-pressed={row.id === selected} aria-label={`${tr('Slide','Слайд')} ${row.order}: ${displayTitle}`} className={`draft-thumbnail ${row.id === selected ? 'is-selected' : ''}`} onClick={()=>setSelected(row.id)}><DraftCanvas project={project} slideId={row.id} grayscale={project.phase !== 'ready'}/><span className="mt-2 flex justify-between gap-2 text-xs"><span>{row.order}. {displayTitle}</span><span className="text-muted-foreground">{state === 'ready' ? tr('Ready','Готов') : state === 'generating' ? tr('Writing','Создаётся') : state === 'error' ? tr('Error','Ошибка') : tr('Queued','В очереди')}</span></span></button>;
      })}</nav>
      <div className="min-w-0"><div className="mb-3 flex justify-between gap-3 text-sm text-muted-foreground"><span>{tr('Slide','Слайд')} {item.order} / 5</span><span>{project.phase === 'ready' ? tr('Styled','Оформлен') : tr('Content draft · grayscale','Черновик содержания')}</span></div><DraftCanvas project={project} slideId={selected} grayscale={project.phase !== 'ready'}/>{slide?.status === 'generating' && <p role="status" className="mt-4 text-sm text-muted-foreground">{tr('Actual model text is arriving. This body is editable when complete.','Поступает настоящий текст модели. Его можно редактировать после завершения.')}</p>}{slide?.status === 'error' && <div role="alert" className="mt-4 space-y-3"><p>{tr('This slide could not be completed. Other slides are kept.','Этот слайд не удалось завершить. Остальные сохранены.')}</p><Button disabled={busy || drafting} onClick={()=>void run(()=>retryDraftSlide(project,selected))}>{tr('Retry this slide','Повторить этот слайд')}</Button></div>}</div>
      <aside className="draft-inspector"><h2 className="font-semibold">{tr('Slide settings','Настройки слайда')}</h2><p className="mt-2 text-sm text-muted-foreground">{item.purpose}</p><p className="mt-3 text-xs text-muted-foreground">{tr('Composition','Композиция')}: {item.layout_type}</p>
        <div className="my-4 flex gap-2 border-b pb-3"><Button size="sm" variant={inspector === 'content' ? 'default' : 'ghost'} onClick={()=>setInspector('content')}>{tr('Content','Содержание')}</Button><Button size="sm" variant={inspector === 'sources' ? 'default' : 'ghost'} onClick={()=>setInspector('sources')}>{tr('Sources','Источники')}</Button></div>
        {inspector === 'content' && <><fieldset className="mt-4"><legend className="mb-2 text-xs text-muted-foreground">{tr('Choose composition','Выбрать композицию')}</legend><div className="flex flex-wrap gap-2">{(['title','content','comparison'] as const).map(layout=><Button key={layout} size="sm" variant={item.layout_type === layout && !slide?.visual ? 'default' : 'outline'} disabled={busy || drafting || slide?.status !== 'ready'} onClick={()=>void run(()=>changeSlideComposition(project,selected,layout))}>{layout === 'title' ? tr('Cover','Обложка') : layout === 'content' ? tr('Text','Текст') : tr('Two columns','Две колонки')}</Button>)}</div></fieldset>
        {project.phase === 'outline_draft' && <div className="mt-3 flex gap-2"><Button size="sm" variant="ghost" disabled={busy || item.order === 1} onClick={()=>moveSlide(-1)}>{tr('Move earlier','Переместить выше')}</Button><Button size="sm" variant="ghost" disabled={busy || item.order === 5} onClick={()=>moveSlide(1)}>{tr('Move later','Переместить ниже')}</Button></div>}
        {slide?.visual && <div className="mt-4"><p className="text-sm">{slide.visual.kind === 'process' ? tr('Process diagram','Схема процесса') : tr('Bar comparison · check the PDF context','Сравнение чисел · проверьте контекст в PDF')}</p><Button className="mt-2" size="sm" variant="outline" disabled={busy || slide.status !== 'ready'} onClick={()=>void run(()=>hideSlideVisual(project,selected))}>{tr('Use text only','Оставить только текст')}</Button></div>}
        </>}
        {inspector === 'sources' && <details open className="mt-6 border-t pt-4"><summary className="cursor-pointer text-sm font-medium">{tr('Shared PDF & sources','Общий PDF и источники')}</summary><p className="mt-3 break-words text-xs text-muted-foreground">{project.source_filename || tr('No PDF uploaded','PDF не загружен')}</p>{item.suggested_refs.map((ref,index)=><div key={index} className="mt-4 space-y-2 text-sm"><p className="font-medium">{tr('Suggested page','Предложенная страница')} {ref.page_number}</p><p className="max-h-32 overflow-auto text-xs leading-relaxed text-muted-foreground">{ref.excerpt}</p><p className="text-xs">{tr('Check that the excerpt supports this slide.','Проверьте, подтверждает ли фрагмент содержание слайда.')}</p><Button size="sm" variant="outline" disabled={busy || drafting || project.phase !== 'outline_draft' || slide?.status !== 'ready' || item.evidence_refs.some(r=>r.page_number === ref.page_number && r.excerpt === ref.excerpt)} onClick={()=>void run(confirmSource)}>{item.evidence_refs.some(r=>r.page_number === ref.page_number && r.excerpt === ref.excerpt) ? tr('Source confirmed','Источник подтверждён') : tr('Confirm this source','Подтвердить источник')}</Button></div>)}</details>}
        {slide && <div className="mt-6 space-y-5 border-t pt-4">{inspector === 'content' && <div className="flex gap-2"><Button size="sm" variant={editTarget === 'title' ? 'default' : 'ghost'} onClick={()=>setEditTarget('title')}>{tr('Title','Заголовок')}</Button><Button size="sm" variant={editTarget === 'body' ? 'default' : 'ghost'} onClick={()=>setEditTarget('body')}>{tr('Slide text','Текст слайда')}</Button></div>}{(() => {const key = inspector === 'sources' ? 'source_label' : editTarget;return slide.blocks[key].status === 'ready' || slide.status === 'ready' ? <BlockEditor key={`${selected}-${key}`} project={project} slideId={selected} blockKey={key} onChange={onChange}/> : <p role="status" className="text-sm text-muted-foreground">{tr('This element is still being written.','Этот элемент ещё создаётся.')}</p>;})()}</div>}

      </aside>
    </div>}
  </section>;
}
