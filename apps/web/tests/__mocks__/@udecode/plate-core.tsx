import React, { useState, useEffect } from 'react';

export const Plate = ({ children, value, onChange }: any) => {
  return (
    <div data-testid="plate-wrapper" data-value={JSON.stringify(value)} data-onchange={!!onChange}>
      {children}
    </div>
  );
};

export const PlateContent = React.forwardRef(({
  id,
  placeholder,
  disabled,
  readOnly,
  autoFocus,
  className,
  style,
  ...props
}: any, ref) => {
  const [content, setContent] = useState('');

  // Extract parent's value from context (simulated)
  useEffect(() => {
    const wrapper = document.querySelector('[data-value]');
    if (wrapper) {
      try {
        const value = JSON.parse(wrapper.getAttribute('data-value') || '[]');
        const text = extractTextFromValue(value);
        setContent(text);
      } catch (e) {
        // ignore
      }
    }
  }, []);

  const handleInput = (e: React.FormEvent<HTMLDivElement>) => {
    const newText = e.currentTarget.textContent || '';
    setContent(newText);

    // Trigger onChange on parent
    const wrapper = document.querySelector('[data-onchange="true"]');
    if (wrapper) {
      // Simulate onChange being called
      const event = new CustomEvent('plate-change', {
        detail: [{ type: 'p', children: [{ text: newText }] }]
      });
      document.dispatchEvent(event);
    }
  };

  return (
    <div
      ref={ref}
      role="textbox"
      id={id}
      placeholder={placeholder}
      contentEditable={!disabled}
      data-disabled={disabled}
      data-readonly={readOnly}
      autoFocus={autoFocus}
      className={className}
      style={style}
      aria-label={props['aria-label']}
      aria-describedby={props['aria-describedby']}
      onInput={handleInput}
      suppressContentEditableWarning
    >
      {content}
    </div>
  );
});

PlateContent.displayName = 'PlateContent';

export const createPlugins = (plugins: any[]) => plugins;

function extractTextFromValue(value: any[]): string {
  if (!Array.isArray(value) || value.length === 0) {
    return '';
  }

  return value.map(node => {
    if (node.children) {
      return node.children.map((child: any) => {
        if (typeof child === 'object' && 'text' in child) {
          return child.text;
        }
        return '';
      }).join('');
    }
    return '';
  }).join('');
}
