import { render, screen } from '@testing-library/react';
import { PlateMarkdownToolbar } from '@/components/plate/PlateMarkdownToolbar';
import { TooltipProvider } from '@/components/ui/tooltip';

// Mock KEYS constant
jest.mock('platejs', () => ({
  KEYS: {
    bold: 'bold',
    italic: 'italic',
    code: 'code',
    strikethrough: 'strikethrough',
    codeBlock: 'code_block',
    blockquote: 'blockquote',
    p: 'p',
    ul: 'ul',
    ol: 'ol',
  },
  useMarkToolbarButton: jest.fn(() => ({
    props: { onClick: jest.fn() },
  })),
  useMarkToolbarButtonState: jest.fn(() => ({})),
}));

// Mock the PlateJS hooks and components
jest.mock('platejs/react', () => ({
  useEditorReadOnly: jest.fn(() => false),
  useEditorRef: jest.fn(() => ({
    undo: jest.fn(),
    redo: jest.fn(),
    history: {
      undos: [1],
      redos: [1],
    },
  })),
  useEditorSelector: jest.fn((selector) => {
    // Mock selector return value for list buttons
    return false;
  }),
  useSelectionFragmentProp: jest.fn(() => 'p'),
  useMarkToolbarButton: jest.fn(() => ({
    props: { onClick: jest.fn() },
  })),
  useMarkToolbarButtonState: jest.fn(() => ({})),
}));

jest.mock('@platejs/link/react', () => ({
  useLinkToolbarButton: jest.fn(() => ({
    props: { onClick: jest.fn() },
  })),
  useLinkToolbarButtonState: jest.fn(() => ({})),
}));

jest.mock('@platejs/list/react', () => ({
  useIndentTodoToolBarButton: jest.fn(() => ({
    props: { onClick: jest.fn() },
  })),
  useIndentTodoToolBarButtonState: jest.fn(() => ({})),
}));

jest.mock('@platejs/list', () => ({
  ListStyleType: {
    Disc: 'disc',
    Circle: 'circle',
    Square: 'square',
    Decimal: 'decimal',
    LowerAlpha: 'lower-alpha',
    UpperAlpha: 'upper-alpha',
    LowerRoman: 'lower-roman',
    UpperRoman: 'upper-roman',
  },
  someList: jest.fn(() => false),
  toggleList: jest.fn(),
}));

// Helper to render with required providers
function renderWithProviders(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

describe('PlateMarkdownToolbar', () => {
  it('renders all button groups', () => {
    const { container } = renderWithProviders(<PlateMarkdownToolbar />);

    // Check for toolbar container
    expect(screen.getByRole('toolbar')).toBeInTheDocument();

    // Count toolbar groups
    const toolbarGroups = container.querySelectorAll('.group\\/toolbar-group');
    expect(toolbarGroups).toHaveLength(5);

    // Check for specific icons by their SVG classes
    const allButtons = screen.getAllByRole('button');

    // History: Undo (undo-2) and Redo (redo-2)
    const undoButton = allButtons.find(btn => btn.querySelector('svg.lucide-undo-2'));
    const redoButton = allButtons.find(btn => btn.querySelector('svg.lucide-redo-2'));
    expect(undoButton).toBeInTheDocument();
    expect(redoButton).toBeInTheDocument();

    // Marks: Bold, Italic, Code, Strikethrough
    const boldButton = allButtons.find(btn => btn.querySelector('svg.lucide-bold'));
    const italicButton = allButtons.find(btn => btn.querySelector('svg.lucide-italic'));
    const codeInlineButton = allButtons.find(btn => {
      const svg = btn.querySelector('svg');
      return svg && svg.classList.toString().includes('code') && !svg.classList.toString().includes('file-code');
    });
    const strikeButton = allButtons.find(btn => btn.querySelector('svg.lucide-strikethrough'));
    expect(boldButton).toBeInTheDocument();
    expect(italicButton).toBeInTheDocument();
    expect(codeInlineButton).toBeInTheDocument();
    expect(strikeButton).toBeInTheDocument();

    // Headings: H1, H2, H3
    const h1Button = allButtons.find(btn => btn.querySelector('svg.lucide-heading-1'));
    const h2Button = allButtons.find(btn => btn.querySelector('svg.lucide-heading-2'));
    const h3Button = allButtons.find(btn => btn.querySelector('svg.lucide-heading-3'));
    expect(h1Button).toBeInTheDocument();
    expect(h2Button).toBeInTheDocument();
    expect(h3Button).toBeInTheDocument();

    // Lists: Bullet and Numbered - BulletedListToolbarButton and NumberedListToolbarButton render
    // This is verified by checking the fourth toolbar group exists and has content
    const fourthGroup = toolbarGroups[3];
    expect(fourthGroup).toBeInTheDocument();
    // The list buttons are complex split buttons, so just verify the group has content
    expect(fourthGroup.querySelectorAll('.flex.items-center').length).toBeGreaterThan(0);

    // Blocks: Code Block, Blockquote, Link
    const codeBlockButton = allButtons.find(btn => btn.querySelector('svg.lucide-file-code'));
    const quoteButton = allButtons.find(btn => btn.querySelector('svg.lucide-quote'));
    const linkButton = allButtons.find(btn => btn.querySelector('svg.lucide-link'));
    expect(codeBlockButton).toBeInTheDocument();
    expect(quoteButton).toBeInTheDocument();
    expect(linkButton).toBeInTheDocument();
  });

  it('renders in correct order', () => {
    const { container } = renderWithProviders(<PlateMarkdownToolbar />);

    const toolbarGroups = container.querySelectorAll('.group\\/toolbar-group');

    // Should have 5 toolbar groups
    expect(toolbarGroups).toHaveLength(5);

    // First group: History (Undo, Redo) - check by icon presence
    const historyGroup = toolbarGroups[0];
    expect(historyGroup.querySelector('svg.lucide-undo-2')).toBeInTheDocument();
    expect(historyGroup.querySelector('svg.lucide-redo-2')).toBeInTheDocument();

    // Second group: Marks (Bold, Italic, Code, Strikethrough) - check by icon presence
    const markGroup = toolbarGroups[1];
    expect(markGroup.querySelector('svg.lucide-bold')).toBeInTheDocument();
    expect(markGroup.querySelector('svg.lucide-italic')).toBeInTheDocument();

    // Third group: Headings (H1, H2, H3) - check by icon presence
    const headingGroup = toolbarGroups[2];
    expect(headingGroup.querySelector('svg.lucide-heading-1')).toBeInTheDocument();
    expect(headingGroup.querySelector('svg.lucide-heading-2')).toBeInTheDocument();
    expect(headingGroup.querySelector('svg.lucide-heading-3')).toBeInTheDocument();

    // Fourth group: Lists (Bullet, Numbered) - check by icon presence
    const listGroup = toolbarGroups[3];
    expect(listGroup.querySelector('svg.lucide-list')).toBeInTheDocument();
    expect(listGroup.querySelector('svg.lucide-list-ordered')).toBeInTheDocument();

    // Fifth group: Blocks (Code Block, Blockquote, Link) - check by icon presence
    const blockGroup = toolbarGroups[4];
    expect(blockGroup.querySelector('svg.lucide-file-code')).toBeInTheDocument();
    expect(blockGroup.querySelector('svg.lucide-quote')).toBeInTheDocument();
    expect(blockGroup.querySelector('svg.lucide-link')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = renderWithProviders(
      <PlateMarkdownToolbar className="custom-toolbar-class" />
    );

    const toolbar = container.querySelector('.custom-toolbar-class');
    expect(toolbar).toBeInTheDocument();
    expect(toolbar).toHaveClass('flex', 'w-full', 'items-center');
  });

  it('buttons are interactive (not disabled)', () => {
    renderWithProviders(<PlateMarkdownToolbar />);

    const allButtons = screen.getAllByRole('button');

    // Find specific buttons by icon and check they're not disabled
    const boldButton = allButtons.find(btn => btn.querySelector('svg.lucide-bold'));
    const italicButton = allButtons.find(btn => btn.querySelector('svg.lucide-italic'));
    const h1Button = allButtons.find(btn => btn.querySelector('svg.lucide-heading-1'));
    const linkButton = allButtons.find(btn => btn.querySelector('svg.lucide-link'));

    expect(boldButton).not.toBeDisabled();
    expect(italicButton).not.toBeDisabled();
    expect(h1Button).not.toBeDisabled();
    expect(linkButton).not.toBeDisabled();
  });
});
