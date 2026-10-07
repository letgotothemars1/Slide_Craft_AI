import {useEffect,useState} from 'react';
import {Textarea} from '@/components/ui/textarea';
import {Button} from '@/components/ui/button';
import {useLanguage} from '@/context/LanguageContext';
import {saveSpeakerNotes,type Project} from '@/lib/project-api';
export default function SpeakerNotesEditor({project,slideId,disabled,onChange,onDirtyChange}:{project:Project;slideId:string;disabled:boolean;onChange:(p:Project)=>void;onDirtyChange:(id:string,key:string,dirty:boolean)=>void}) {
  const {language}=useLanguage();const tr=(en:string,ru:string)=>language==='ru'?ru:en;
  const slide=project.slides.find(row=>row.id===slideId);const [drafts,setDrafts]=useState<Record<string,string>>({});const [saving,setSaving]=useState(false);const [editing,setEditing]=useState<Record<string,boolean>>({});const [error,setError]=useState('');
  const saved=slide?.speaker_notes??'';const value=drafts[slideId]??saved;const dirty=value!==saved;
  useEffect(()=>{for(const row of project.slides)onDirtyChange(row.id,'notes',row.id in drafts && drafts[row.id] !== (row.speaker_notes??''));},[drafts,project.slides,onDirtyChange]);
  if(!slide||slide.status!=='ready')return null;
  const save=async()=>{setSaving(true);setError('');try{const fresh=await saveSpeakerNotes(project,slideId,value);setDrafts(previous=>{const next={...previous};delete next[slideId];return next;});setEditing(previous=>({...previous,[slideId]:false}));onChange(fresh);}catch{setError(tr('Notes could not be saved. Your edits are kept.','Не удалось сохранить заметки. Ваши правки сохранены в поле.'));}finally{setSaving(false);}};
  return <section aria-label={tr("Speaker notes","Заметки докладчика")} className="speaker-notes-panel">
    <h3 className="text-sm font-semibold">{tr("What to say with this slide","Что рассказать по этому слайду")}</h3>
    <p className="mt-2 text-sm text-muted-foreground">{tr('Explain the claim, connect it to the slide and lead into the next point. Notes are included in PowerPoint.','Объясните мысль, свяжите её с содержанием слайда и перейдите к следующему пункту. Заметки попадут в PowerPoint.')}</p>
    {project.workflow?.coherence_review && <p role="status" className="mt-3 text-xs text-muted-foreground">{project.workflow.coherence_review.approved
      ? project.workflow.coherence_review.mode === 'model' ? tr('AI checked slide and notes consistency.','AI проверил согласованность слайдов и заметок.') : tr('AI consistency check is unavailable in key-free mode.','Проверка согласованности с AI недоступна в режиме без API.')
      : tr('Content and notes need review before final design.','Перед финальным дизайном нужно проверить содержание и заметки.')}</p>}
    {!saved&&!dirty&&<p className="mt-2 text-sm text-muted-foreground">{tr('This older slide has no generated notes. New drafts include them automatically.','На этом старом слайде нет сгенерированных заметок. Новые черновики включают их автоматически.')}</p>}
    {(!editing[slideId] && !dirty) ? <><div className="speaker-notes-reading mt-4 whitespace-pre-wrap text-sm leading-relaxed">{saved || tr("No notes yet.","Заметок пока нет.")}</div><Button className="mt-4" variant="outline" disabled={disabled||saving} onClick={()=>setEditing(previous=>({...previous,[slideId]:true}))}>{tr("Edit speaker notes","Редактировать заметки")}</Button></> : <>
    <label className="mt-3 block text-sm" htmlFor={`speaker-notes-${slideId}`}>{tr('Speaker notes','Заметки докладчика')}</label>
    <Textarea id={`speaker-notes-${slideId}`} className="mt-2" rows={8} maxLength={4000} value={value} disabled={disabled||saving} onChange={event=>setDrafts(previous=>({...previous,[slideId]:event.target.value}))}/>
    <div className="mt-3 flex flex-wrap gap-2"><Button disabled={!dirty||disabled||saving} onClick={()=>void save()}>{saving?tr('Saving notes…','Сохраняем заметки…'):tr('Save speaker notes','Сохранить заметки')}</Button><Button variant="outline" disabled={saving} onClick={()=>{setDrafts(previous=>{const next={...previous};delete next[slideId];return next;});setEditing(previous=>({...previous,[slideId]:false}));}}>{dirty?tr('Discard note edits','Отменить правки заметок'):tr('Read notes','Читать заметки')}</Button></div></>}
    {dirty&&<p className="mt-2 text-xs text-muted-foreground">{tr('Save notes before final design.','Сохраните заметки перед финальным оформлением.')}</p>}
    {error&&<p role="alert" className="mt-2 text-sm text-destructive">{error}</p>}
  </section>;
}
