import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {Link,MemoryRouter,Route,Routes} from 'react-router-dom';
import ProjectPage from './ProjectPage';
import {getProject,projectSchema,type Project} from '@/lib/project-api';
import fixture from '../../project-instructions/fixtures/demo-project.json';
vi.mock('@/lib/project-api',async original=>({...await original<typeof import('@/lib/project-api')>(),getProject:vi.fn()}));
vi.mock('@/components/AppHeader',()=>({default:()=>null}));
vi.mock('@/components/LiveDraftEditor',()=>({default:({project}:{project:Project})=><h1>Editor {project.id}</h1>}));
function deferred<T>(){let resolve!:(value:T)=>void;let reject!:(error:Error)=>void;const promise=new Promise<T>((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject};}
function makeProject(id:string,phase:Project['phase']='drafting'){const p=projectSchema.parse(structuredClone(fixture));p.id=id;p.phase=phase;p.revision=id==='a'?100:1;return p;}
function show(){return render(<MemoryRouter initialEntries={['/projects/a']}><Link to="/projects/b">Open B</Link><Routes><Route path="/projects/:projectId" element={<ProjectPage/>}/></Routes></MemoryRouter>);}
beforeEach(()=>vi.clearAllMocks());
afterEach(()=>{cleanup();vi.useRealTimers();});
describe('Project response isolation',()=>{
 it('ignores a late initial response after opening another project',async()=>{const a=deferred<Project>();vi.mocked(getProject).mockImplementation(id=>id==='a'?a.promise:Promise.resolve(makeProject('b')));show();fireEvent.click(screen.getByRole('link',{name:'Open B'}));await screen.findByRole('heading',{name:'Editor b'});await act(async()=>a.resolve(makeProject('a')));expect(screen.getByRole('heading',{name:'Editor b'})).toBeInTheDocument();expect(screen.queryByText('Editor a')).not.toBeInTheDocument();});
 it('ignores an in-flight poll from the previous project even when its revision is higher',async()=>{vi.useFakeTimers();const poll=deferred<Project>();let readsA=0;vi.mocked(getProject).mockImplementation(id=>id==='a'?(++readsA===1?Promise.resolve(makeProject('a')):poll.promise):Promise.resolve(makeProject('b')));show();await act(async()=>{});expect(screen.getByRole('heading',{name:'Editor a'})).toBeInTheDocument();await act(async()=>vi.advanceTimersByTime(300));expect(readsA).toBe(2);fireEvent.click(screen.getByRole('link',{name:'Open B'}));await act(async()=>{});expect(screen.getByRole('heading',{name:'Editor b'})).toBeInTheDocument();await act(async()=>poll.resolve(makeProject('a')));expect(screen.getByRole('heading',{name:'Editor b'})).toBeInTheDocument();});
 it('ignores a previous project load error after navigation',async()=>{const a=deferred<Project>();vi.mocked(getProject).mockImplementation(id=>id==='a'?a.promise:Promise.resolve(makeProject('b')));show();fireEvent.click(screen.getByRole('link',{name:'Open B'}));await screen.findByRole('heading',{name:'Editor b'});await act(async()=>a.reject(new Error('Old project failed')));expect(screen.queryByRole('alert')).not.toBeInTheDocument();});
});
