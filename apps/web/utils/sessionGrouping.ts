/**
 * Session grouping utilities for sidebar organization
 *
 * Provides functions to group sessions by:
 * - Date (for Brainstorm mode): Today, Yesterday, This Week, Older
 * - Project (for Code mode): Group sessions by their project_id
 *
 * @see FR-011: Brainstorm mode with date-grouped sidebar
 * @see FR-012: Code mode with project-grouped sidebar
 */

import type { Session, Project } from "@/types";

/**
 * Date group labels for brainstorm mode sidebar
 */
export type DateGroupLabel = "Today" | "Yesterday" | "This Week" | "Older";

/**
 * A group of sessions organized by date
 */
export interface DateGroup {
  /** Display label for the group */
  label: DateGroupLabel;
  /** Sessions in this group, sorted by last_message_at descending */
  sessions: Session[];
}

/**
 * A group of sessions organized by project
 */
export interface ProjectGroup {
  /** The project these sessions belong to */
  project: Project;
  /** Sessions in this project, sorted by last_message_at descending */
  sessions: Session[];
}

/**
 * Check if two dates are the same calendar day
 */
function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
}

/**
 * Check if a date is yesterday relative to the reference date
 */
function isYesterday(date: Date, reference: Date): boolean {
  const yesterday = new Date(reference);
  yesterday.setDate(yesterday.getDate() - 1);
  return isSameDay(date, yesterday);
}

/**
 * Check if a date is within the last 7 days (excluding today and yesterday)
 */
function isThisWeek(date: Date, reference: Date): boolean {
  const weekAgo = new Date(reference);
  weekAgo.setDate(weekAgo.getDate() - 7);
  const yesterday = new Date(reference);
  yesterday.setDate(yesterday.getDate() - 1);

  return date > weekAgo && date < yesterday && !isSameDay(date, yesterday);
}

/**
 * Get the date group label for a given date
 */
export function getDateGroupLabel(date: Date, reference: Date = new Date()): DateGroupLabel {
  if (isSameDay(date, reference)) {
    return "Today";
  }
  if (isYesterday(date, reference)) {
    return "Yesterday";
  }
  if (isThisWeek(date, reference)) {
    return "This Week";
  }
  return "Older";
}

/**
 * Group sessions by date for brainstorm mode sidebar
 *
 * Sessions are grouped into: Today, Yesterday, This Week, Older
 * Within each group, sessions are sorted by last_message_at (newest first)
 *
 * @param sessions - Array of sessions to group
 * @param referenceDate - Date to use as "now" (defaults to current date)
 * @returns Array of date groups with their sessions
 */
export function groupSessionsByDate(
  sessions: Session[],
  referenceDate: Date = new Date()
): DateGroup[] {
  const groups: Record<DateGroupLabel, Session[]> = {
    "Today": [],
    "Yesterday": [],
    "This Week": [],
    "Older": [],
  };

  // Group sessions
  for (const session of sessions) {
    const sessionDate = session.last_message_at
      ? new Date(session.last_message_at)
      : new Date(session.created_at);
    const label = getDateGroupLabel(sessionDate, referenceDate);
    groups[label].push(session);
  }

  // Sort sessions within each group (newest first)
  const sortByDate = (a: Session, b: Session) => {
    const dateA = a.last_message_at ? new Date(a.last_message_at) : new Date(a.created_at);
    const dateB = b.last_message_at ? new Date(b.last_message_at) : new Date(b.created_at);
    return dateB.getTime() - dateA.getTime();
  };

  for (const label of Object.keys(groups) as DateGroupLabel[]) {
    groups[label].sort(sortByDate);
  }

  // Return only non-empty groups in order
  const orderedLabels: DateGroupLabel[] = ["Today", "Yesterday", "This Week", "Older"];
  return orderedLabels
    .filter((label) => groups[label].length > 0)
    .map((label) => ({
      label,
      sessions: groups[label],
    }));
}

/**
 * Group sessions by project for code mode sidebar
 *
 * Sessions are grouped by their project_id
 * Within each group, sessions are sorted by last_message_at (newest first)
 * Projects are sorted by most recent session activity
 *
 * @param sessions - Array of sessions to group (should be filtered to code mode sessions)
 * @param projects - Map of project ID to project object
 * @returns Array of project groups with their sessions
 */
export function groupSessionsByProject(
  sessions: Session[],
  projects: Map<string, Project>
): ProjectGroup[] {
  const groups = new Map<string, Session[]>();

  // Group sessions by project_id
  for (const session of sessions) {
    if (!session.project_id) continue;

    const existing = groups.get(session.project_id) ?? [];
    existing.push(session);
    groups.set(session.project_id, existing);
  }

  // Sort sessions within each group (newest first)
  const sortByDate = (a: Session, b: Session) => {
    const dateA = a.last_message_at ? new Date(a.last_message_at) : new Date(a.created_at);
    const dateB = b.last_message_at ? new Date(b.last_message_at) : new Date(b.created_at);
    return dateB.getTime() - dateA.getTime();
  };

  for (const sessionList of groups.values()) {
    sessionList.sort(sortByDate);
  }

  // Build project groups and sort by most recent activity
  const projectGroups: ProjectGroup[] = [];

  for (const [projectId, sessionList] of groups) {
    const project = projects.get(projectId);
    if (project) {
      projectGroups.push({
        project,
        sessions: sessionList,
      });
    }
  }

  // Sort project groups by most recent session activity
  projectGroups.sort((a, b) => {
    const latestA = a.sessions[0];
    const latestB = b.sessions[0];
    const dateA = latestA?.last_message_at
      ? new Date(latestA.last_message_at)
      : new Date(latestA?.created_at ?? 0);
    const dateB = latestB?.last_message_at
      ? new Date(latestB.last_message_at)
      : new Date(latestB?.created_at ?? 0);
    return dateB.getTime() - dateA.getTime();
  });

  return projectGroups;
}

/**
 * Filter sessions by mode
 *
 * @param sessions - All sessions
 * @param mode - The mode to filter by
 * @returns Sessions matching the specified mode
 */
export function filterSessionsByMode(
  sessions: Session[],
  mode: "brainstorm" | "code"
): Session[] {
  return sessions.filter((session) => session.mode === mode);
}
