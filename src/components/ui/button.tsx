import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FF6D00] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0E0918] disabled:pointer-events-none disabled:opacity-50 select-none cursor-pointer',
  {
    variants: {
      variant: {
        default:   'bg-gradient-to-r from-[#FF6D00] to-[#FF0C00] text-white shadow-[0_4px_20px_rgba(255,109,0,0.35)] hover:shadow-[0_6px_24px_rgba(255,109,0,0.50)] hover:brightness-110 active:scale-[0.96] font-semibold',
        secondary: 'bg-[#1B1728]/80 text-white border border-[rgba(255,255,255,0.12)] hover:bg-[#231E3A] hover:border-[#FF6D00]/40 active:scale-[0.96] backdrop-blur-md',
        outline:   'border border-[rgba(255,255,255,0.12)] bg-[#1B1728]/40 backdrop-blur-md text-[rgba(255,255,255,0.85)] hover:bg-[#231E3A] hover:border-[#FF6D00]/50 hover:text-white active:scale-[0.96]',
        ghost:     'text-[rgba(255,255,255,0.60)] hover:text-white hover:bg-[#231E3A]/60 backdrop-blur-sm active:scale-[0.96]',
        danger:    'bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 hover:bg-[#EF4444]/25 hover:border-[#EF4444]/50 active:scale-[0.96]',
        gradient:  'bg-gradient-to-r from-[#FF6D00] via-[#FF0C00] to-[#FF802C] text-white shadow-[0_4px_20px_rgba(255,109,0,0.35)] hover:brightness-110 active:scale-[0.96] font-semibold',
        link:      'text-[#FF6D00] underline-offset-4 hover:underline p-0 h-auto',
      },
      size: {
        sm:   'h-8 px-3 text-xs gap-1.5 rounded-lg',
        md:   'h-10 px-4 py-2',
        lg:   'h-11 px-6 text-base rounded-xl',
        xl:   'h-12 px-8 text-base rounded-xl',
        icon: 'h-9 w-9 rounded-xl',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} disabled={disabled || loading} {...props}>
        {loading && <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />}
        {children}
      </Comp>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
