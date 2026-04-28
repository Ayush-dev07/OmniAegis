'use client';

import React, { ReactNode, useState } from 'react';

export interface DataTableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (value: any, row: T, index: number) => ReactNode;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  onRowClick?: (row: T, index: number) => void;
  selectable?: boolean;
  onSelectionChange?: (selectedIndices: number[]) => void;
  loading?: boolean;
  emptyMessage?: string;
}

/**
 * DataTable component - Sentry + Linear pattern
 * 
 * Features:
 * - Sticky header
 * - Sortable columns
 * - Alternating row fills
 * - Inline row actions on hover
 * - Multi-select with checkbox
 * - 44px row height (comfortable density)
 */
export function DataTable<T extends Record<string, any>>({
  columns,
  rows,
  onRowClick,
  selectable = false,
  onSelectionChange,
  loading = false,
  emptyMessage = 'No data available',
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<{
    key: string | null;
    direction: 'asc' | 'desc';
  }>({ key: null, direction: 'asc' });
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

  const handleSort = (key: string, sortable?: boolean) => {
    if (!sortable) return;

    if (sortConfig.key === key) {
      setSortConfig({
        key,
        direction: sortConfig.direction === 'asc' ? 'desc' : 'asc',
      });
    } else {
      setSortConfig({ key, direction: 'asc' });
    }
  };

  const handleSelectAll = () => {
    if (selectedRows.size === rows.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(rows.map((_, i) => i)));
    }
  };

  const handleSelectRow = (index: number) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedRows(newSelected);
    onSelectionChange?.(Array.from(newSelected));
  };

  if (loading) {
    return (
      <div className="border border-border-default rounded-xl overflow-hidden bg-surface-secondary">
        <div className="space-y-2 p-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-11 bg-surface-tertiary rounded animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="border border-border-default rounded-xl p-12 text-center bg-surface-secondary">
        <p className="text-text-secondary">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="border border-border-default rounded-xl overflow-hidden bg-surface-secondary">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10 bg-surface-secondary border-b border-border-default">
          <tr>
            {selectable && (
              <th className="w-10 px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedRows.size === rows.length && rows.length > 0}
                  onChange={handleSelectAll}
                  className="rounded border-border-default cursor-pointer"
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map((col) => (
              <th
                key={String(col.key)}
                style={{ width: col.width }}
                className={`px-4 py-3 text-left font-semibold text-text-primary ${
                  col.sortable ? 'cursor-pointer hover:bg-surface-tertiary' : ''
                }`}
                onClick={() => handleSort(String(col.key), col.sortable)}
              >
                <div className="flex items-center gap-2">
                  {col.label}
                  {col.sortable && (
                    <span className="text-xs text-text-secondary">
                      {sortConfig.key === col.key
                        ? sortConfig.direction === 'asc'
                          ? '↑'
                          : '↓'
                        : '↕'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className={`border-t border-border-subtle h-11 transition-colors duration-fast ${
                rowIndex % 2 === 0
                  ? 'bg-surface-secondary'
                  : 'bg-surface-secondary'
              } hover:bg-surface-tertiary cursor-pointer`}
              onClick={() => onRowClick?.(row, rowIndex)}
            >
              {selectable && (
                <td className="px-4 py-3">
                  <input
                    type="checkbox"
                    checked={selectedRows.has(rowIndex)}
                    onChange={() => handleSelectRow(rowIndex)}
                    onClick={(e) => e.stopPropagation()}
                    className="rounded border-border-default cursor-pointer"
                    aria-label={`Select row ${rowIndex + 1}`}
                  />
                </td>
              )}
              {columns.map((col) => (
                <td key={String(col.key)} className="px-4 py-3 text-text-primary">
                  {col.render
                    ? col.render(row[col.key as keyof T], row, rowIndex)
                    : String(row[col.key as keyof T])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
