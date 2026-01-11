"use client";

import { useState, useCallback, memo } from "react";
import { Lightbulb, Code } from "lucide-react";
import type { SessionMode } from "@/types";

export interface ModeToggleProps {
  mode: SessionMode;
  onModeChange: (mode: SessionMode) => void;
  disabled?: boolean;
}

export const ModeToggle = memo(function ModeToggle({
  mode,
  onModeChange,
  disabled = false,
}: ModeToggleProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const handleClick = useCallback(() => {
    if (disabled) return;
    const newMode: SessionMode = mode === "brainstorm" ? "code" : "brainstorm";
    onModeChange(newMode);
  }, [mode, onModeChange, disabled]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (disabled) return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleClick();
      }
    },
    [handleClick, disabled]
  );

  const isBrainstorm = mode === "brainstorm";
  const targetMode = isBrainstorm ? "Code" : "Brainstorm";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        disabled={disabled}
        aria-label="Toggle mode"
        className={`
          flex items-center gap-8 rounded-8 px-12 py-8 text-14 font-medium
          transition-colors duration-200
          ${isBrainstorm ? "bg-yellow-100 text-yellow-800" : "bg-blue-100 text-blue-800"}
          ${disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer hover:opacity-80"}
        `}
      >
        {isBrainstorm ? (
          <Lightbulb
            data-testid="brainstorm-icon"
            className="h-16 w-16"
            aria-hidden="true"
          />
        ) : (
          <Code
            data-testid="code-icon"
            className="h-16 w-16"
            aria-hidden="true"
          />
        )}
        <span className="capitalize">{mode}</span>
      </button>

      {showTooltip && !disabled && (
        <div
          role="tooltip"
          className="absolute left-1/2 top-full z-50 mt-4 -translate-x-1/2 whitespace-nowrap rounded-6 bg-gray-900 px-8 py-4 text-12 text-white shadow-lg"
        >
          Click to switch to {targetMode} mode
        </div>
      )}
    </div>
  );
});
