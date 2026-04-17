import React from 'react';
import Skeleton from '@mui/material/Skeleton';
import Box from '@mui/material/Box';

/**
 * LoadingFallback - Skeleton loading state for Suspense fallback
 *
 * Shows a placeholder layout while components are loading.
 * Uses MUI Skeleton for a smooth loading experience.
 */
export default function LoadingFallback() {
  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header skeleton */}
      <Box sx={{ mb: 4 }}>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="text" width={300} height={24} />
      </Box>

      {/* Content skeleton */}
      <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Sidebar skeleton (desktop only) */}
        <Box sx={{ display: { xs: 'none', md: 'block' }, width: 240 }}>
          <Skeleton variant="rectangular" height={40} sx={{ mb: 1 }} />
          <Skeleton variant="rectangular" height={40} sx={{ mb: 1 }} />
          <Skeleton variant="rectangular" height={40} sx={{ mb: 1 }} />
          <Skeleton variant="rectangular" height={40} sx={{ mb: 1 }} />
          <Skeleton variant="rectangular" height={40} />
        </Box>

        {/* Main content skeleton */}
        <Box sx={{ flex: 1 }}>
          {/* Table/card skeleton */}
          <Box sx={{ mb: 3 }}>
            <Skeleton variant="rectangular" height={56} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={56} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={56} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={56} sx={{ mb: 1 }} />
            <Skeleton variant="rectangular" height={56} />
          </Box>

          {/* Pagination skeleton */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} />
            <Skeleton variant="circular" width={32} height={32} />
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

/**
 * PageSkeleton - Simple skeleton for a single page view
 */
export function PageSkeleton({ rows = 5 }) {
  return (
    <Box sx={{ p: 3 }}>
      <Skeleton variant="text" width="40%" height={40} sx={{ mb: 3 }} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={64} sx={{ mb: 1 }} />
      ))}
    </Box>
  );
}

/**
 * CardSkeleton - Skeleton for card-based layouts
 */
export function CardSkeleton({ count = 3 }) {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', p: 2 }}>
      {Array.from({ length: count }).map((_, i) => (
        <Box key={i} sx={{ width: { xs: '100%', sm: 'calc(50% - 8px)', md: 'calc(33% - 11px)' } }}>
          <Skeleton variant="rectangular" height={140} />
          <Skeleton variant="text" width="60%" sx={{ mt: 1 }} />
          <Skeleton variant="text" width="40%" />
        </Box>
      ))}
    </Box>
  );
}

/**
 * FormSkeleton - Skeleton for form pages
 */
export function FormSkeleton({ fields = 4 }) {
  return (
    <Box sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Skeleton variant="text" width="50%" height={36} sx={{ mb: 3 }} />
      {Array.from({ length: fields }).map((_, i) => (
        <Skeleton key={i} variant="rectangular" height={56} sx={{ mb: 2 }} />
      ))}
      <Skeleton variant="rectangular" height={44} sx={{ mt: 2 }} />
    </Box>
  );
}
