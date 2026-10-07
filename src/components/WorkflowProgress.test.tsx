import {render, screen, cleanup} from '@testing-library/react';
import {afterEach, describe, expect, it} from 'vitest';
import {LanguageProvider} from '@/context/LanguageContext';
import {LANGUAGE_STORAGE_KEY} from '@/lib/i18n';
import {projectSchema} from '@/lib/project-api';
import fixture from '../../project-instructions/fixtures/demo-project.json';
import WorkflowProgress from './WorkflowProgress';

afterEach(cleanup);
function show(stage:'design_planning'|'checking'|'budget_exhausted') {
  localStorage.setItem(LANGUAGE_STORAGE_KEY,'en');
  const project=projectSchema.parse(structuredClone(fixture));
  project.build_mode='model';project.phase=stage==='budget_exhausted'?'outline_draft':'designing';
  project.workflow={stage,model_calls:7,request_budget:40,input_tokens:1000,output_tokens:300,actions:[{sequence:1,action:'review_slide',slide_id:project.outline[0].id,status:stage==='budget_exhausted'?'error':'running',detail:'INTERNAL PRIVATE CRITIC DETAILS'}]};
  return render(<LanguageProvider><WorkflowProgress project={project}/></LanguageProvider>);
}
describe('Observed generation progress',()=>{
  it('reports actual zero calls for a prepared draft without an AI label',()=>{
    const project=projectSchema.parse(structuredClone(fixture));project.build_mode='template';
    project.workflow={stage:'review',model_calls:0,request_budget:40,input_tokens:0,output_tokens:0,actions:[]};
    render(<LanguageProvider><WorkflowProgress project={project}/></LanguageProvider>);
    expect(screen.getByText('Model requests: 0 / 40')).toBeInTheDocument();
    expect(screen.queryByText(/AI requests/)).not.toBeInTheDocument();
  });
  it('keeps an initial failure at Plan without claiming content exists',()=>{
    const project=projectSchema.parse(structuredClone(fixture));project.phase='error';project.outline=[];
    project.workflow={stage:'error',model_calls:1,request_budget:40,input_tokens:0,output_tokens:0,actions:[]};
    render(<LanguageProvider><WorkflowProgress project={project}/></LanguageProvider>);
    expect(screen.getByText('Plan').closest('li')).toHaveAttribute('aria-current','step');
  });
  it.each(['outline_draft','ready'] as const)('returns invalidated %s content to review',phase=>{
    localStorage.setItem(LANGUAGE_STORAGE_KEY,'en');
    const project=projectSchema.parse(structuredClone(fixture));project.phase=phase;
    project.workflow={stage:'complete',model_calls:12,request_budget:40,input_tokens:0,output_tokens:0,actions:[]};
    project.slides=project.outline.map(item=>({id:item.id,status:'ready',revision:1,design_status:'none',design:null,blocks:{title:{text:item.title,status:'ready',revision:1},body:{text:item.key_message,status:'ready',revision:1},source_label:{text:'',status:'ready',revision:1}}}));
    render(<LanguageProvider><WorkflowProgress project={project}/></LanguageProvider>);
    expect(screen.getByText('Review').closest('li')).toHaveAttribute('aria-current','step');
    expect(screen.getByText('Ready').closest('li')).not.toHaveAttribute('aria-current');
  });
  it.each([['generate_variants','Creating three slide variants'],['check_slide_notes','Checking slide and notes consistency']])('names observed %s work clearly',(action,label)=>{
    localStorage.setItem(LANGUAGE_STORAGE_KEY,'en');const project=projectSchema.parse(structuredClone(fixture));project.phase='designing';project.build_mode='model';
    project.workflow={stage:'design_planning',model_calls:7,request_budget:40,input_tokens:0,output_tokens:0,actions:[{sequence:1,action,status:'running',slide_id:project.outline[0].id,detail:''}]};
    render(<LanguageProvider><WorkflowProgress project={project}/></LanguageProvider>);expect(screen.getByRole('status')).toHaveTextContent(label+' · slide 1');
  });
  it('shows whole-deck planning before individual slide work',()=>{
    show('design_planning');
    expect(screen.getByRole('status')).toHaveTextContent('Planning the visual direction for the whole presentation');
    expect(screen.getByText('Design & check').closest('li')).toHaveAttribute('aria-current','step');
    expect(screen.queryByText('INTERNAL PRIVATE CRITIC DETAILS')).not.toBeInTheDocument();
  });
  it('reports the recorded check and request count without invented percentage',()=>{
    show('checking');
    expect(screen.getByRole('status')).toHaveTextContent('Checking the rendered slide · slide 1');
    expect(screen.getByText('AI requests: 7 / 40')).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
  it('explains a stopped budget while retaining the saved presentation',()=>{
    show('budget_exhausted');
    expect(screen.getByRole('alert')).toHaveTextContent('Completed content is saved');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
