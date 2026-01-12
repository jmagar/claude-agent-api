/**
 * YAML Frontmatter Validation Utilities
 *
 * Provides proper YAML parsing and validation for agent/skill/command configurations
 * using gray-matter and js-yaml libraries.
 */

import matter from 'gray-matter';
import yaml from 'js-yaml';

/**
 * Parse YAML frontmatter from markdown content
 *
 * @param content - Content with YAML frontmatter
 * @returns Parsed frontmatter and content
 */
export function parseYamlFrontmatter<T = Record<string, unknown>>(content: string): {
  data: T;
  content: string;
  isEmpty: boolean;
  excerpt?: string;
} {
  try {
    const parsed = matter(content);

    return {
      data: parsed.data as T,
      content: parsed.content,
      isEmpty: Object.keys(parsed.data).length === 0,
      excerpt: parsed.excerpt,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse YAML frontmatter: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Validate YAML frontmatter structure
 *
 * @param content - Content with YAML frontmatter
 * @param requiredFields - Array of required field names
 * @returns Validation result
 */
export function validateYamlFrontmatter(
  content: string,
  requiredFields: string[] = []
): {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  data: Record<string, unknown>;
} {
  const errors: string[] = [];
  const warnings: string[] = [];
  let data: Record<string, unknown> = {};

  try {
    const parsed = parseYamlFrontmatter(content);
    data = parsed.data as Record<string, unknown>;

    // Check for required fields
    for (const field of requiredFields) {
      if (!(field in data) || data[field] === undefined || data[field] === '') {
        errors.push(`Required field "${field}" is missing or empty`);
      }
    }

    // Check for empty frontmatter
    if (parsed.isEmpty && requiredFields.length > 0) {
      errors.push('YAML frontmatter is empty');
    }

    // Validate data types for common fields
    if ('name' in data && typeof data.name !== 'string') {
      errors.push('Field "name" must be a string');
    }

    if ('description' in data && typeof data.description !== 'string') {
      errors.push('Field "description" must be a string');
    }

    if ('enabled' in data && typeof data.enabled !== 'boolean') {
      warnings.push('Field "enabled" should be a boolean');
    }

    if ('tools' in data && !Array.isArray(data.tools)) {
      errors.push('Field "tools" must be an array');
    }

    if ('model' in data) {
      const validModels = ['sonnet', 'opus', 'haiku', 'inherit'];
      if (!validModels.includes(data.model as string)) {
        errors.push(`Field "model" must be one of: ${validModels.join(', ')}`);
      }
    }
  } catch (error) {
    errors.push(
      `YAML parsing error: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    data,
  };
}

/**
 * Serialize object to YAML with frontmatter delimiters
 *
 * @param data - Object to serialize
 * @param content - Content to append after frontmatter
 * @returns YAML frontmatter + content
 */
export function serializeYamlFrontmatter(
  data: Record<string, unknown>,
  content: string = ''
): string {
  try {
    const frontmatter = yaml.dump(data, {
      indent: 2,
      lineWidth: 80,
      noRefs: true,
      sortKeys: true,
    });

    return `---\n${frontmatter}---\n${content}`;
  } catch (error) {
    throw new Error(
      `Failed to serialize YAML frontmatter: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}

/**
 * Extract content without frontmatter
 *
 * @param content - Content with YAML frontmatter
 * @returns Content without frontmatter
 */
export function extractContent(content: string): string {
  try {
    const parsed = matter(content);
    return parsed.content;
  } catch {
    // If parsing fails, return original content
    return content;
  }
}

/**
 * Extract frontmatter only
 *
 * @param content - Content with YAML frontmatter
 * @returns Frontmatter data
 */
export function extractFrontmatter<T = Record<string, unknown>>(content: string): T {
  try {
    const parsed = matter(content);
    return parsed.data as T;
  } catch {
    return {} as T;
  }
}

/**
 * Check if content has valid YAML frontmatter
 *
 * @param content - Content to check
 * @returns True if content has valid YAML frontmatter
 */
export function hasValidYamlFrontmatter(content: string): boolean {
  try {
    const parsed = matter(content);
    return !parsed.isEmpty && Object.keys(parsed.data).length > 0;
  } catch {
    return false;
  }
}

/**
 * Merge frontmatter with new data
 *
 * @param content - Original content with frontmatter
 * @param newData - New data to merge
 * @returns Updated content with merged frontmatter
 */
export function mergeFrontmatter(
  content: string,
  newData: Record<string, unknown>
): string {
  try {
    const parsed = matter(content);
    const mergedData = { ...parsed.data, ...newData };
    return serializeYamlFrontmatter(mergedData, parsed.content);
  } catch (error) {
    throw new Error(
      `Failed to merge frontmatter: ${error instanceof Error ? error.message : 'Unknown error'}`
    );
  }
}
