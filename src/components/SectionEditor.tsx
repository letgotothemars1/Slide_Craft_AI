import {useEffect,useRef,useState} from 'react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Textarea} from '@/components/ui/textarea';
import {saveSlideSections,type Project} from '@/lib/project-api';
import {useLanguage} from '@/context/LanguageContext';

export default function SectionEditor({project,slideId,onChange,onDirtyChange}:{project:Project;slideId:string;onChange:(p:Project)=>void;onDirtyChange:(id:string,key:string,dirty:boolean)=>void}){
  const {language}=useLanguage();const tr=(en:string,ru:string)=>language==='ru'?ru:en;
  const slide=project.slides.find(s=>s.id===slideId)!;
  const [draft,setDraft]=useState(slide.sections??[]);const saved=useRef(JSON.stringify(slide.sections??[]));
  const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const dirty=JSON.stringify(draft)!==JSON.stringify(slide.sections??[]);
  useEffect(()=>{onDirtyChange(slideId,'body',dirty);},[dirty,onDirtyChange,slideId]);
  useEffect(()=>{const prior=saved.current;setDraft(current=>JSON.stringify(current)===prior?(slide.sections??[]):current);saved.current=JSON.stringify(slide.sections??[]);},[slide.sections]);
  const update=(id:string,field:'heading'|'text',value:string)=>setDraft(rows=>rows.map(row=>row.id===id?{...row,[field]:value}:row));
  return <section aria-label={tr('Semantic sections','Смысловые разделы')} className="space-y-5">
    <p className="text-xs text-muted-foreground">{tr('Each section keeps its own text and data during design.','Каждый раздел сохраняет свой текст и данные при оформлении.')}</p>
    {draft.map((section,index)=><fieldset key={section.id} className="space-y-2 border-b pb-4"><legend className="text-sm font-semibold">{tr('Section','Раздел')} {index+1}</legend>
      <label className="text-xs" htmlFor={`section-${section.id}-heading`}>{tr('Section heading','Заголовок раздела')} {index+1}</label><Input id={`section-${section.id}-heading`} value={section.heading} maxLength={100} disabled={busy||project.phase==='designing'} onChange={e=>update(section.id,'heading',e.target.value)}/>
      <label className="block text-xs" htmlFor={`section-${section.id}-text`}>{tr('Section text and data','Текст и данные раздела')} {index+1}</label><Textarea id={`section-${section.id}-text`} rows={6} value={section.text} maxLength={500} disabled={busy||project.phase==='designing'} onChange={e=>update(section.id,'text',e.target.value)}/>
      {draft.length>1&&<Button size="sm" variant="ghost" disabled={busy||project.phase==='designing'} onClick={()=>setDraft(rows=>rows.filter(r=>r.id!==section.id))}>{tr('Remove section','Удалить раздел')} {index+1}</Button>}
    </fieldset>)}
    <div className="flex flex-wrap gap-2"><Button disabled={busy||!dirty||project.phase==='designing'||draft.some(s=>!s.text.trim())} onClick={()=>{setBusy(true);setError('');saveSlideSections(project,slideId,draft).then(onChange).catch(e=>setError(e.message)).finally(()=>setBusy(false));}}>{tr('Save sections','Сохранить разделы')}</Button><Button variant="outline" disabled={busy||draft.length>=4||project.phase==='designing'} onClick={()=>setDraft(rows=>[...rows,{id:crypto.randomUUID(),heading:'',text:''}])}>{tr('Add section','Добавить раздел')}</Button>{dirty&&<Button variant="ghost" disabled={busy} onClick={()=>setDraft(slide.sections??[])}>{tr('Discard section edits','Отменить правки разделов')}</Button>}</div>
    {error&&<p role="alert" className="text-sm text-destructive">{error}</p>}
  </section>;
}
