/**
 * Slate Serializers
 *
 * Convert between Markdown and Slate JSON for PlateJS editor.
 * Preserves YAML frontmatter during conversions.
 */

import { parseYamlFrontmatter, extractContent } from './yaml-validation';

// Slate node types
type Text = { text: string; bold?: boolean; italic?: boolean; code?: boolean };
type Paragraph = { type: 'p'; children: (Text | Link)[] };
type Heading = { type: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'; children: Text[] };
type CodeBlock = { type: 'code_block'; lang?: string; children: Text[] };
type List = { type: 'ul' | 'ol'; children: ListItem[] };
type ListItem = { type: 'lic'; children: (Text | Paragraph)[] };
type Blockquote = { type: 'blockquote'; children: Paragraph[] };
type Link = { type: 'a'; url: string; children: Text[] };
type SlateNode = Paragraph | Heading | CodeBlock | List | Blockquote;
export type SlateValue = SlateNode[];

/**
 * Convert markdown string to Slate JSON
 */
export function markdownToSlate(markdown: string): SlateValue {
  if (!markdown.trim()) {
    return [{ type: 'p', children: [{ text: '' }] }];
  }

  const lines = markdown.split('\n');
  const nodes: SlateValue = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Empty line
    if (!line.trim()) {
      i++;
      continue;
    }

    // Headings
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length as 1 | 2 | 3 | 4 | 5 | 6;
      const text = headingMatch[2];
      nodes.push({
        type: `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6',
        children: parseInlineMarkdown(text)
      });
      i++;
      continue;
    }

    // Code blocks
    const codeBlockMatch = line.match(/^```(\w+)?$/);
    if (codeBlockMatch) {
      const lang = codeBlockMatch[1];
      const codeLines: string[] = [];
      i++;

      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }

      nodes.push({
        type: 'code_block',
        lang: lang || undefined,
        children: [{ text: codeLines.join('\n') }]
      });
      i++; // Skip closing ```
      continue;
    }

    // Unordered lists
    if (line.match(/^-\s+(.+)$/)) {
      const listItems: ListItem[] = [];

      while (i < lines.length && lines[i].match(/^-\s+(.+)$/)) {
        const itemMatch = lines[i].match(/^-\s+(.+)$/);
        if (itemMatch) {
          listItems.push({
            type: 'lic',
            children: parseInlineMarkdown(itemMatch[1])
          });
        }
        i++;
      }

      nodes.push({ type: 'ul', children: listItems });
      continue;
    }

    // Ordered lists
    if (line.match(/^\d+\.\s+(.+)$/)) {
      const listItems: ListItem[] = [];

      while (i < lines.length && lines[i].match(/^\d+\.\s+(.+)$/)) {
        const itemMatch = lines[i].match(/^\d+\.\s+(.+)$/);
        if (itemMatch) {
          listItems.push({
            type: 'lic',
            children: parseInlineMarkdown(itemMatch[1])
          });
        }
        i++;
      }

      nodes.push({ type: 'ol', children: listItems });
      continue;
    }

    // Blockquotes
    if (line.startsWith('> ')) {
      const quoteText = line.substring(2);
      nodes.push({
        type: 'blockquote',
        children: [{ type: 'p', children: parseInlineMarkdown(quoteText) }]
      });
      i++;
      continue;
    }

    // Regular paragraph
    nodes.push({
      type: 'p',
      children: parseInlineMarkdown(line)
    });
    i++;
  }

  return nodes.length > 0 ? nodes : [{ type: 'p', children: [{ text: '' }] }];
}

/**
 * Parse inline markdown (bold, italic, code, links)
 */
function parseInlineMarkdown(text: string): (Text | Link)[] {
  const children: (Text | Link)[] = [];
  let remaining = text;

  while (remaining.length > 0) {
    // Bold
    const boldMatch = remaining.match(/^\*\*(.+?)\*\*/);
    if (boldMatch) {
      children.push({ text: boldMatch[1], bold: true });
      remaining = remaining.substring(boldMatch[0].length);
      continue;
    }

    // Italic
    const italicMatch = remaining.match(/^\*(.+?)\*/);
    if (italicMatch) {
      children.push({ text: italicMatch[1], italic: true });
      remaining = remaining.substring(italicMatch[0].length);
      continue;
    }

    // Inline code
    const codeMatch = remaining.match(/^`(.+?)`/);
    if (codeMatch) {
      children.push({ text: codeMatch[1], code: true });
      remaining = remaining.substring(codeMatch[0].length);
      continue;
    }

    // Links
    const linkMatch = remaining.match(/^\[(.+?)\]\((.+?)\)/);
    if (linkMatch) {
      children.push({
        type: 'a',
        url: linkMatch[2],
        children: [{ text: linkMatch[1] }]
      });
      remaining = remaining.substring(linkMatch[0].length);
      continue;
    }

    // Regular text - consume until next special character
    const nextSpecial = remaining.search(/[\*`\[]/);
    if (nextSpecial === -1) {
      children.push({ text: remaining });
      break;
    } else {
      children.push({ text: remaining.substring(0, nextSpecial) });
      remaining = remaining.substring(nextSpecial);
    }
  }

  return children.length > 0 ? children : [{ text: '' }];
}

/**
 * Convert Slate JSON to markdown string
 */
export function slateToMarkdown(value: SlateValue): string {
  return value.map(node => serializeNode(node)).join('\n\n') + '\n';
}

/**
 * Serialize single Slate node to markdown
 */
function serializeNode(node: SlateNode): string {
  switch (node.type) {
    case 'h1':
      return `# ${serializeChildren(node.children)}`;
    case 'h2':
      return `## ${serializeChildren(node.children)}`;
    case 'h3':
      return `### ${serializeChildren(node.children)}`;
    case 'h4':
      return `#### ${serializeChildren(node.children)}`;
    case 'h5':
      return `##### ${serializeChildren(node.children)}`;
    case 'h6':
      return `###### ${serializeChildren(node.children)}`;
    case 'code_block':
      const lang = (node as CodeBlock).lang || '';
      return '```' + lang + '\n' + node.children[0].text + '\n```';
    case 'ul':
      return (node as List).children.map(li => `- ${serializeChildren(li.children)}`).join('\n');
    case 'ol':
      return (node as List).children.map((li, i) => `${i + 1}. ${serializeChildren(li.children)}`).join('\n');
    case 'blockquote':
      return `> ${serializeChildren((node as Blockquote).children[0].children)}`;
    case 'p':
    default:
      return serializeChildren(node.children);
  }
}

/**
 * Serialize children (text nodes with formatting)
 */
function serializeChildren(children: (Text | Link | Paragraph)[]): string {
  return children.map(child => {
    if ('type' in child) {
      if (child.type === 'a') {
        return `[${child.children[0].text}](${child.url})`;
      }
      if (child.type === 'p') {
        return serializeChildren(child.children);
      }
      return '';
    }

    let text = child.text;
    if (child.bold) text = `**${text}**`;
    if (child.italic) text = `*${text}*`;
    if (child.code) text = `\`${text}\``;
    return text;
  }).join('');
}

/**
 * Preserve YAML frontmatter during conversion
 */
export function preserveYamlFrontmatter(content: string): {
  frontmatter: Record<string, unknown>;
  body: string;
} {
  try {
    const parsed = parseYamlFrontmatter(content);
    return {
      frontmatter: parsed.data as Record<string, unknown>,
      body: parsed.content
    };
  } catch {
    return {
      frontmatter: {},
      body: content
    };
  }
}
