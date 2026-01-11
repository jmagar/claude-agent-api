/**
 * ThreadingVisualization component
 *
 * Displays visual connection lines between parent and child tool calls.
 * Supports multiple threading modes:
 * - always: Always show connection lines
 * - hover: Show lines only on hover
 * - adaptive: Show for complex threads (2+ children), hide for simple
 * - toggle: Manual toggle button
 *
 * On mobile (< 768px), uses simple indentation instead of SVG lines.
 */

"use client";

import { useState, useEffect, memo } from "react";
import type { ToolCall } from "@/types";
import { Eye, EyeOff } from "lucide-react";
import { ToolCallCard } from "./ToolCallCard";

export interface ThreadingVisualizationProps {
  children: ToolCall[];
  mode?: "always" | "hover" | "adaptive" | "toggle";
  onRetryTool?: () => void;
}

export const ThreadingVisualization = memo(function ThreadingVisualization({
  children,
  mode = "always",
  onRetryTool,
}: ThreadingVisualizationProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isToggled, setIsToggled] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile viewport
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Determine if lines should be visible
  const shouldShowLines = () => {
    if (isMobile) return false; // No SVG lines on mobile
    if (mode === "always") return true;
    if (mode === "hover") return isHovered;
    if (mode === "adaptive") return children.length > 1; // Complex = 2+ children
    if (mode === "toggle") return isToggled;
    return false;
  };

  const isVisible = shouldShowLines();

  // Get color for status
  const getLineColor = (status: ToolCall["status"]) => {
    switch (status) {
      case "success":
        return "stroke-green-500";
      case "error":
        return "stroke-red-500";
      case "running":
        return "stroke-blue-500";
      default:
        return "stroke-gray-400";
    }
  };

  // Generate SVG path for curved connection line
  const generatePath = (childIndex: number) => {
    const startY = 40; // Parent bottom
    const endY = 60 + childIndex * 100; // Child top (staggered)
    const controlY = (startY + endY) / 2;

    // Bezier curve: M start C control1 control2 end
    return `M 20 ${startY} C 20 ${controlY}, 40 ${controlY}, 40 ${endY}`;
  };

  // On mobile, use indentation instead of lines
  if (isMobile) {
    return (
      <div data-testid="threading-wrapper" className="ml-16">
        <div data-testid="threading-children" className="flex flex-col gap-8">
          {children.map((toolCall) => (
            <ToolCallCard key={toolCall.id} toolCall={toolCall} onRetry={onRetryTool} />
          ))}
        </div>
      </div>
    );
  }

  // Adaptive mode - don't render for simple threads
  if (mode === "adaptive" && children.length <= 1) {
    return null;
  }

  return (
    <div
      data-testid="threading-wrapper"
      className="relative"
      onMouseEnter={() => mode === "hover" && setIsHovered(true)}
      onMouseLeave={() => mode === "hover" && setIsHovered(false)}
    >
      {/* Toggle button (only in toggle mode) */}
      {mode === "toggle" && (
        <button
          onClick={() => setIsToggled(!isToggled)}
          className="absolute top-8 right-8 z-10 p-6 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Toggle threading visualization"
        >
          {isToggled ? (
            <Eye className="w-16 h-16" />
          ) : (
            <EyeOff className="w-16 h-16" />
          )}
        </button>
      )}

      {/* SVG connection lines */}
      <svg
        data-testid="threading-svg"
        className={`absolute left-0 top-0 w-full h-full pointer-events-none transition-opacity duration-200 ${
          isVisible ? "opacity-100" : "opacity-0"
        } ${mode === "toggle" && !isToggled ? "hidden" : ""}`}
        role="img"
        aria-hidden="true"
      >
        {children.map((child, index) => (
          <path
            key={child.id}
            d={generatePath(index)}
            fill="none"
            strokeWidth="2"
            className={`${getLineColor(child.status)} transition-colors duration-200`}
          />
        ))}
      </svg>

      {/* Children container */}
      <div data-testid="threading-children" className="ml-40 flex flex-col gap-8">
        {children.map((toolCall) => (
          <ToolCallCard key={toolCall.id} toolCall={toolCall} onRetry={onRetryTool} />
        ))}
      </div>
    </div>
  );
});
