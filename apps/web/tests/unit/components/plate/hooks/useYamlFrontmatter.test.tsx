/**
 * Tests for useYamlFrontmatter hook
 *
 * Verifies YAML frontmatter parsing, state management, and serialization
 */

import { renderHook, act } from '@testing-library/react';
import { useYamlFrontmatter } from '@/components/plate/hooks/useYamlFrontmatter';

describe('useYamlFrontmatter', () => {
  it('should parse frontmatter on mount', () => {
    const content = `---
name: test-agent
description: Test description
model: sonnet
---
This is the content body.`;

    const { result } = renderHook(() =>
      useYamlFrontmatter(content, jest.fn())
    );

    expect(result.current.frontmatter).toEqual({
      name: 'test-agent',
      description: 'Test description',
      model: 'sonnet',
    });
    expect(result.current.body).toBe('This is the content body.');
  });

  it('should handle content without frontmatter', () => {
    const content = 'Plain content without frontmatter';

    const { result } = renderHook(() =>
      useYamlFrontmatter(content, jest.fn())
    );

    expect(result.current.frontmatter).toEqual({});
    expect(result.current.body).toBe(content);
  });

  it('should update frontmatter and serialize back to markdown', () => {
    const content = `---
name: test-agent
---
Body content`;

    const onChange = jest.fn();
    const { result } = renderHook(() => useYamlFrontmatter(content, onChange));

    act(() => {
      result.current.updateFrontmatter({ name: 'updated-agent', model: 'opus' });
    });

    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('name: updated-agent')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('model: opus')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('Body content')
    );
  });

  it('should update body and serialize back to markdown', () => {
    const content = `---
name: test-agent
---
Original body`;

    const onChange = jest.fn();
    const { result } = renderHook(() => useYamlFrontmatter(content, onChange));

    act(() => {
      result.current.updateBody('Updated body content');
    });

    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('name: test-agent')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('Updated body content')
    );
  });

  it('should merge frontmatter updates with existing data', () => {
    const content = `---
name: test-agent
description: Test description
---
Body`;

    const onChange = jest.fn();
    const { result } = renderHook(() => useYamlFrontmatter(content, onChange));

    act(() => {
      result.current.updateFrontmatter({ model: 'haiku' });
    });

    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('name: test-agent')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('description: Test description')
    );
    expect(onChange).toHaveBeenCalledWith(
      expect.stringContaining('model: haiku')
    );
  });

  it('should handle empty frontmatter', () => {
    const content = `---
---
Just body content`;

    const { result } = renderHook(() =>
      useYamlFrontmatter(content, jest.fn())
    );

    expect(result.current.frontmatter).toEqual({});
    expect(result.current.body).toBe('Just body content');
  });

  it('should re-parse when content changes externally', () => {
    const onChange = jest.fn();
    const { result, rerender } = renderHook(
      ({ content }) => useYamlFrontmatter(content, onChange),
      {
        initialProps: {
          content: `---
name: original
---
Original body`,
        },
      }
    );

    expect(result.current.frontmatter).toEqual({ name: 'original' });

    rerender({
      content: `---
name: updated
---
Updated body`,
    });

    expect(result.current.frontmatter).toEqual({ name: 'updated' });
    expect(result.current.body).toBe('Updated body');
  });

  it('should use serializeYamlFrontmatter from yaml-validation.ts', () => {
    const content = `---
name: test
---
Content`;

    const onChange = jest.fn();
    const { result } = renderHook(() => useYamlFrontmatter(content, onChange));

    act(() => {
      result.current.updateFrontmatter({ description: 'New desc' });
    });

    // serializeYamlFrontmatter sorts keys alphabetically
    const call = onChange.mock.calls[0][0] as string;
    expect(call).toMatch(/---\n[\s\S]*---\n/);
    expect(call.indexOf('description:')).toBeLessThan(call.indexOf('name:'));
  });
});
