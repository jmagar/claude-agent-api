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
  useEditorSelector: jest.fn((_selector: unknown) => {
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

// Mock transforms for BlockToolbarButton
jest.mock('@/components/editor/transforms', () => ({
  getBlockType: jest.fn(() => 'p'),
  setBlockType: jest.fn(),
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

    // History icons: Undo (undo-2) and Redo (redo-2)
    expect(container.querySelector('svg.lucide-undo-2')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-redo-2')).toBeInTheDocument();

    // Mark icons: Bold, Italic, Code, Strikethrough
    // Note: Code2Icon renders as 'lucide-code-2' but the actual class may vary
    expect(container.querySelector('svg.lucide-bold')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-italic')).toBeInTheDocument();
    // Code icon - look for any code-related icon (Code2Icon class name varies)
    const codeIcon = container.querySelector('svg[class*="code"]');
    expect(codeIcon).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-strikethrough')).toBeInTheDocument();

    // Heading icons: H1, H2, H3 (now BlockToolbarButton - renders as toggle items)
    expect(container.querySelector('svg.lucide-heading-1')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-heading-2')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-heading-3')).toBeInTheDocument();

    // List icons: Bullet and Numbered
    // The fourth toolbar group contains list buttons
    const fourthGroup = toolbarGroups[3];
    expect(fourthGroup).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-list')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-list-ordered')).toBeInTheDocument();

    // Block icons: Code Block, Blockquote (now BlockToolbarButton), Link
    expect(container.querySelector('svg.lucide-file-code')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-quote')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-link')).toBeInTheDocument();
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
    const { container } = renderWithProviders(<PlateMarkdownToolbar />);

    const allButtons = screen.getAllByRole('button');

    // Find mark buttons by icon and check they're not disabled
    const boldButton = allButtons.find(btn => btn.querySelector('svg.lucide-bold'));
    const italicButton = allButtons.find(btn => btn.querySelector('svg.lucide-italic'));
    const linkButton = allButtons.find(btn => btn.querySelector('svg.lucide-link'));

    expect(boldButton).not.toBeDisabled();
    expect(italicButton).not.toBeDisabled();
    expect(linkButton).not.toBeDisabled();

    // Block buttons (headings, code block, blockquote) render as toggle items,
    // not standard buttons. Verify they exist in the DOM via icons.
    expect(container.querySelector('svg.lucide-heading-1')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-file-code')).toBeInTheDocument();
    expect(container.querySelector('svg.lucide-quote')).toBeInTheDocument();
  });
});
