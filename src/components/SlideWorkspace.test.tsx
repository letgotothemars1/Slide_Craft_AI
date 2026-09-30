import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SlideWorkspace from './SlideWorkspace';
import fixture from '../../project-instructions/fixtures/demo-project.json';
import { projectSchema, regenerateBlock, editSlideBlock, getProject } from '@/lib/project-api';

vi.mock('@/lib/project-api', async (importOriginal) => ({
  ...await importOriginal<typeof import('@/lib/project-api')>(),
  regenerateBlock: vi.fn(), editSlideBlock: vi.fn(), getProject: vi.fn(),
}));

const readyProject = () => {
  const project = projectSchema.parse(structuredClone(fixture));
  project.phase = 'ready';
  project.slides = project.outline.map((item) => ({id: item.id, status: 'ready', revision: 1, blocks: {
    title: {text: item.title, status: 'ready', revision: 1},
    body: {text: item.key_message, status: 'ready', revision: 1},
    source_label: {text: 'Source needed', status: 'ready', revision: 1},
  }}));
  return project;
};

beforeEach(() => vi.clearAllMocks());

describe('Local block editor', () => {
  it('preserves an unsaved body through title regeneration and locks only the title', async () => {
    const project = readyProject();
    const onChange = vi.fn();
    const view = render(<SlideWorkspace project={project} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox', {name: 'Body'}), {target: {value: 'My unsaved body'}});
    const started = structuredClone(project);
    started.revision++;
    started.slides[0].blocks.title.status = 'generating';
    vi.mocked(regenerateBlock).mockResolvedValue(started);
    fireEvent.click(screen.getByRole('button', {name: 'Regenerate title with AI'}));
    await waitFor(() => expect(onChange).toHaveBeenCalledWith(started));
    view.rerender(<SlideWorkspace project={started} onChange={onChange} />);
    expect(screen.getByRole('textbox', {name: 'Title'})).toBeDisabled();
    expect(screen.getByRole('textbox', {name: 'Body'})).toBeEnabled();
    expect(screen.getByRole('textbox', {name: 'Body'})).toHaveValue('My unsaved body');
    const finished = structuredClone(started);
    finished.slides[0].blocks.title.status = 'ready';
    finished.slides[0].blocks.title.text = 'New model title';
    finished.slides[0].revision++;
    view.rerender(<SlideWorkspace project={finished} onChange={onChange} />);
    await waitFor(() => expect(screen.getByRole('textbox', {name: 'Title'})).toHaveValue('New model title'));
    expect(screen.getByRole('textbox', {name: 'Body'})).toHaveValue('My unsaved body');
  });

  it('retains a draft after a revision conflict and refreshes the saved project', async () => {
    const project = readyProject();
    const onChange = vi.fn();
    render(<SlideWorkspace project={project} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox', {name: 'Body'}), {target: {value: 'Keep this draft'}});
    vi.mocked(editSlideBlock).mockRejectedValue(new Error('Project changed. Refresh before saving again.'));
    vi.mocked(getProject).mockResolvedValue(project);
    fireEvent.click(screen.getByRole('button', {name: 'Save body'}));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    expect(screen.getByRole('textbox', {name: 'Body'})).toHaveValue('Keep this draft');
    expect(screen.getByRole('alert')).toHaveTextContent('Refresh');
  });
});
