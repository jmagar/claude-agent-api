/**
 * Tests for PlateYamlEditor component
 *
 * Verifies YAML-aware editor with dual-mode editing (Visual/YAML)
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlateYamlEditor } from '@/components/plate/PlateYamlEditor';

// Mock the PlateEditor component
jest.mock('@/components/plate/PlateEditor', () => ({
  PlateEditor: ({ value, onChange, placeholder, ariaLabel }: {
    value: Array<{ type: string; children: Array<{ text: string }> }>;
    onChange: (value: Array<{ type: string; children: Array<{ text: string }> }>) => void;
    placeholder?: string;
    ariaLabel?: string;
  }) => (
    <div
      data-testid="plate-editor"
      aria-label={ariaLabel}
      data-placeholder={placeholder}
    >
      <textarea
        data-testid="plate-editor-textarea"
        value={JSON.stringify(value)}
        onChange={(e) => {
          try {
            const parsed = JSON.parse(e.target.value);
            onChange(parsed);
          } catch {
            // Ignore invalid JSON
          }
        }}
      />
    </div>
  ),
}));

describe('PlateYamlEditor', () => {
  it('should render in Visual mode by default', () => {
    const content = `---
name: test-agent
description: Test description
---
This is the content body.`;

    render(<PlateYamlEditor value={content} onChange={jest.fn()} />);

    expect(screen.getByRole('tab', { name: /visual/i, selected: true })).toBeInTheDocument();
    expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
  });

  it('should toggle to YAML view when YAML tab is clicked', async () => {
    const user = userEvent.setup();
    const content = `---
name: test-agent
---
Content`;

    render(<PlateYamlEditor value={content} onChange={jest.fn()} />);

    const yamlTab = screen.getByRole('tab', { name: /yaml/i });
    await user.click(yamlTab);

    expect(yamlTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('textbox', { name: /yaml editor/i })).toBeInTheDocument();
    expect(screen.queryByTestId('plate-editor')).not.toBeInTheDocument();
  });

  it('should parse and display content in YAML view', async () => {
    const user = userEvent.setup();
    const content = `---
name: test-agent
description: Test description
model: sonnet
---
This is the body content.`;

    render(<PlateYamlEditor value={content} onChange={jest.fn()} />);

    const yamlTab = screen.getByRole('tab', { name: /yaml/i });
    await user.click(yamlTab);

    const yamlTextarea = screen.getByRole('textbox', { name: /yaml editor/i }) as HTMLTextAreaElement;
    expect(yamlTextarea.value).toContain('name: test-agent');
    expect(yamlTextarea.value).toContain('description: Test description');
    expect(yamlTextarea.value).toContain('This is the body content.');
  });

  it('should sync changes from YAML view to parent', async () => {
    const onChange = jest.fn();
    const content = `---
name: original
---
Original content`;

    render(<PlateYamlEditor value={content} onChange={onChange} />);

    const yamlTab = screen.getByRole('tab', { name: /yaml/i });
    await userEvent.click(yamlTab);

    const yamlTextarea = screen.getByRole('textbox', { name: /yaml editor/i }) as HTMLTextAreaElement;

    // Use fireEvent for complex input instead of userEvent
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(yamlTextarea, {
      target: { value: '---\nname: updated\n---\nUpdated content' }
    });

    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('name: updated')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('Updated content')
    );
  });

  it('should display validation errors for invalid YAML', async () => {
    const user = userEvent.setup();
    const content = `---
name: test
---
Content`;

    render(
      <PlateYamlEditor
        value={content}
        onChange={jest.fn()}
        validateYaml={true}
        requiredFields={['name', 'description']}
      />
    );

    const yamlTab = screen.getByRole('tab', { name: /yaml/i });
    await user.click(yamlTab);

    // Missing required field 'description'
    expect(screen.getByRole('alert')).toHaveTextContent(/required field.*description/i);
  });

  it('should pass custom placeholder to PlateEditor', () => {
    const content = `---
name: test
---
`;

    render(
      <PlateYamlEditor
        value={content}
        onChange={jest.fn()}
        placeholder="Custom placeholder"
      />
    );

    const editor = screen.getByTestId('plate-editor');
    expect(editor).toHaveAttribute('data-placeholder', 'Custom placeholder');
  });

  it('should use custom aria-label', () => {
    const content = `---
name: test
---
Content`;

    const { container } = render(
      <PlateYamlEditor
        value={content}
        onChange={jest.fn()}
        ariaLabel="Agent prompt editor"
      />
    );

    // Check the top-level container has the aria-label
    const editor = container.querySelector('[aria-label="Agent prompt editor"]');
    expect(editor).toBeInTheDocument();
  });

  it('should handle content without frontmatter', () => {
    const content = 'Just plain content';

    render(<PlateYamlEditor value={content} onChange={jest.fn()} />);

    expect(screen.getByRole('tab', { name: /visual/i })).toBeInTheDocument();
    expect(screen.getByTestId('plate-editor')).toBeInTheDocument();
  });

  it('should sync changes from Visual mode to parent', async () => {
    const onChange = jest.fn();
    const content = `---
name: test
---
Original body`;

    render(<PlateYamlEditor value={content} onChange={onChange} />);

    // Simulate PlateEditor change by updating the mocked textarea
    const slateTextarea = screen.getByTestId('plate-editor-textarea') as HTMLTextAreaElement;
    const newSlateValue = [{ type: 'paragraph', children: [{ text: 'Updated body' }] }];

    // Use fireEvent for complex input
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(slateTextarea, {
      target: { value: JSON.stringify(newSlateValue) }
    });

    expect(onChange).toHaveBeenCalled();
  });

  it('should preserve frontmatter when editing body in Visual mode', async () => {
    const onChange = jest.fn();
    const content = `---
name: test-agent
description: Test description
model: sonnet
---
Original body content`;

    render(<PlateYamlEditor value={content} onChange={onChange} />);

    // Simulate body change in Visual mode
    const slateTextarea = screen.getByTestId('plate-editor-textarea') as HTMLTextAreaElement;
    const newSlateValue = [{ type: 'paragraph', children: [{ text: 'New body' }] }];

    // Use fireEvent for complex input
    const { fireEvent } = await import('@testing-library/react');
    fireEvent.change(slateTextarea, {
      target: { value: JSON.stringify(newSlateValue) }
    });

    // Verify onChange was called with frontmatter preserved
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('name: test-agent')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('description: Test description')
    );
  });

  it('should support tab navigation between Visual and YAML modes', async () => {
    const user = userEvent.setup();
    const content = `---
name: test
---
Content`;

    render(<PlateYamlEditor value={content} onChange={jest.fn()} />);

    const visualTab = screen.getByRole('tab', { name: /visual/i });
    const yamlTab = screen.getByRole('tab', { name: /yaml/i });

    // Initially in Visual mode
    expect(visualTab).toHaveAttribute('aria-selected', 'true');

    // Switch to YAML
    await user.click(yamlTab);
    expect(yamlTab).toHaveAttribute('aria-selected', 'true');
    expect(visualTab).toHaveAttribute('aria-selected', 'false');

    // Switch back to Visual
    await user.click(visualTab);
    expect(visualTab).toHaveAttribute('aria-selected', 'true');
    expect(yamlTab).toHaveAttribute('aria-selected', 'false');
  });
});
