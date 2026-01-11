/**
 * PermissionsChip Component
 *
 * A clickable chip that displays and cycles through permission modes:
 * - Default: Ask for approval before executing tools
 * - Accept Edits: Auto-accept file edits, ask for other tools
 * - Don't Ask: Auto-accept all tool executions
 * - Bypass Permissions: Skip all permission checks
 *
 * @see FR-020: System MUST display permissions chip with four modes
 * @see FR-021: System MUST allow cycling through permission modes
 */

"use client";

import { memo, useState, useCallback, useRef, useEffect } from "react";
import { Shield, Edit, FastForward, AlertTriangle } from "lucide-react";
import type { PermissionMode } from "@/types";

export interface PermissionsChipProps {
  /** Current permission mode */
  mode: PermissionMode;
  /** Callback when mode changes */
  onModeChange: (mode: PermissionMode) => void;
  /** Whether the chip is disabled */
  disabled?: boolean;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

/** Display configuration for each mode */
const MODE_CONFIG: Record<
  PermissionMode,
  {
    label: string;
    description: string;
    bgClass: string;
    textClass: string;
    icon: typeof Shield;
    iconTestId: string;
  }
> = {
  default: {
    label: "Default",
    description: "Ask for approval before executing tools",
    bgClass: "bg-gray-100",
    textClass: "text-gray-700",
    icon: Shield,
    iconTestId: "icon-shield",
  },
  acceptEdits: {
    label: "Accept Edits",
    description: "Auto-accept file edits, ask for other tools",
    bgClass: "bg-blue-100",
    textClass: "text-blue-700",
    icon: Edit,
    iconTestId: "icon-edit",
  },
  dontAsk: {
    label: "Don't Ask",
    description: "Auto-accept all tool executions",
    bgClass: "bg-yellow-100",
    textClass: "text-yellow-700",
    icon: FastForward,
    iconTestId: "icon-fast-forward",
  },
  bypassPermissions: {
    label: "Bypass",
    description: "Skip all permission checks (testing only)",
    bgClass: "bg-red-100",
    textClass: "text-red-700",
    icon: AlertTriangle,
    iconTestId: "icon-alert",
  },
};

/** Order of modes for cycling */
const MODE_ORDER: PermissionMode[] = ["default", "acceptEdits", "dontAsk", "bypassPermissions"];

export const PermissionsChip = memo(function PermissionsChip({
  mode,
  onModeChange,
  disabled = false,
  size = "md",
}: PermissionsChipProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const config = MODE_CONFIG[mode];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "text-12 px-8 py-4 gap-4",
    md: "text-14 px-10 py-6 gap-6",
    lg: "text-16 px-12 py-8 gap-8",
  };

  const iconSizes = {
    sm: "h-12 w-12",
    md: "h-14 w-14",
    lg: "h-16 w-16",
  };

  const cycleMode = useCallback(() => {
    if (disabled) return;
    const currentIndex = MODE_ORDER.indexOf(mode);
    const nextIndex = (currentIndex + 1) % MODE_ORDER.length;
    onModeChange(MODE_ORDER[nextIndex]);
  }, [mode, onModeChange, disabled]);

  const handleClick = useCallback(() => {
    cycleMode();
  }, [cycleMode]);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      if (disabled) return;
      setIsMenuOpen(true);
      setFocusedIndex(MODE_ORDER.indexOf(mode));
    },
    [disabled, mode]
  );

  const handleMouseDown = useCallback(() => {
    if (disabled) return;
    longPressTimer.current = setTimeout(() => {
      setIsMenuOpen(true);
      setFocusedIndex(MODE_ORDER.indexOf(mode));
    }, 500);
  }, [disabled, mode]);

  const handleMouseUp = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (disabled) return;

      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (isMenuOpen) {
          if (focusedIndex >= 0) {
            onModeChange(MODE_ORDER[focusedIndex]);
            setIsMenuOpen(false);
          }
        } else {
          cycleMode();
        }
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        if (!isMenuOpen) {
          setIsMenuOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) => Math.min(prev + 1, MODE_ORDER.length - 1));
        }
      } else if (e.key === "ArrowUp" && isMenuOpen) {
        e.preventDefault();
        setFocusedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Escape" && isMenuOpen) {
        setIsMenuOpen(false);
        buttonRef.current?.focus();
      }
    },
    [disabled, isMenuOpen, focusedIndex, onModeChange, cycleMode]
  );

  const handleMenuItemClick = useCallback(
    (selectedMode: PermissionMode) => {
      onModeChange(selectedMode);
      setIsMenuOpen(false);
      buttonRef.current?.focus();
    },
    [onModeChange]
  );

  // Close menu when clicking outside
  useEffect(() => {
    if (!isMenuOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isMenuOpen]);

  // Focus menu item when focusedIndex changes
  useEffect(() => {
    if (isMenuOpen && focusedIndex >= 0 && menuRef.current) {
      const items = menuRef.current.querySelectorAll('[role="menuitem"]');
      if (items[focusedIndex]) {
        (items[focusedIndex] as HTMLElement).focus();
      }
    }
  }, [isMenuOpen, focusedIndex]);

  return (
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onKeyDown={handleKeyDown}
        onMouseEnter={() => setShowTooltip(true)}
        onFocus={() => setShowTooltip(true)}
        onMouseOut={() => setShowTooltip(false)}
        onBlur={() => setShowTooltip(false)}
        disabled={disabled}
        aria-label={`Permissions mode: ${config.label}`}
        aria-live="polite"
        aria-haspopup="menu"
        aria-expanded={isMenuOpen}
        className={`
          inline-flex items-center rounded-full
          transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          disabled:cursor-not-allowed disabled:opacity-50
          ${config.bgClass} ${config.textClass}
          ${sizeClasses[size]}
        `}
      >
        <Icon
          className={iconSizes[size]}
          aria-hidden="true"
          data-testid={config.iconTestId}
        />
        <span className="font-medium">{config.label}</span>
      </button>

      {/* Tooltip */}
      {showTooltip && !isMenuOpen && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 z-50 mb-8 -translate-x-1/2 whitespace-nowrap rounded-6 bg-gray-900 px-12 py-6 text-12 text-white shadow-lg"
        >
          {config.description}
          <div className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}

      {/* Dropdown menu */}
      {isMenuOpen && (
        <div
          ref={menuRef}
          role="menu"
          aria-labelledby={buttonRef.current?.id}
          className="absolute left-0 top-full z-50 mt-4 min-w-[200px] rounded-8 bg-white py-4 shadow-lg ring-1 ring-black/5"
        >
          {MODE_ORDER.map((modeOption, index) => {
            const optionConfig = MODE_CONFIG[modeOption];
            const OptionIcon = optionConfig.icon;
            const isSelected = modeOption === mode;

            return (
              <button
                key={modeOption}
                role="menuitem"
                aria-checked={isSelected}
                tabIndex={focusedIndex === index ? 0 : -1}
                onClick={() => handleMenuItemClick(modeOption)}
                className={`
                  flex w-full items-center gap-8 px-12 py-8 text-left text-14
                  transition-colors
                  hover:bg-gray-100
                  focus:bg-gray-100 focus:outline-none
                  ${isSelected ? "bg-gray-50" : ""}
                `}
              >
                <OptionIcon className="h-16 w-16" aria-hidden="true" />
                <div className="flex-1">
                  <div className="font-medium">{optionConfig.label}</div>
                  <div className="text-12 text-gray-500">{optionConfig.description}</div>
                </div>
                {isSelected && (
                  <span className="text-12 text-blue-600">✓</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
});
