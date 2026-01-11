/**
 * ToolManagementModal Component
 *
 * Modal for managing tools with:
 * - Tools grouped by MCP server
 * - Enable/disable individual tools
 * - Save and load tool presets
 * - Search and filter tools
 *
 * @see FR-017: System MUST show tool management modal with tools grouped by MCP server
 * @see FR-018: System MUST allow enabling/disabling individual tools
 * @see FR-019: System MUST support saving tool configurations as named presets
 * @see FR-033: System MUST display MCP tools grouped by server
 */

"use client";

import { memo, useState, useCallback, useRef, useEffect, useMemo } from "react";
import { X, Search, ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";
import type { ToolDefinition, ToolPreset, McpServerConfig } from "@/types";
import {
  groupToolsByServer,
  filterToolsByServer,
  countEnabledTools,
  areAllToolsEnabled,
  areSomeToolsEnabled,
  getEnabledToolNames,
} from "@/utils/toolSelection";

export interface ToolManagementModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Close modal callback */
  onClose: () => void;
  /** List of available tools */
  tools: ToolDefinition[];
  /** List of MCP servers */
  servers: McpServerConfig[];
  /** List of saved presets */
  presets: ToolPreset[];
  /** Callback when a tool is toggled */
  onToolToggle: (toolName: string, enabled: boolean) => void;
  /** Callback when a preset is selected */
  onPresetSelect: (preset: ToolPreset) => void;
  /** Callback when a new preset is created */
  onPresetCreate: (preset: Omit<ToolPreset, "id" | "created_at">) => void;
  /** Callback when a preset is deleted */
  onPresetDelete: (presetId: string) => void;
  /** Whether the modal is loading data */
  isLoading?: boolean;
  /** Error message to display */
  error?: string;
  /** Retry callback for error state */
  onRetry?: () => void;
}

export const ToolManagementModal = memo(function ToolManagementModal({
  open,
  onClose,
  tools,
  servers,
  presets,
  onToolToggle,
  onPresetSelect,
  onPresetCreate,
  onPresetDelete,
  isLoading = false,
  error,
  onRetry,
}: ToolManagementModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showEnabledOnly, setShowEnabledOnly] = useState(false);
  const [expandedServers, setExpandedServers] = useState<Set<string>>(new Set());
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [newPresetName, setNewPresetName] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showPresetDropdown, setShowPresetDropdown] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Group tools by server
  const toolsByServer = useMemo(() => groupToolsByServer(tools), [tools]);

  // Filter tools based on search and enabled filter
  const filteredToolsByServer = useMemo(
    () => filterToolsByServer(toolsByServer, searchQuery, showEnabledOnly),
    [toolsByServer, searchQuery, showEnabledOnly]
  );

  // Calculate enabled count
  const enabledCount = useMemo(() => countEnabledTools(tools), [tools]);

  // Get server config by name
  const getServerConfig = useCallback(
    (serverName: string) => servers.find((s) => s.name === serverName),
    [servers]
  );

  // Initialize expanded servers on first open
  useEffect(() => {
    if (open && expandedServers.size === 0) {
      setExpandedServers(new Set(toolsByServer.keys()));
    }
  }, [open, toolsByServer, expandedServers.size]);

  // Focus search input when modal opens
  useEffect(() => {
    if (open && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [open]);

  // Handle escape key
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (showSaveDialog) {
          setShowSaveDialog(false);
        } else if (showDeleteConfirm) {
          setShowDeleteConfirm(false);
        } else if (showPresetDropdown) {
          setShowPresetDropdown(false);
        } else {
          onClose();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, showSaveDialog, showDeleteConfirm, showPresetDropdown, onClose]);

  const toggleServer = useCallback((serverName: string) => {
    setExpandedServers((prev) => {
      const next = new Set(prev);
      if (next.has(serverName)) {
        next.delete(serverName);
      } else {
        next.add(serverName);
      }
      return next;
    });
  }, []);

  const toggleAllInServer = useCallback(
    (serverName: string) => {
      const serverTools = toolsByServer.get(serverName) ?? [];
      const allEnabled = areAllToolsEnabled(serverTools);

      for (const tool of serverTools) {
        onToolToggle(tool.name, !allEnabled);
      }
    },
    [toolsByServer, onToolToggle]
  );

  const handlePresetSelect = useCallback(
    (preset: ToolPreset) => {
      // Optimize: Update UI state immediately for responsive feedback
      setSelectedPresetId(preset.id);
      setShowPresetDropdown(false);

      // Defer preset application to next tick to avoid blocking UI
      // This allows the dropdown to close smoothly before heavy updates
      requestAnimationFrame(() => {
        onPresetSelect(preset);
      });
    },
    [onPresetSelect]
  );

  const handleSavePreset = useCallback(() => {
    const enabledTools = getEnabledToolNames(tools);
    onPresetCreate({
      name: newPresetName,
      tools: enabledTools,
    });
    setNewPresetName("");
    setShowSaveDialog(false);
  }, [tools, newPresetName, onPresetCreate]);

  const handleDeletePreset = useCallback(() => {
    if (selectedPresetId) {
      onPresetDelete(selectedPresetId);
      setSelectedPresetId(null);
    }
    setShowDeleteConfirm(false);
  }, [selectedPresetId, onPresetDelete]);

  const selectedPreset = presets.find((p) => p.id === selectedPresetId);

  if (!open) return null;

  return (
    <div
      data-testid="modal-backdrop"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="tool-modal-title"
        className="relative flex max-h-[80vh] w-full max-w-2xl flex-col rounded-12 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-24 py-16">
          <h2 id="tool-modal-title" className="text-18 font-semibold">
            Tool Management
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-6 p-4 hover:bg-gray-100"
          >
            <X className="h-20 w-20" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-12 border-b border-gray-200 px-24 py-12">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-12 top-1/2 h-16 w-16 -translate-y-1/2 text-gray-400" />
            <input
              ref={searchInputRef}
              type="search"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search tools"
              className="w-full rounded-8 border border-gray-300 py-8 pl-40 pr-32 text-14 focus:border-blue-500 focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                aria-label="Clear search"
                className="absolute right-8 top-1/2 -translate-y-1/2 rounded-4 p-4 hover:bg-gray-100"
              >
                <X className="h-12 w-12" />
              </button>
            )}
          </div>

          {/* Enabled only filter */}
          <label className="flex items-center gap-8 text-14">
            <input
              type="checkbox"
              checked={showEnabledOnly}
              onChange={(e) => setShowEnabledOnly(e.target.checked)}
              aria-label="Show enabled only"
              className="rounded-4"
            />
            <span>Show enabled only</span>
          </label>

          {/* Preset dropdown */}
          <div className="relative">
            <button
              type="button"
              role="combobox"
              aria-label="Preset"
              aria-expanded={showPresetDropdown}
              onClick={() => setShowPresetDropdown(!showPresetDropdown)}
              className="flex items-center gap-8 rounded-8 border border-gray-300 px-12 py-8 text-14 hover:bg-gray-50"
            >
              <span>{selectedPreset?.name ?? "Select preset..."}</span>
              <ChevronDown className="h-14 w-14" />
            </button>

            {showPresetDropdown && (
              <div className="absolute right-0 top-full z-10 mt-4 min-w-[200px] rounded-8 bg-white py-4 shadow-lg ring-1 ring-black/5">
                {presets.map((preset) => (
                  <button
                    key={preset.id}
                    role="option"
                    aria-selected={preset.id === selectedPresetId}
                    onClick={() => handlePresetSelect(preset)}
                    className="flex w-full items-center gap-8 px-12 py-8 text-left text-14 hover:bg-gray-100"
                  >
                    <span className="flex-1">{preset.name}</span>
                    {preset.is_default && (
                      <span className="text-12 text-gray-500">Default</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Save preset button */}
          <button
            type="button"
            onClick={() => setShowSaveDialog(true)}
            aria-label="Save preset"
            className="flex items-center gap-4 rounded-8 bg-blue-600 px-12 py-8 text-14 font-medium text-white hover:bg-blue-700"
          >
            <Plus className="h-14 w-14" />
            Save Preset
          </button>

          {/* Delete preset button (only for non-default presets) */}
          {selectedPreset && !selectedPreset.is_default && (
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(true)}
              aria-label="Delete preset"
              className="flex items-center gap-4 rounded-8 border border-red-300 px-12 py-8 text-14 text-red-600 hover:bg-red-50"
            >
              <Trash2 className="h-14 w-14" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-24 py-16">
          {/* Loading state */}
          {isLoading && (
            <div data-testid="tool-modal-loading" className="space-y-16">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-8">
                  <div className="h-24 w-48 animate-pulse rounded-6 bg-gray-200" />
                  <div className="space-y-4">
                    <div className="h-40 animate-pulse rounded-8 bg-gray-100" />
                    <div className="h-40 animate-pulse rounded-8 bg-gray-100" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="flex flex-col items-center py-32 text-center">
              <p className="mb-16 text-red-600">{error}</p>
              <button
                type="button"
                onClick={onRetry}
                aria-label="Retry"
                disabled={!onRetry}
                className="rounded-8 bg-blue-600 px-16 py-8 text-14 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                Retry
              </button>
            </div>
          )}

          {/* Empty search state */}
          {!isLoading && !error && filteredToolsByServer.size === 0 && (
            <div className="py-32 text-center text-gray-500">
              No tools found
            </div>
          )}

          {/* Tool list grouped by server */}
          {!isLoading && !error && filteredToolsByServer.size > 0 && (
            <div className="space-y-16">
              {Array.from(filteredToolsByServer.entries()).map(([serverName, serverTools]) => {
                const serverConfig = getServerConfig(serverName);
                const isExpanded = expandedServers.has(serverName);
                const allEnabled = areAllToolsEnabled(serverTools);
                const someEnabled = areSomeToolsEnabled(serverTools);

                return (
                  <div
                    key={serverName}
                    data-server-group
                    data-testid={`server-group-${serverName}`}
                    className="rounded-8 border border-gray-200"
                  >
                    {/* Server header */}
                    <button
                      type="button"
                      data-testid={`server-header-${serverName}`}
                      onClick={() => toggleServer(serverName)}
                      className="flex w-full items-center gap-12 px-16 py-12 hover:bg-gray-50"
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-16 w-16" />
                      ) : (
                        <ChevronRight className="h-16 w-16" />
                      )}

                      {/* Status indicator */}
                      <span
                        data-testid="status-indicator"
                        className={`h-8 w-8 rounded-full ${
                          serverConfig?.status === "active"
                            ? "bg-green-500"
                            : serverConfig?.status === "failed"
                            ? "bg-red-500"
                            : "bg-gray-400"
                        }`}
                      />

                      <span className="font-medium">{serverName}</span>
                      <span className="text-12 text-gray-500">
                        {serverTools.length} {serverTools.length === 1 ? "tool" : "tools"}
                      </span>

                      {/* Toggle all checkbox */}
                      <label
                        className="ml-auto flex items-center gap-4"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          checked={allEnabled}
                          ref={(el) => {
                            if (el) {
                              el.indeterminate = someEnabled && !allEnabled;
                            }
                          }}
                          onChange={() => toggleAllInServer(serverName)}
                          aria-label={`Toggle all ${serverName}`}
                          className="rounded-4"
                        />
                      </label>
                    </button>

                    {/* Tool list */}
                    {isExpanded && (
                      <div className="border-t border-gray-200 py-8">
                        {serverTools.map((tool) => (
                          <div
                            key={tool.name}
                            data-testid={`tool-item-${tool.name}`}
                            className="flex items-center gap-12 px-16 py-8 hover:bg-gray-50"
                          >
                            <label className="flex flex-1 cursor-pointer items-center gap-12">
                              <input
                                type="checkbox"
                                role="switch"
                                checked={tool.enabled}
                                onChange={() => onToolToggle(tool.name, !tool.enabled)}
                                aria-label={tool.name}
                                className="rounded-4"
                              />
                              <div className="min-w-0 flex-1">
                                <div className="font-medium text-gray-900">{tool.name}</div>
                                <div className="truncate text-12 text-gray-500">
                                  {tool.description}
                                </div>
                              </div>
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-200 px-24 py-12">
          <span className="text-14 text-gray-500">
            {enabledCount} of {tools.length} tools enabled
          </span>
        </div>

        {/* Save preset dialog */}
        {showSaveDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div
              role="dialog"
              aria-modal="true"
              aria-label="Save preset"
              className="w-full max-w-sm rounded-12 bg-white p-24 shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-16 text-16 font-semibold">Save Preset</h3>
              <label className="block">
                <span className="text-14 text-gray-700">Preset name</span>
                <input
                  type="text"
                  value={newPresetName}
                  onChange={(e) => setNewPresetName(e.target.value)}
                  aria-label="Preset name"
                  className="mt-4 w-full rounded-8 border border-gray-300 px-12 py-8 text-14 focus:border-blue-500 focus:outline-none"
                  autoFocus
                />
              </label>
              <div className="mt-16 flex justify-end gap-8">
                <button
                  type="button"
                  onClick={() => setShowSaveDialog(false)}
                  className="rounded-8 px-12 py-8 text-14 hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSavePreset}
                  aria-label="Save"
                  disabled={!newPresetName.trim()}
                  className="rounded-8 bg-blue-600 px-12 py-8 text-14 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete confirmation dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div
              role="dialog"
              aria-modal="true"
              className="w-full max-w-sm rounded-12 bg-white p-24 shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="mb-8 text-16 font-semibold">Delete Preset?</h3>
              <p className="mb-16 text-14 text-gray-600">
                Are you sure you want to delete &quot;{selectedPreset?.name}&quot;?
              </p>
              <div className="flex justify-end gap-8">
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(false)}
                  className="rounded-8 px-12 py-8 text-14 hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDeletePreset}
                  aria-label="Confirm"
                  className="rounded-8 bg-red-600 px-12 py-8 text-14 font-medium text-white hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
