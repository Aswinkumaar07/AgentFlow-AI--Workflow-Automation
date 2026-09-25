import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import type { WorkflowStatus } from '../../types';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-[#FF6D00]/15 text-[#FF9E43] border-[#FF6D00]/30',
        success: 'bg-[#22C55E]/15 text-[#4ADE80] border-[#22C55E]/30',
        running: 'bg-[#06B6D4]/15 text-[#38BDF8] border-[#06B6D4]/30',
        pending: 'bg-[#F59E0B]/15 text-[#FCD34D] border-[#F59E0B]/30',
        error: 'bg-[#EF4444]/15 text-[#F87171] border-[#EF4444]/30',
        cancelled: 'bg-[#71717A]/15 text-[#A1A1AA] border-[#71717A]/30',
        outline: 'bg-transparent border-[rgba(255,255,255,0.12)] text-[rgba(255,255,255,0.70)]',
        secondary: 'bg-[#A855F7]/15 text-[#C084FC] border-[#A855F7]/30',
      },
    },
    defaultVariants: { variant: 'default' },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
  status?: WorkflowStatus;
}

function Badge({ className, variant, dot, status, children, ...props }: BadgeProps) {
  const dotColors: Record<string, string> = {
    success: 'bg-[#22C55E]',
    running: 'bg-[#06B6D4] animate-pulse',
    pending: 'bg-[#F59E0B]',
    error: 'bg-[#EF4444]',
    cancelled: 'bg-[#71717A]',
    default: 'bg-[#FF6D00]',
  };

  type VariantKey = NonNullable<Parameters<typeof badgeVariants>[0]>['variant'];
  const resolvedVariant = (status ?? variant ?? 'default') as VariantKey;

  return (
    <span
      className={cn(badgeVariants({ variant: resolvedVariant }), className)}
      {...props}
    >
      {dot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[resolvedVariant as string] ?? dotColors.default)} />}
      {children}
    </span>
  );
}

export { Badge, badgeVariants };
