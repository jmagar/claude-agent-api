/**
 * ChatInterface component
 *
 * Main container for chat UI - combines MessageList, Composer, and streaming logic.
 * Manages message state, loading, and error handling.
 * Includes sidebar with mode toggle and session management.
 *
 * @see tests/integration/chat-flow.test.tsx for test specifications
 * @see wireframes/01-chat-brainstorm-mode.html for design
 */

"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { MessageList } from "./MessageList";
import { Composer } from "./Composer";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useStreamingQuery } from "@/hooks/useStreamingQuery";
import { useCheckpoints } from "@/hooks/useCheckpoints";
import { useQuery } from "@tanstack/react-query";
import { ModeToggle } from "@/components/sidebar/ModeToggle";
import { ProjectPicker } from "@/components/modals/ProjectPickerModal";
import { useModeOptional } from "@/contexts/ModeContext";
import { PermissionsChip } from "@/components/shared/PermissionsChip";
import { ToolBadge } from "@/components/shared/ToolBadge";
import { ToolManagementModal } from "@/components/modals/ToolManagementModal";
import { ToolApprovalCard } from "./ToolApprovalCard";
import { ToolCallCard } from "./ToolCallCard";
import { usePermissionsOptional } from "@/contexts/PermissionsContext";
import { useActiveSession } from "@/contexts/ActiveSessionContext";
import type {
  Message,
  Project,
  SessionMode,
  ToolDefinition,
  ToolPreset,
  McpServerConfig,
  PermissionMode,
} from "@/types";
import { isToolUseBlock } from "@/types";

const PERMISSION_MODES: PermissionMode[] = [
  "default",
  "acceptEdits",
  "dontAsk",
  "bypassPermissions",
];
const FILE_EDIT_TOOLS = new Set([
  "write_file",
  "edit_file",
  "create_file",
  "apply_patch",
  "delete_file",
  "rename_file",
  "move_file",
]);

export interface ChatInterfaceProps {
  /** Session ID for this chat (optional - will be generated if not provided) */
  sessionId?: string;
}

export function ChatInterface({ sessionId: initialSessionId }: ChatInterfaceProps) {
  // Only show loading state if we're resuming an existing session
  const [loadingMessages, setLoadingMessages] = useState(!!initialSessionId);
  const [showProjectPicker, setShowProjectPicker] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [toolsLoading, setToolsLoading] = useState(false);
  const [toolsError, setToolsError] = useState<string | null>(null);
  const [servers, setServers] = useState<McpServerConfig[]>([]);
  const [presets, setPresets] = useState<ToolPreset[]>([]);
  const [toolModalOpen, setToolModalOpen] = useState(false);
  const [toolModalLoading, setToolModalLoading] = useState(false);
  const [toolModalError, setToolModalError] = useState<string | null>(null);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [handledApprovalIds, setHandledApprovalIds] = useState<Set<string>>(
    new Set()
  );

  // Mode context - provides mode state and persistence
  // We always call useModeOptional() to satisfy Rules of Hooks, then check if it's available
  const modeContext = useModeOptional();

  // Fallback local state if context is not available
  const [localMode, setLocalMode] = useState<SessionMode>("brainstorm");
  const [localSelectedProjectId, setLocalSelectedProjectId] = useState<string | null>(null);
  const [localSelectedProject, setLocalSelectedProject] = useState<Project | null>(null);

  const mode = modeContext?.mode ?? localMode;
  const selectedProjectId = modeContext?.selectedProjectId ?? localSelectedProjectId;
  const selectedProject = modeContext?.selectedProject ?? localSelectedProject;
  const setMode = modeContext?.setMode ?? setLocalMode;
  const setSelectedProjectId = modeContext?.setSelectedProjectId ?? setLocalSelectedProjectId;
  const setSelectedProject = modeContext?.setSelectedProject ?? setLocalSelectedProject;

  const permissionsContext = usePermissionsOptional();
  const [localPermissionMode, setLocalPermissionMode] =
    useState<PermissionMode>("default");
  const permissionMode = permissionsContext?.mode ?? localPermissionMode;

  useEffect(() => {
    if (permissionsContext || typeof window === "undefined") {
      return;
    }
    const stored = localStorage.getItem("permissionMode");
    if (!stored) {
      return;
    }
    try {
      const parsed = JSON.parse(stored) as PermissionMode;
      if (PERMISSION_MODES.includes(parsed)) {
        setLocalPermissionMode(parsed);
      }
    } catch {
      // Ignore malformed stored value
    }
  }, [permissionsContext]);

  const setPermissionMode = useCallback(
    (newMode: PermissionMode) => {
      if (permissionsContext) {
        permissionsContext.setMode(newMode);
        return;
      }
      setLocalPermissionMode(newMode);
      if (typeof window !== "undefined") {
        localStorage.setItem("permissionMode", JSON.stringify(newMode));
      }
    },
    [permissionsContext]
  );

  const cyclePermissionMode = useCallback(() => {
    const currentIndex = PERMISSION_MODES.indexOf(permissionMode);
    const nextMode = PERMISSION_MODES[(currentIndex + 1) % PERMISSION_MODES.length];
    setPermissionMode(nextMode);
  }, [permissionMode, setPermissionMode]);

  const {
    messages: streamMessages,
    toolCalls,
    sessionId, // Get the actual session ID from the hook (updated from init event)
    isStreaming,
    error,
    sendMessage,
    retry,
    clearError,
  } = useStreamingQuery(initialSessionId);
  const {
    messages: allMessages,
    setMessages: setAllMessages,
    setIsStreaming: setContextStreaming,
  } = useActiveSession();
  const resolvedSessionId = sessionId ?? initialSessionId ?? "";
  const { checkpoints } = useCheckpoints(resolvedSessionId);

  const fetchTools = useCallback(async () => {
    setToolsLoading(true);
    try {
      const response = await fetch("/api/tools");
      if (!response.ok) {
        throw new Error("Failed to load tools");
      }
      const data = await response.json();
      const nextTools = Array.isArray(data) ? data : data.tools ?? [];
      setTools(nextTools);
      setToolsError(null);
    } catch (err) {
      setToolsError(err instanceof Error ? err.message : "Failed to load tools");
    } finally {
      setToolsLoading(false);
    }
  }, []);

  const fetchToolModalData = useCallback(async () => {
    setToolModalLoading(true);
    try {
      const [serversResponse, presetsResponse] = await Promise.all([
        fetch("/api/mcp-servers"),
        fetch("/api/tool-presets"),
      ]);

      if (!serversResponse.ok) {
        throw new Error("Failed to load MCP servers");
      }
      if (!presetsResponse.ok) {
        throw new Error("Failed to load tool presets");
      }

      const serversData = await serversResponse.json();
      const presetsData = await presetsResponse.json();

      setServers(Array.isArray(serversData) ? serversData : serversData.servers ?? []);
      setPresets(Array.isArray(presetsData) ? presetsData : presetsData.presets ?? []);
      setToolModalError(null);
    } catch (err) {
      setToolModalError(
        err instanceof Error ? err.message : "Failed to load tool settings"
      );
    } finally {
      setToolModalLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTools();
  }, [fetchTools]);

  useEffect(() => {
    if (toolModalOpen) {
      fetchToolModalData();
    }
  }, [toolModalOpen, fetchToolModalData]);

  // Fetch projects when needed
  const fetchProjects = useCallback(async () => {
    try {
      const response = await fetch("/api/projects");
      if (!response.ok) {
        throw new Error("Failed to load projects");
      }
      const data = await response.json();
      const nextProjects = Array.isArray(data) ? data : data.projects ?? [];
      setProjects(nextProjects);
      setProjectsError(null);
      return nextProjects as Project[];
    } catch (err) {
      setProjectsError(err instanceof Error ? err.message : "Failed to load projects");
      return [];
    }
  }, []);

  // Load project data if we're in code mode with a selectedProjectId but no project object
  useEffect(() => {
    if (mode === "code" && selectedProjectId && !selectedProject) {
      fetchProjects().then((fetchedProjects) => {
        const project = fetchedProjects.find((p) => p.id === selectedProjectId);
        if (project) {
          setSelectedProject(project);
        }
      });
    }
  }, [mode, selectedProjectId, selectedProject, setSelectedProject, fetchProjects]);

  // Handle mode change
  const handleModeChange = useCallback(
    (newMode: SessionMode) => {
      if (newMode === "code" && mode === "brainstorm") {
        // Switching to code mode - show project picker
        fetchProjects();
        setShowProjectPicker(true);
      } else {
        // Switching to brainstorm mode - just change mode
        setMode(newMode);
        setSelectedProjectId(null);
        setSelectedProject(null);
      }
    },
    [mode, setMode, setSelectedProjectId, setSelectedProject, fetchProjects]
  );

  // Handle project selection
  const handleSelectProject = useCallback(
    (project: Project) => {
      setMode("code");
      setSelectedProjectId(project.id);
      setSelectedProject(project);
      setShowProjectPicker(false);
    },
    [setMode, setSelectedProjectId, setSelectedProject]
  );

  // Handle project picker close
  const handleProjectPickerClose = useCallback(() => {
    setShowProjectPicker(false);
    // Don't change mode if cancelled
  }, []);

  // Fetch existing messages on mount (only if we have an initial session ID to resume)
  const { data: existingMessages } = useQuery<{ messages: Message[] }>({
    queryKey: ["messages", initialSessionId],
    queryFn: async () => {
      const response = await fetch(`/api/sessions/${initialSessionId}/messages`);
      if (!response.ok) {
        throw new Error("Failed to load messages");
      }
      return response.json();
    },
    enabled: !!initialSessionId, // Only fetch if we're resuming an existing session
  });

  useEffect(() => {
    setContextStreaming(isStreaming);
  }, [isStreaming, setContextStreaming]);

  useEffect(() => {
    if (existingMessages?.messages) {
      setAllMessages(existingMessages.messages);
      setLoadingMessages(false);
    }
  }, [existingMessages, setAllMessages]);

  useEffect(() => {
    if (streamMessages.length > 0) {
      // Merge with existing, avoid duplicates
      setAllMessages((prev) => {
        const existingIds = new Set(prev.map((m) => m.id));
        const newMessages = streamMessages.filter(
          (m) => !existingIds.has(m.id)
        );
        return [...prev, ...newMessages];
      });
    }
  }, [streamMessages, setAllMessages]);

  const toolCallsById = useMemo(
    () =>
      toolCalls.reduce<Record<string, (typeof toolCalls)[number]>>((acc, toolCall) => {
        acc[toolCall.id] = toolCall;
        return acc;
      }, {}),
    [toolCalls]
  );

  // Handle send message
  const handleSend = async (text: string) => {
    clearError();
    await sendMessage(text);
  };

  const handleApprovalSubmit = useCallback(
    async (toolCallId: string, toolName: string, approved: boolean, remember: boolean) => {
      setApprovalError(null);
      try {
        const response = await fetch("/api/tool-approval", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tool_use_id: toolCallId,
            approved,
            remember,
          }),
        });

        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({
            error: { message: "Tool approval failed" },
          }));
          throw new Error(
            errorBody.error?.message ?? "Tool approval failed"
          );
        }

        if (remember && permissionsContext) {
          permissionsContext.addAlwaysAllowedTool(toolName);
        }

        setHandledApprovalIds((prev) => {
          const next = new Set(prev);
          next.add(toolCallId);
          return next;
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Tool approval failed";
        setApprovalError(message);
      }
    },
    [permissionsContext]
  );

  const pendingApprovals = useMemo(
    () =>
      toolCalls.filter(
        (toolCall) =>
          toolCall.requires_approval &&
          !handledApprovalIds.has(toolCall.id) &&
          permissionMode === "default"
      ),
    [toolCalls, handledApprovalIds, permissionMode]
  );

  const toolUseIdsInMessages = useMemo(() => {
    const ids = new Set<string>();
    for (const message of allMessages) {
      for (const block of message.content) {
        if (isToolUseBlock(block)) {
          ids.add(block.id);
        }
      }
    }
    return ids;
  }, [allMessages]);

  const orphanToolCalls = useMemo(
    () =>
      toolCalls.filter(
        (toolCall) =>
          !toolUseIdsInMessages.has(toolCall.id) &&
          !toolCall.parent_tool_use_id
      ),
    [toolCalls, toolUseIdsInMessages]
  );

  useEffect(() => {
    if (
      permissionMode !== "acceptEdits" &&
      permissionMode !== "dontAsk" &&
      permissionMode !== "bypassPermissions"
    ) {
      return;
    }

    const autoApprove = async () => {
      for (const toolCall of toolCalls) {
        if (!toolCall.requires_approval) {
          continue;
        }
        if (handledApprovalIds.has(toolCall.id)) {
          continue;
        }
        if (
          permissionMode === "acceptEdits" &&
          !FILE_EDIT_TOOLS.has(toolCall.name)
        ) {
          continue;
        }

        await handleApprovalSubmit(toolCall.id, toolCall.name, true, false);
      }
    };

    void autoApprove();
  }, [toolCalls, handledApprovalIds, permissionMode, handleApprovalSubmit]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!event.ctrlKey || !event.shiftKey) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === "p") {
        event.preventDefault();
        cyclePermissionMode();
      }
      if (key === "t") {
        event.preventDefault();
        setToolModalOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [cyclePermissionMode]);

  const handleToolToggle = useCallback((toolName: string, enabled: boolean) => {
    setTools((prev) =>
      prev.map((tool) =>
        tool.name === toolName ? { ...tool, enabled } : tool
      )
    );
  }, []);

  const handlePresetSelect = useCallback(async (preset: ToolPreset) => {
    try {
      const response = await fetch(`/api/tool-presets/${preset.id}/apply`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Failed to apply preset");
      }
      const data = await response.json();
      const updatedTools = Array.isArray(data) ? data : data.tools ?? [];
      if (updatedTools.length > 0) {
        setTools(updatedTools);
      }
    } catch (err) {
      setToolModalError(
        err instanceof Error ? err.message : "Failed to apply preset"
      );
    }
  }, []);

  const handlePresetCreate = useCallback(
    (preset: Omit<ToolPreset, "id" | "created_at">) => {
      const createdPreset: ToolPreset = {
        id: `preset-${Date.now()}`,
        name: preset.name,
        description: preset.description,
        tools: preset.tools,
        created_at: new Date(),
      };
      setPresets((prev) => [...prev, createdPreset]);
    },
    []
  );

  const handlePresetDelete = useCallback((presetId: string) => {
    setPresets((prev) => prev.filter((preset) => preset.id !== presetId));
  }, []);

  const enabledToolCount = useMemo(
    () => tools.filter((tool) => tool.enabled).length,
    [tools]
  );

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="flex w-256 flex-col border-r border-gray-200 bg-gray-50">
        {/* Mode toggle */}
        <div className="border-b border-gray-200 p-16">
          <ModeToggle mode={mode} onModeChange={handleModeChange} />
        </div>

        {/* Session list with grouping */}
        <div className="flex-1 overflow-y-auto p-16">
          {mode === "brainstorm" ? (
            // Date-based grouping for brainstorm mode
            <div className="space-y-16">
              <div>
                <h3 className="mb-8 text-12 font-semibold uppercase text-gray-500">
                  Today
                </h3>
                <div className="space-y-4">
                  {/* Session items would go here */}
                </div>
              </div>
              <div>
                <h3 className="mb-8 text-12 font-semibold uppercase text-gray-500">
                  Yesterday
                </h3>
                <div className="space-y-4">
                  {/* Session items would go here */}
                </div>
              </div>
            </div>
          ) : (
            // Project-based grouping for code mode
            <div className="space-y-16">
              {selectedProject && (
                <div>
                  <div className="mb-8 flex items-center justify-between">
                    <h3 className="text-14 font-semibold text-gray-900">
                      {selectedProject.name}
                    </h3>
                    <button
                      type="button"
                      onClick={() => {
                        fetchProjects();
                        setShowProjectPicker(true);
                      }}
                      aria-label="Change project"
                      className="text-12 text-blue-600 hover:underline"
                    >
                      Change
                    </button>
                  </div>
                  <div className="space-y-4">
                    {/* Session items for this project would go here */}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        {/* Message list */}
        <MessageList
          messages={allMessages}
          isLoading={loadingMessages}
          isStreaming={isStreaming}
          toolCallsById={toolCallsById}
          onRetryTool={retry}
          checkpoints={checkpoints}
        />

        {/* Error banner */}
        {error && (
          <ErrorBanner error={error} onRetry={retry} onDismiss={clearError} />
        )}

        {approvalError && (
          <ErrorBanner
            error={approvalError}
            onDismiss={() => setApprovalError(null)}
          />
        )}

        {/* Projects error */}
        {projectsError && (
          <div className="bg-red-50 p-16 text-center text-14 text-red-600">
            {projectsError}
          </div>
        )}

        {orphanToolCalls.length > 0 && (
          <div className="space-y-12 px-20 py-12">
            {orphanToolCalls.map((toolCall) => (
              <ToolCallCard
                key={toolCall.id}
                toolCall={toolCall}
                onRetry={retry}
              />
            ))}
          </div>
        )}

        {pendingApprovals.length > 0 && (
          <div className="space-y-12 px-20 py-12">
            {pendingApprovals.map((toolCall) => (
              <ToolApprovalCard
                key={toolCall.id}
                toolCall={toolCall}
                onApprove={(remember) =>
                  handleApprovalSubmit(toolCall.id, toolCall.name, true, remember)
                }
                onReject={() =>
                  handleApprovalSubmit(toolCall.id, toolCall.name, false, false)
                }
              />
            ))}
          </div>
        )}

        <div className="bg-white">
          <div className="flex items-center justify-between border-t border-gray-300 px-20 py-10">
            <PermissionsChip
              mode={permissionMode}
              onModeChange={setPermissionMode}
              disabled={isStreaming}
            />
            <ToolBadge
              count={enabledToolCount}
              total={tools.length}
              onClick={() => setToolModalOpen(true)}
              disabled={toolsLoading}
            />
          </div>
          <Composer
            onSend={handleSend}
            isLoading={isStreaming}
            sessionId={sessionId ?? undefined}
          />
        </div>
      </div>

      {/* Project picker modal */}
      <ProjectPicker
        open={showProjectPicker}
        onClose={handleProjectPickerClose}
        onSelectProject={handleSelectProject}
        projects={projects}
        selectedProjectId={selectedProjectId ?? undefined}
      />

      {/* Tool management modal */}
      <ToolManagementModal
        open={toolModalOpen}
        onClose={() => setToolModalOpen(false)}
        tools={tools}
        servers={servers}
        presets={presets}
        onToolToggle={handleToolToggle}
        onPresetSelect={handlePresetSelect}
        onPresetCreate={handlePresetCreate}
        onPresetDelete={handlePresetDelete}
        isLoading={toolsLoading || toolModalLoading}
        error={toolsError ?? toolModalError ?? undefined}
        onRetry={() => {
          fetchTools();
          fetchToolModalData();
        }}
      />
    </div>
  );
}
