import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {beforeEach, describe, expect, it, vi} from 'vitest';
import LiveDraftEditor from './LiveDraftEditor';
import {LanguageProvider} from '@/context/LanguageContext';
import {LANGUAGE_STORAGE_KEY} from '@/lib/i18n';
import {projectSchema, saveOutline, regenerateWholeSlide, setSlideSourceVisibility, startAIDesign, saveSlideSections, retryAIDesign} from '@/lib/project-api';
import fixture from '../../project-instructions/fixtures/demo-project.json';

vi.mock('./CompositionChooser',()=>({default:()=>null}));
vi.mock('./SpeakerNotesEditor',()=>({default:()=>null}));
vi.mock('@/lib/project-api', async original => ({...await original<typeof import('@/lib/project-api')>(), saveOutline: vi.fn(), regenerateWholeSlide: vi.fn(), setSlideSourceVisibility: vi.fn(), startAIDesign: vi.fn(), retryAIDesign: vi.fn(), saveSlideSections: vi.fn()}));
const makeProject = () => {
  const project = projectSchema.parse(structuredClone(fixture));
  project.phase = 'outline_draft';
  project.build_mode = 'model';
  project.outline[0].layout_type = 'content';
  project.slides = project.outline.map(item => ({id:item.id, status:'ready' as const, revision:1, show_source:true, blocks:{
    title:{text:item.title,status:'ready' as const,revision:1},
    body:{text:item.key_message,status:'ready' as const,revision:1},
    source_label:{text:'Source needed',status:'ready' as const,revision:1},
  }}));
  return project;
};
beforeEach(() => {
  vi.clearAllMocks();
  localStorage.setItem(LANGUAGE_STORAGE_KEY,'en');
  window.matchMedia = vi.fn().mockReturnValue({matches:false});
});
describe('Canvas editing and slide order', () => {
  it('focuses the clicked block and retains unsaved body edits across inspector switches', () => {
    render(<LanguageProvider><LiveDraftEditor project={makeProject()} onChange={vi.fn()}/></LanguageProvider>);
    fireEvent.click(screen.getByRole('button',{name:'Edit slide text'}));
    expect(screen.getByRole('textbox',{name:'Body'})).toHaveFocus();
    fireEvent.change(screen.getByRole('textbox',{name:'Body'}),{target:{value:'My unsaved wording'}});
    fireEvent.click(screen.getByRole('button',{name:'Edit title'}));
    expect(screen.getByRole('textbox',{name:'Title'})).toHaveFocus();
    fireEvent.keyDown(screen.getByRole('button',{name:'Edit source label'}),{key:'Enter'});
    expect(screen.getByRole('textbox',{name:'Source label'})).toHaveFocus();
    fireEvent.click(screen.getByRole('button',{name:'Edit slide text'}));
    expect(screen.getByRole('textbox',{name:'Body'})).toHaveFocus();
    expect(screen.getByRole('textbox',{name:'Body'})).toHaveValue('My unsaved wording');
  });
  it('targets the clicked comparison column with keyboard activation', () => {
    const project = makeProject();
    project.outline[0].layout_type = 'comparison';
    project.slides[0].blocks.body.text = 'First argument | Second argument';
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    fireEvent.keyDown(screen.getByRole('button',{name:'Edit column 2'}),{key:' '});
    expect(screen.getByRole('textbox',{name:'Second point'})).toHaveFocus();
  });
  it('reorders the hovered thumbnail rather than the selected slide, preserving its selection', async () => {
    const project = makeProject();
    const onChange = vi.fn();
    const updated = structuredClone(project);
    [updated.outline[1],updated.outline[2]] = [updated.outline[2],updated.outline[1]];
    updated.outline = updated.outline.map((row,i)=>({...row,order:i+1}));
    vi.mocked(saveOutline).mockResolvedValue(updated);
    const view = render(<LanguageProvider><LiveDraftEditor project={project} onChange={onChange}/></LanguageProvider>);
    expect(screen.getByRole('button',{name:'Move slide 1 up'})).toBeDisabled();
    expect(screen.getByRole('button',{name:'Move slide 5 down'})).toBeDisabled();
    fireEvent.click(screen.getByRole('button',{name:'Move slide 3 up'}));
    await waitFor(()=>expect(onChange).toHaveBeenCalledWith(updated));
    expect(vi.mocked(saveOutline).mock.calls[0][1].map(row=>row.id)).toEqual(updated.outline.map(row=>row.id));
    view.rerender(<LanguageProvider><LiveDraftEditor project={updated} onChange={onChange}/></LanguageProvider>);
    expect(screen.getByRole('button',{name:`Slide 1: ${project.outline[0].title}`})).toHaveAttribute('aria-pressed','true');
  });
  it('requires an instruction and protects unsaved text before whole-slide regeneration', async () => {
    const project = makeProject();
    vi.mocked(regenerateWholeSlide).mockResolvedValue(project);
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    const regenerate = screen.getByRole('button',{name:'Regenerate this slide with AI'});
    expect(regenerate).toBeDisabled();
    fireEvent.change(screen.getByRole('textbox',{name:'What should change on this slide?'}),{target:{value:'Focus on limitations'}});
    expect(regenerate).toBeEnabled();
    fireEvent.change(screen.getByRole('textbox',{name:'Body'}),{target:{value:'Unsaved edit'}});
    expect(regenerate).toBeDisabled();
    fireEvent.click(screen.getByRole('button',{name:'Discard unsaved body'}));
    fireEvent.click(regenerate);
    await waitFor(()=>expect(regenerateWholeSlide).toHaveBeenCalledWith(project,project.outline[0].id,'Focus on limitations'));
  });
  it('hides default footers and changes visibility for only the selected slide', async () => {
    const project = makeProject(); project.slides.forEach(row=>row.show_source=false);
    vi.mocked(setSlideSourceVisibility).mockResolvedValue(project);
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    expect(screen.queryByRole('button',{name:'Edit source label'})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab',{name:'Sources'}));
    fireEvent.click(screen.getByRole('checkbox',{name:'Show source label on this slide'}));
    await waitFor(()=>expect(setSlideSourceVisibility).toHaveBeenCalledWith(project,project.outline[0].id,true));
  });

  it('shows an accessible skeleton until the first outline arrives', () => {
    const project = makeProject(); project.phase='drafting'; project.outline=[]; project.slides=[];
    const view=render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    expect(screen.getByRole('status',{name:'Preparing your slides'})).toHaveAttribute('aria-busy','true');
    expect(screen.queryByText(/No content has arrived/)).not.toBeInTheDocument();
    view.rerender(<LanguageProvider><LiveDraftEditor project={makeProject()} onChange={vi.fn()}/></LanguageProvider>);
    expect(screen.queryByRole('status',{name:'Preparing your slides'})).not.toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Edit title'})).toBeInTheDocument();
  });
  it('keeps approval visible and finishes with the selected theme without collapsing on another click', async () => {
    const project=makeProject(); const finished={...project,phase:'ready' as const,theme:'dark_tech_pitch' as const,slides:project.slides.map(row=>({...row,design_status:'ready' as const,design:{layout:'editorial' as const,emphasis:'quiet' as const,visual:null,rationale:'Clear hierarchy'}}))};
    vi.mocked(startAIDesign).mockResolvedValue(finished);
    const onChange=vi.fn();
    const view=render(<LanguageProvider><LiveDraftEditor project={project} onChange={onChange}/></LanguageProvider>);
    const approve=screen.getByRole('button',{name:'Approve content & choose design'});
    fireEvent.click(approve); fireEvent.click(approve);
    expect(approve).toHaveAttribute('aria-expanded','true');
    fireEvent.click(screen.getByRole('radio',{name:'Dark tech'}));
    fireEvent.click(screen.getByRole('button',{name:'Generate final slides with AI'}));
    await waitFor(()=>expect(onChange).toHaveBeenCalledWith(finished));
    expect(startAIDesign).toHaveBeenCalledWith(project,'dark_tech_pitch');
    view.rerender(<LanguageProvider><LiveDraftEditor project={finished} onChange={onChange}/></LanguageProvider>);
    expect(screen.getByRole('button',{name:'Download PowerPoint'})).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'Generate final slides with AI'})).not.toBeInTheDocument();
  });

  it('keeps a completed design visible while other slides are being designed', () => {
    const project=makeProject(); project.phase='designing';
    Object.assign(project.slides[0],{design_status:'ready',design:{layout:'statement',emphasis:'quiet',visual:null,rationale:'Clear hierarchy'},scene:[{kind:'text',x:7,y:9,w:86,h:15,text:'Accepted title',color:'#111111',size:4,bold:true,font:'Georgia',block_key:'title'}]});
    Object.assign(project.slides[1],{design_status:'generating'});
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    expect(screen.getByText('Designing your slides · 1/5 ready')).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Edit title'})).toHaveTextContent('Accepted title');
    fireEvent.click(screen.getByRole('button',{name:'Edit title'}));
    expect(screen.getByRole('textbox',{name:'Title'})).toHaveFocus();
    expect(screen.queryByRole('button',{name:'Download PowerPoint'})).not.toBeInTheDocument();
  });
  it('retries only the selected failed design and blocks finishing with unsaved text', async () => {
    const project=makeProject(); Object.assign(project.slides[0],{design_status:'error',design_error:'Design unavailable. Retry this slide.'});
    vi.mocked(retryAIDesign).mockResolvedValue(project);
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    fireEvent.click(screen.getByRole('button',{name:'Update this slide’s design'}));
    await waitFor(()=>expect(retryAIDesign).toHaveBeenCalledWith(project,project.slides[0].id));
    fireEvent.change(screen.getByRole('textbox',{name:'Body'}),{target:{value:'Unsaved wording'}});
    fireEvent.click(screen.getByRole('button',{name:`Slide 2: ${project.outline[1].title}`}));
    expect(screen.getByRole('button',{name:'Approve content & choose design'})).toBeDisabled();
  });

  it('edits a clicked semantic section without flattening the other sections',async()=> {
    const project=makeProject(); project.slides[0].sections=[{id:'review',heading:'Staff review',text:'18 minutes per day.'},{id:'maintenance',heading:'Maintenance',text:'Two hours per week.'},{id:'scope',heading:'Scope',text:'A narrow campus sample.'}];
    vi.mocked(saveSlideSections).mockResolvedValue(project);
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    fireEvent.click(screen.getByRole('button',{name:'Edit section 2 text'}));
    const field=screen.getByRole('textbox',{name:'Section text and data 2'});expect(field).toHaveFocus();
    fireEvent.change(field,{target:{value:'Three hours per week.'}});
    fireEvent.click(screen.getByRole('button',{name:'Save sections'}));
    await waitFor(()=>expect(saveSlideSections).toHaveBeenCalled());
    expect(vi.mocked(saveSlideSections).mock.calls[0][2]).toEqual([{id:'review',heading:'Staff review',text:'18 minutes per day.'},{id:'maintenance',heading:'Maintenance',text:'Three hours per week.'},{id:'scope',heading:'Scope',text:'A narrow campus sample.'}]);
  });

  it('keeps critic findings private and shows only improvement progress',()=> {
    const project=makeProject();project.phase='designing';
    Object.assign(project.slides[0],{design_status:'generating',design_stage:'refining',quality_issues:['Internal typography critique: too small']});
    render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    expect(screen.getByText('Improving slide design…')).toBeInTheDocument();
    expect(screen.queryByText('Internal typography critique: too small')).not.toBeInTheDocument();
  });

  it('shows thumbnail activity while AI works and removes it when complete',()=> {
    const project=makeProject();project.phase='designing';project.slides[0].design_status='generating';
    const view=render(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    const thumbnail=screen.getByRole('button',{name:`Slide 1: ${project.outline[0].title}`});
    expect(thumbnail).toHaveAttribute('aria-busy','true');expect(thumbnail).toHaveTextContent('Designing…');expect(thumbnail.querySelector('.draft-thumbnail-shimmer')).not.toBeNull();
    project.slides[0].design_status='ready';project.phase='ready';
    view.rerender(<LanguageProvider><LiveDraftEditor project={project} onChange={vi.fn()}/></LanguageProvider>);
    expect(thumbnail).toHaveAttribute('aria-busy','false');expect(thumbnail.querySelector('.draft-thumbnail-shimmer')).toBeNull();
  });

});
