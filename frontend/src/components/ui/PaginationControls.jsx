import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';

/**
 * PaginationControls — Server-side pagination controls for DRF paginated responses.
 * Displays record range, page info, and Previous/Next navigation.
 *
 * Props:
 *   currentPage   - Current 1-indexed page number
 *   pageSize      - Number of records per page (default: 20)
 *   totalCount    - Total number of records from DRF `count` field
 *   onPageChange  - Callback invoked with new page number
 *   loading       - If true, disables navigation buttons
 */
export function PaginationControls({
  currentPage = 1,
  pageSize = 20,
  totalCount = 0,
  onPageChange,
  loading = false,
}) {
  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const startRecord = totalCount === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endRecord = Math.min(currentPage * pageSize, totalCount);

  const hasPrev = currentPage > 1;
  const hasNext = currentPage < totalPages;

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 0',
        marginTop: '8px',
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      {/* Record range */}
      <span
        style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          whiteSpace: 'nowrap',
        }}
      >
        {totalCount === 0
          ? 'No records'
          : `Showing ${startRecord}–${endRecord} of ${totalCount} records`}
      </span>

      {/* Page navigation */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span
          className="font-mono"
          style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            fontWeight: 600,
            whiteSpace: 'nowrap',
          }}
        >
          Page {currentPage} of {totalPages}
        </span>

        <Button
          variant="secondary"
          size="small"
          icon={ChevronLeft}
          disabled={!hasPrev || loading}
          onClick={() => onPageChange(currentPage - 1)}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="small"
          icon={ChevronRight}
          disabled={!hasNext || loading}
          onClick={() => onPageChange(currentPage + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
