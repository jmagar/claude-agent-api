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
import { useQuery } from "@tanstack/react-query";
import { ModeToggle } from "@/components/sidebar/ModeToggle";
import { ProjectPicker } from "@/components/modals/ProjectPickerModal";
import { useMode } from "@/contexts/ModeContext";
import type { Message, Project, SessionMode } from "@/types";

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

  // Mode context - provides mode state and persistence
  let modeContext: {
    mode: SessionMode;
    selectedProjectId: string | null;
    selectedProject: Project | null;
    setMode: (mode: SessionMode) => void;
    setSelectedProjectId: (id: string | null) => void;
    setSelectedProject: (project: Project | null) => void;
  } | null = null;

  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    modeContext = useMode();
  } catch {
    // ModeProvider not available, use local state
  }

  const [localMode, setLocalMode] = useState<SessionMode>("brainstorm");
  const [localSelectedProjectId, setLocalSelectedProjectId] = useState<string | null>(null);
  const [localSelectedProject, setLocalSelectedProject] = useState<Project | null>(null);

  const mode = modeContext?.mode ?? localMode;
  const selectedProjectId = modeContext?.selectedProjectId ?? localSelectedProjectId;
  const selectedProject = modeContext?.selectedProject ?? localSelectedProject;
  const setMode = modeContext?.setMode ?? setLocalMode;
  const setSelectedProjectId = modeContext?.setSelectedProjectId ?? setLocalSelectedProjectId;
  const setSelectedProject = modeContext?.setSelectedProject ?? setLocalSelectedProject;

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

  // Fetch projects when needed
  const fetchProjects = useCallback(async () => {
    try {
      const response = await fetch("/api/projects");
      if (!response.ok) {
        throw new Error("Failed to load projects");
      }
      const data = await response.json();
      setProjects(data);
      setProjectsError(null);
      return data as Project[];
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

  // Merge existing messages with stream messages
  const [allMessages, setAllMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (existingMessages?.messages) {
      setAllMessages(existingMessages.messages);
      setLoadingMessages(false);
    }
  }, [existingMessages]);

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
  }, [streamMessages]);

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
        />

        {/* Error banner */}
        {error && (
          <ErrorBanner error={error} onRetry={retry} onDismiss={clearError} />
        )}

        {/* Projects error */}
        {projectsError && (
          <div className="bg-red-50 p-16 text-center text-14 text-red-600">
            {projectsError}
          </div>
        )}

        {/* Composer */}
        <Composer
          onSend={handleSend}
          isLoading={isStreaming}
          sessionId={sessionId ?? undefined}
        />
      </div>

      {/* Project picker modal */}
      <ProjectPicker
        open={showProjectPicker}
        onClose={handleProjectPickerClose}
        onSelectProject={handleSelectProject}
        projects={projects}
        selectedProjectId={selectedProjectId ?? undefined}
      />
    </div>
  );
}
