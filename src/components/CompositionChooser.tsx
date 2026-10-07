import {useEffect,useState} from 'react';
import {Button} from '@/components/ui/button';
import {useLanguage} from '@/context/LanguageContext';
import DraftCanvas from './DraftCanvas';
import {chooseComposition,generateCompositionChoices,getCompositionChoices,type CompositionChoice,type Project} from '@/lib/project-api';

export default function CompositionChooser({project,slideId,disabled,onChange}:{project:Project;slideId:string;disabled:boolean;onChange:(p:Project)=>void}) {
  const {language}=useLanguage();
  const tr=(en:string,ru:string)=>language==='ru'?ru:en;
  const slide=project.slides.find(row=>row.id===slideId);
  const [choices,setChoices]=useState<CompositionChoice[]>([]);
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  const [saving,setSaving]=useState(false);
  const [retry,setRetry]=useState(0);
  const projectId=project.id;
  const slideStatus=slide?.status;
  const variantsStatus=slide?.variants_status;
  const variantsFingerprint=slide?.variants_fingerprint;
  const previewLoadError=tr('Variants could not load. Reload to try again.','Не удалось загрузить варианты. Повторите загрузку.');
  const previewTheme=project.theme;
  const variantPlansKey=JSON.stringify([slide?.composition_variants,slide?.design]);
  useEffect(()=>{
    let ignore=false;
    setChoices([]);setError('');setLoading(false);
    if(slideStatus!=='ready'||variantsStatus!=='ready')return;
    setLoading(true);
    getCompositionChoices(projectId,slideId).then(result=>{
      if(!ignore){setChoices(result);setLoading(false);}
    }).catch(()=>{
      if(!ignore){setError(previewLoadError);setLoading(false);}
    });
    return()=>{ignore=true;};
  },[projectId,slideId,slideStatus,variantsStatus,variantsFingerprint,variantPlansKey,previewTheme,previewLoadError,retry]);
  const select=async(choice:CompositionChoice)=>{
    if(choice.id===slide?.selected_variant_id)return;
    setSaving(true);setError('');
    try{onChange(await chooseComposition(project,slideId,choice.id));}
    catch{setError(tr('Could not save this choice. Refresh and try again.','Не удалось сохранить выбор. Обновите страницу и повторите.'));}
    finally{setSaving(false);}
  };
  const generate=async()=>{
    setSaving(true);setError('');
    try{onChange(await generateCompositionChoices(project,slideId));}
    catch(reason){setError(reason instanceof Error?reason.message:tr('Could not start variant generation. Try again.','Не удалось запустить генерацию вариантов. Повторите.'));}
    finally{setSaving(false);}
  };
  if(!slide||slide.status!=='ready')return null;
  const generating=slide.variants_status==='generating';
  const labels={selected:tr('Recommended','Рекомендованный'),alternative:tr('Alternative','Альтернативный'),out_of_box:tr('Out of the box','Нестандартный')};
  return <section className="composition-chooser mt-6 border-t pt-5" aria-label={tr('Slide composition options','Варианты композиции слайда')}>
    <h2 className="text-sm font-semibold">{tr('Three ways to present this slide','Три варианта этого слайда')}</h2>
    <p className="mt-1 text-sm text-muted-foreground">{project.build_mode==='model'
      ?tr('AI proposes three arrangements for your content and notes. The selected option is the slide shown above.','AI предлагает три варианта под содержание и заметки. Выбранный вариант показан выше.')
      :tr('Three prepared arrangements, without AI requests. The selected option is the slide shown above.','Три готовых варианта без AI-запросов. Выбранный вариант показан выше.')}</p>
    {(loading||generating)&&<p role="status" className="mt-3 text-sm text-muted-foreground">{generating?tr('Creating three slide variants…','Создаём три варианта слайда…'):tr('Loading slide variants…','Загружаем варианты слайда…')}</p>}
    {slide.variants_status==='error'&&<p role="alert" className="mt-3 text-sm text-destructive">{tr('Variant generation did not finish. Your content is kept. Try again.','Генерация вариантов не завершилась. Содержание сохранено. Повторите попытку.')}</p>}
    {error&&<div className="mt-3 text-sm text-destructive"><p role="alert">{error}</p>{slide.variants_status==='ready'&&<Button variant="outline" size="sm" className="mt-2" disabled={saving} onClick={()=>setRetry(value=>value+1)}>{tr('Reload variants','Загрузить варианты снова')}</Button>}</div>}
    {!generating&&slide.variants_status!=='ready'&&<Button variant="outline" className="mt-3" disabled={disabled||saving} onClick={()=>void generate()}>{saving?tr('Starting…','Запускаем…'):project.build_mode==='model'?tr('Generate three variants with AI','Создать три варианта с AI'):tr('Prepare three variants','Подготовить три варианта')}</Button>}
    <div className="mt-3 grid gap-3 sm:grid-cols-3">{choices.map(choice=>{
      const preview={...project,slides:project.slides.map(row=>row.id===slideId?{...row,design:choice.design,scene:choice.scene}:row)};
      const selected=slide.selected_variant_id===choice.id;
      return <button type="button" key={choice.id} aria-label={tr(`Choose ${labels[choice.id]} variant`,`Выбрать вариант «${labels[choice.id]}»`)} aria-pressed={selected} disabled={disabled||saving||generating} onClick={()=>void select(choice)} className={`min-w-0 cursor-pointer rounded-lg border p-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 ${selected?'border-primary bg-primary/5':'border-border hover:border-primary/60'}`}>
        <div aria-hidden="true"><DraftCanvas project={preview} slideId={slideId} grayscale={!slide.design}/></div>
        <p className="mt-2 text-sm font-medium">{selected && slide.design && slide.design_status === 'ready' ? `${labels[choice.id]} · ${tr("final design","итоговый дизайн")}` : choice.label||labels[choice.id]}</p>
        <p className="mt-1 text-xs text-muted-foreground">{selected?tr('Selected · shown above','Выбран · показан выше'):choice.unconventional?labels.out_of_box:labels[choice.id]}</p>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{choice.description}</p>
      </button>;
    })}</div>
  </section>;
}
