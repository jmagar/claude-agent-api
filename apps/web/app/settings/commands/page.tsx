'use client';

import { useState } from 'react';
import { SlashCommandList } from '@/components/commands/SlashCommandList';
import { SlashCommandEditor } from '@/components/commands/SlashCommandEditor';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { SlashCommand } from '@/types';

async function fetchSlashCommands(): Promise<SlashCommand[]> {
  const response = await fetch('/api/slash-commands');
  if (!response.ok) throw new Error('Failed to fetch slash commands');
  const data = await response.json();
  return data.commands || [];
}

async function createSlashCommand(data: Partial<SlashCommand>): Promise<SlashCommand> {
  const response = await fetch('/api/slash-commands', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create slash command');
  const result = await response.json();
  return result.command;
}

async function updateSlashCommand({ id, data }: { id: string; data: Partial<SlashCommand> }): Promise<SlashCommand> {
  const response = await fetch(`/api/slash-commands/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update slash command');
  const result = await response.json();
  return result.command;
}

async function deleteSlashCommand(id: string): Promise<void> {
  const response = await fetch(`/api/slash-commands/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete slash command');
}

export default function SlashCommandsSettingsPage() {
  const queryClient = useQueryClient();

  const { data: commands = [], isLoading, error, refetch } = useQuery({
    queryKey: ['slash-commands'],
    queryFn: fetchSlashCommands,
  });

  const createMutation = useMutation({
    mutationFn: createSlashCommand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['slash-commands'] }),
  });

  const updateMutation = useMutation({
    mutationFn: updateSlashCommand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['slash-commands'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSlashCommand,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['slash-commands'] }),
  });

  const [isCreating, setIsCreating] = useState(false);
  const [editingCommand, setEditingCommand] = useState<SlashCommand | null>(null);

  const handleCreate = () => {
    setIsCreating(true);
    setEditingCommand(null);
  };

  const handleEdit = (command: SlashCommand) => {
    setEditingCommand(command);
    setIsCreating(false);
  };

  const handleSubmit = async (data: Partial<SlashCommand>) => {
    try {
      if (editingCommand) {
        await updateMutation.mutateAsync({ id: editingCommand.id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      setIsCreating(false);
      setEditingCommand(null);
    } catch (err) {
      console.error('Failed to save slash command:', err);
      throw err;
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
    } catch (err) {
      console.error('Failed to delete slash command:', err);
    }
  };

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      await updateMutation.mutateAsync({ id, data: { enabled } });
    } catch (err) {
      console.error('Failed to toggle slash command:', err);
    }
  };

  const handleCancel = () => {
    setIsCreating(false);
    setEditingCommand(null);
  };

  if (isCreating || editingCommand) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <SlashCommandEditor
          command={editingCommand || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Slash Command Management</h1>
        <p className="text-gray-600 mt-2">
          Create and manage custom slash commands for quick actions
        </p>
      </div>

      <SlashCommandList
        commands={commands}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onToggleEnabled={handleToggleEnabled}
        onCreate={handleCreate}
        isLoading={isLoading}
        error={error as Error | undefined}
        onRetry={refetch}
      />
    </div>
  );
}
