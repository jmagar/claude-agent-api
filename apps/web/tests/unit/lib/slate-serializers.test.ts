import { markdownToSlate, slateToMarkdown, preserveYamlFrontmatter, type SlateValue } from '@/lib/slate-serializers';

describe('Slate Serializers', () => {
  describe('markdownToSlate', () => {
    it('converts plain text to Slate', () => {
      const result = markdownToSlate('Hello world');
      expect(result).toEqual([
        { type: 'p', children: [{ text: 'Hello world' }] }
      ]);
    });

    it('converts headings', () => {
      const result = markdownToSlate('# H1\n## H2\n### H3');
      expect(result).toEqual([
        { type: 'h1', children: [{ text: 'H1' }] },
        { type: 'h2', children: [{ text: 'H2' }] },
        { type: 'h3', children: [{ text: 'H3' }] }
      ]);
    });

    it('converts bold and italic', () => {
      const result = markdownToSlate('**bold** and *italic*');
      expect(result).toEqual([
        {
          type: 'p',
          children: [
            { text: 'bold', bold: true },
            { text: ' and ' },
            { text: 'italic', italic: true }
          ]
        }
      ]);
    });

    it('converts code blocks with language', () => {
      const result = markdownToSlate('```typescript\nconst x = 1;\n```');
      expect(result).toEqual([
        {
          type: 'code_block',
          lang: 'typescript',
          children: [{ text: 'const x = 1;' }]
        }
      ]);
    });

    it('converts lists (unordered)', () => {
      const result = markdownToSlate('- Item 1\n- Item 2');
      expect(result).toEqual([
        {
          type: 'ul',
          children: [
            { type: 'lic', children: [{ text: 'Item 1' }] },
            { type: 'lic', children: [{ text: 'Item 2' }] }
          ]
        }
      ]);
    });

    it('converts lists (ordered)', () => {
      const result = markdownToSlate('1. First\n2. Second');
      expect(result).toEqual([
        {
          type: 'ol',
          children: [
            { type: 'lic', children: [{ text: 'First' }] },
            { type: 'lic', children: [{ text: 'Second' }] }
          ]
        }
      ]);
    });

    it('converts blockquotes', () => {
      const result = markdownToSlate('> Quote text');
      expect(result).toEqual([
        {
          type: 'blockquote',
          children: [{ type: 'p', children: [{ text: 'Quote text' }] }]
        }
      ]);
    });

    it('converts links', () => {
      const result = markdownToSlate('[Link](https://example.com)');
      expect(result).toEqual([
        {
          type: 'p',
          children: [
            {
              type: 'a',
              url: 'https://example.com',
              children: [{ text: 'Link' }]
            }
          ]
        }
      ]);
    });

    it('converts inline code', () => {
      const result = markdownToSlate('Text with `code` inline');
      expect(result).toEqual([
        {
          type: 'p',
          children: [
            { text: 'Text with ' },
            { text: 'code', code: true },
            { text: ' inline' }
          ]
        }
      ]);
    });

    it('handles empty input', () => {
      const result = markdownToSlate('');
      expect(result).toEqual([
        { type: 'p', children: [{ text: '' }] }
      ]);
    });

    it('preserves multiple paragraphs', () => {
      const result = markdownToSlate('Para 1\n\nPara 2');
      expect(result).toEqual([
        { type: 'p', children: [{ text: 'Para 1' }] },
        { type: 'p', children: [{ text: 'Para 2' }] }
      ]);
    });
  });

  describe('slateToMarkdown', () => {
    it('converts plain text', () => {
      const value: SlateValue = [{ type: 'p', children: [{ text: 'Hello' }] }];
      expect(slateToMarkdown(value)).toBe('Hello\n');
    });

    it('converts headings', () => {
      const value: SlateValue = [
        { type: 'h1', children: [{ text: 'H1' }] },
        { type: 'h2', children: [{ text: 'H2' }] }
      ];
      expect(slateToMarkdown(value)).toBe('# H1\n\n## H2\n');
    });

    it('converts bold and italic', () => {
      const value: SlateValue = [
        {
          type: 'p',
          children: [
            { text: 'bold', bold: true },
            { text: ' and ' },
            { text: 'italic', italic: true }
          ]
        }
      ];
      expect(slateToMarkdown(value)).toBe('**bold** and *italic*\n');
    });

    it('converts code blocks', () => {
      const value: SlateValue = [
        {
          type: 'code_block',
          lang: 'typescript',
          children: [{ text: 'const x = 1;' }]
        }
      ];
      expect(slateToMarkdown(value)).toBe('```typescript\nconst x = 1;\n```\n');
    });

    it('round-trips correctly', () => {
      const original = '# Title\n\n**Bold** text\n\n- Item 1\n- Item 2';
      const slate = markdownToSlate(original);
      const result = slateToMarkdown(slate);
      expect(result.trim()).toBe(original.trim());
    });
  });

  describe('preserveYamlFrontmatter', () => {
    it('extracts frontmatter and body', () => {
      const content = '---\nname: test\n---\n# Content';
      const { frontmatter, body } = preserveYamlFrontmatter(content);

      expect(frontmatter).toEqual({ name: 'test' });
      expect(body).toBe('# Content');
    });

    it('handles content without frontmatter', () => {
      const content = '# No frontmatter';
      const { frontmatter, body } = preserveYamlFrontmatter(content);

      expect(frontmatter).toEqual({});
      expect(body).toBe('# No frontmatter');
    });

    it('preserves complex YAML', () => {
      const content = '---\nname: test\ntools:\n  - Read\n  - Write\n---\nContent';
      const { frontmatter } = preserveYamlFrontmatter(content);

      expect(frontmatter).toEqual({
        name: 'test',
        tools: ['Read', 'Write']
      });
    });
  });
});
