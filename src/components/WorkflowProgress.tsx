import {Check, Circle, LoaderCircle} from 'lucide-react';
import {useLanguage} from '@/context/LanguageContext';
import type {Project} from '@/lib/project-api';

/** Progress describes saved work, rather than elapsed time or model thoughts. */
export default function WorkflowProgress({project}: {project:Project}) {
  const {language}=useLanguage();
  const tr=(en:string,ru:string)=>language==='ru'?ru:en;
  const workflow=project.workflow;
  const phase=workflow?.stage;
  const ready=project.outline.length>0 && project.slides.length===project.outline.length && project.slides.every(slide=>slide.design_status==='ready' && slide.design && Object.values(slide.blocks).every(block=>block.status==='ready'));
  const stage=!project.outline.length?0:project.phase==='drafting'?(phase==='planning'||!project.outline.length?0:1):
    project.phase==='designing'?3:project.phase==='outline_draft'?2:
    project.phase==='ready'&&ready?4:phase==='planning'?0:phase==='content'?1:
    phase==='design_planning'||phase==='designing'||phase==='checking'?3:2;
  const active=project.phase==='drafting'||project.phase==='designing';
  const labels=[tr('Plan','План'),tr('Content','Содержание'),tr('Review','Согласование'),tr('Design & check','Оформление и проверка'),tr('Ready','Готово')];
  const actionLabels:Record<string,string>={
    generate_variants:tr('Creating three slide variants','Создаём три варианта слайда'),
    check_slide_notes:tr('Checking slide and notes consistency','Проверяем согласованность слайдов и заметок'),
    revise_block:tr('Revising slide content','Редактируем содержание слайда'),
    revise_slide:tr('Revising the slide','Редактируем слайд'),
    group_sections:tr('Organizing slide sections','Структурируем разделы слайда'),
    analyze_story:tr('Checking the presentation story','Проверяем историю презентации'),
    render_candidates:tr('Rendering alternative designs','Отрисовываем варианты дизайна'),
    select_composition:tr('Comparing visual approaches','Сравниваем визуальные подходы'),
    review_deck:tr('Reviewing the complete presentation','Проверяем презентацию целиком'),
    plan_outline:tr('Planning the presentation','Планируем презентацию'),
    generate_outline:tr('Planning the presentation','Планируем презентацию'),
    write_content:tr('Writing slide content','Создаём содержание слайда'),
    generate_content:tr('Writing slide content','Создаём содержание слайда'),
    plan_deck:tr('Planning the presentation','Планируем презентацию'),
    plan_design:tr('Planning a consistent design','Планируем общий дизайн'),
    apply_composition:tr('Arranging slide elements','Располагаем элементы слайда'),
    inspect_deck:tr('Reading the accepted presentation','Смотрим согласованную презентацию'),
    inspect_compositions:tr('Checking available compositions','Смотрим доступные композиции'),
    compose_slide:tr('Composing the slide','Оформляем слайд'),
    render_slide:tr('Rendering the slide','Отрисовываем слайд'),
    review_slide:tr('Checking the rendered slide','Проверяем отрисованный слайд'),
    refine_slide:tr('Improving the slide','Улучшаем слайд'),
    review_design:tr('Checking the rendered slide','Проверяем отрисованный слайд'),
    inspect_slide:tr('Checking the rendered slide','Проверяем отрисованный слайд'),
    refine_design:tr('Improving the slide','Улучшаем слайд'),
  };
  const latest=workflow?.actions.at(-1);
  const slide=latest?.slide_id?project.outline.find(row=>row.id===latest.slide_id):undefined;
  const activity=phase==='design_planning'&&!['analyze_story','check_slide_notes','generate_variants'].includes(latest?.action??'')?tr('Planning the visual direction for the whole presentation…','Планируем оформление всей презентации…'):
    latest&&actionLabels[latest.action]?actionLabels[latest.action]+(slide?` · ${tr('slide','слайд')} ${slide.order}`:''):
    active?tr('Your presentation is being updated…','Презентация обновляется…'):'';

  return <div className="border-b py-4" aria-label={tr('Presentation progress','Этапы презентации')}>
    <ol className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
      {labels.map((label,index)=><li key={label} className={`flex items-center gap-2 ${index===stage?'font-medium text-foreground':'text-muted-foreground'}`} aria-current={index===stage?'step':undefined}>
        {index<stage?<Check size={15} aria-hidden="true"/>:index===stage&&active?<LoaderCircle size={15} className="animate-spin motion-reduce:animate-none" aria-hidden="true"/>:<Circle size={13} aria-hidden="true"/>}
        {label}
      </li>)}
    </ol>
    {active&&activity&&<p role="status" className="mt-3 text-sm text-muted-foreground">{activity}</p>}
    {phase==='budget_exhausted'&&<p role="alert" className="mt-3 text-sm text-destructive">{tr('The generation limit has been reached. Completed content is saved; automatic requests have stopped.','Достигнут лимит генерации. Готовое содержание сохранено; автоматические запросы остановлены.')}</p>}
    {workflow&&<details className="mt-3 text-sm text-muted-foreground">
      <summary className="w-fit cursor-pointer">{tr('Generation activity','Ход генерации')}</summary>
      <p className="mt-2">{project.build_mode==='model'?tr(`AI requests: ${workflow.model_calls} / ${workflow.request_budget}`,`AI-запросы: ${workflow.model_calls} / ${workflow.request_budget}`):tr(`Model requests: ${workflow.model_calls} / ${workflow.request_budget}`,`Запросы к модели: ${workflow.model_calls} / ${workflow.request_budget}`)}</p>
      <ol className="mt-2 max-h-40 space-y-1 overflow-y-auto">
        {workflow.actions.map(action=>{
          const row=project.outline.find(item=>item.id===action.slide_id);
          return <li key={action.sequence}>{actionLabels[action.action]||tr('Presentation update','Обновление презентации')}{row?` · ${tr('slide','слайд')} ${row.order}`:''} — {action.status==='error'?tr('Interrupted','Прервано'):action.status==='complete'||action.status==='completed'?tr('Done','Готово'):tr('In progress','В работе')}</li>;
        })}
      </ol>
    </details>}
  </div>;
}
