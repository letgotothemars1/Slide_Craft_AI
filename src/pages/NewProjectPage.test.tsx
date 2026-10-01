import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {MemoryRouter, Route, Routes} from 'react-router-dom';
import NewProjectPage from './NewProjectPage';
import {LANGUAGE_STORAGE_KEY} from '@/lib/i18n';
import {LanguageProvider} from '@/context/LanguageContext';
import {intakeStorageKey} from '@/lib/intake-draft';
import {createProject, getProject, startLiveDraft, projectSchema} from '@/lib/project-api';
import fixture from '../../project-instructions/fixtures/demo-project.json';

vi.mock('@/components/AppHeader',()=>({default:()=> <header>SlideCraft</header>}));
vi.mock('@/lib/project-api',async importOriginal=>({...await importOriginal<typeof import('@/lib/project-api')>(),createProject:vi.fn(),getProject:vi.fn(),startLiveDraft:vi.fn()}));
const savedInputs={assignment:'Five slides about a synthetic pilot',contextPack:'Thesis: promising, not proven',theme:'dark_tech_pitch',sourceId:'uploaded-pdf',filename:'synthetic.pdf'};
function showForm(){return render(<LanguageProvider><MemoryRouter initialEntries={['/projects/new']}><Routes><Route path="/projects/new" element={<NewProjectPage/>}/><Route path="/projects/:id" element={<h1>Draft editor opened</h1>}/></Routes></MemoryRouter></LanguageProvider>);}
beforeEach(()=> {
  vi.clearAllMocks(); localStorage.clear(); localStorage.setItem(LANGUAGE_STORAGE_KEY,'en');
  const p=projectSchema.parse(fixture);p.id='created';p.phase='intake';p.outline=[];p.slides=[];
  vi.mocked(createProject).mockResolvedValue(p);vi.mocked(getProject).mockResolvedValue(p);
  vi.mocked(startLiveDraft).mockResolvedValue({...p,phase:'drafting'});
});
afterEach(()=>{cleanup();vi.restoreAllMocks();});

describe('Persistent intake and direct generation',()=> {
  it('restores edited text, theme and uploaded PDF reference after remount',async()=> {
    localStorage.setItem(intakeStorageKey,JSON.stringify({...savedInputs,assignment:'',contextPack:'',theme:'clean_editorial'}));
    const view=showForm();
    fireEvent.change(screen.getByRole('textbox',{name:'Assignment brief'}),{target:{value:savedInputs.assignment}});
    fireEvent.change(screen.getByRole('textbox',{name:'Context Pack'}),{target:{value:savedInputs.contextPack}});
    fireEvent.click(screen.getByRole('radio',{name:'Dark tech'}));
    await waitFor(()=>expect(JSON.parse(localStorage.getItem(intakeStorageKey)!)).toEqual(savedInputs));
    view.unmount();showForm();
    expect(screen.getByRole('textbox',{name:'Assignment brief'})).toHaveValue(savedInputs.assignment);
    expect(screen.getByRole('textbox',{name:'Context Pack'})).toHaveValue(savedInputs.contextPack);
    expect(screen.getByRole('radio',{name:'Dark tech'})).toBeChecked();
    expect(screen.getByText(/synthetic.pdf/)).toBeInTheDocument();
  });
  it('starts the selected key-free method on the intake form before opening the editor',async()=> {
    localStorage.setItem(intakeStorageKey,JSON.stringify(savedInputs));showForm();
    expect(screen.queryByRole('button',{name:'Save project'})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Generate without API'}));
    await screen.findByRole('heading',{name:'Draft editor opened'});
    expect(createProject).toHaveBeenCalledWith(expect.objectContaining({assignment_text:savedInputs.assignment,source_document_id:'uploaded-pdf',theme:'dark_tech_pitch'}));
    expect(startLiveDraft).toHaveBeenCalledWith(expect.objectContaining({id:'created'}),'template');
    expect(JSON.parse(localStorage.getItem(intakeStorageKey)!)).toEqual(savedInputs);
  });
  it('keeps the form on a start error and reuses the created project for an alternate method',async()=> {
    localStorage.setItem(intakeStorageKey,JSON.stringify(savedInputs));
    vi.mocked(startLiveDraft).mockRejectedValueOnce(new Error('AI provider is not configured'));
    showForm();fireEvent.click(screen.getByRole('button',{name:'Generate with AI'}));
    await screen.findByRole('alert');
    expect(screen.getByRole('textbox',{name:'Assignment brief'})).toHaveValue(savedInputs.assignment);
    await waitFor(()=>expect(screen.getByRole('button',{name:'Generate without API'})).toBeEnabled());
    fireEvent.click(screen.getByRole('button',{name:'Generate without API'}));
    await screen.findByRole('heading',{name:'Draft editor opened'});
    expect(createProject).toHaveBeenCalledTimes(1);
    expect(startLiveDraft).toHaveBeenNthCalledWith(1,expect.anything(),'model');
    expect(startLiveDraft).toHaveBeenNthCalledWith(2,expect.anything(),'template');
  });
  it('opens an empty form when saved browser data is malformed',()=> {
    localStorage.setItem(intakeStorageKey,'{broken');showForm();
    expect(screen.getByRole('textbox',{name:'Assignment brief'})).toHaveValue('');
    expect(screen.getByRole('radio',{name:'Clean editorial'})).toBeChecked();
  });
  it('starts a blank project and keeps it blank after refresh',async()=> {
    localStorage.setItem(intakeStorageKey,JSON.stringify(savedInputs));
    const view=showForm();
    fireEvent.click(screen.getByRole('button',{name:'Start from scratch'}));
    expect(screen.getByRole('textbox',{name:'Assignment brief'})).toHaveValue('');
    expect(screen.getByRole('textbox',{name:'Context Pack'})).toHaveValue('');
    expect(screen.getByRole('radio',{name:'Clean editorial'})).toBeChecked();
    expect(screen.queryByText(/synthetic.pdf/)).not.toBeInTheDocument();
    await waitFor(()=>expect(JSON.parse(localStorage.getItem(intakeStorageKey)!)).toEqual({assignment:'',contextPack:'',theme:'clean_editorial',sourceId:null,filename:null}));
    view.unmount();showForm();
    expect(screen.getByRole('textbox',{name:'Assignment brief'})).toHaveValue('');
    expect(screen.queryByText(/synthetic.pdf/)).not.toBeInTheDocument();
  });

});
