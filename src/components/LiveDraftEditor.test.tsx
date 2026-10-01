import {render, screen, fireEvent, waitFor} from '@testing-library/react';
import {beforeEach, describe, expect, it, vi} from 'vitest';
import LiveDraftEditor from './LiveDraftEditor';
import {LanguageProvider} from '@/context/LanguageContext';
import {LANGUAGE_STORAGE_KEY} from '@/lib/i18n';
import {projectSchema, saveOutline} from '@/lib/project-api';
import fixture from '../../project-instructions/fixtures/demo-project.json';

vi.mock('@/lib/project-api', async original => ({...await original<typeof import('@/lib/project-api')>(), saveOutline: vi.fn()}));
const makeProject = () => {
  const project = projectSchema.parse(structuredClone(fixture));
  project.phase = 'outline_draft';
  project.outline[0].layout_type = 'content';
  project.slides = project.outline.map(item => ({id:item.id, status:'ready' as const, revision:1, blocks:{
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
});
