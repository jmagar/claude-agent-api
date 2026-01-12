/**
 * Tools API route tests
 */

import { GET } from '@/app/api/tools/route';

describe('GET /api/tools', () => {
  it('returns the built-in tool catalog', async () => {
    const response = await GET();
    const data = await response.json();

    expect(Array.isArray(data.tools)).toBe(true);
    expect(data.tools).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'Read', enabled: true }),
        expect.objectContaining({ name: 'Write', enabled: true }),
      ])
    );
  });
});
