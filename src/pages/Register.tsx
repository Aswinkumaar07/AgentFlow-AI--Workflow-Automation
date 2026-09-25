import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Eye, EyeOff, Zap, ArrowRight, Check } from 'lucide-react';
import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useToast } from '../context/ToastContext';

const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
    .regex(/[0-9]/, 'Must contain at least one number'),
  confirmPassword: z.string(),
}).refine(d => d.password === d.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

const fieldVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.07, duration: 0.3 } }),
};

export default function Register() {
  const navigate                = useNavigate();
  const { toast }               = useToast();
  const [showPass, setShowPass] = useState(false);

  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const passValue = watch('password', '');
  const hasMinLen = passValue.length >= 8;
  const hasUpper  = /[A-Z]/.test(passValue);
  const hasNum    = /[0-9]/.test(passValue);

  const onSubmit = async (_data: RegisterFormData) => {
    await new Promise(r => setTimeout(r, 800));
    localStorage.setItem('agentflow-token', 'demo-token');
    toast({ type: 'success', title: 'Account created!', description: 'Welcome to AgentFlow AI Studio' });
    navigate('/builder');
  };

  const signUpAsDemo = () => {
    localStorage.setItem('agentflow-token', 'demo-token');
    toast({ type: 'info', title: 'Instant Access', description: 'Entering demo workspace' });
    navigate('/builder');
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="glass-panel rounded-3xl p-8 sm:p-10 shadow-2xl border border-[var(--border-glass)] relative overflow-hidden"
    >
      {/* Glow highlight pill */}
      <div className="absolute -top-12 -right-12 w-40 h-40 bg-violet-500/15 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="mb-6 text-center sm:text-left">
        <div className="flex items-center justify-center sm:justify-start gap-2.5 mb-6 lg:hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-[var(--text)] font-extrabold font-display text-lg">AgentFlow AI</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[var(--text)] tracking-tight font-display mb-1.5">
          Create your account
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-4)] font-medium">
          Start building autonomous multi-agent pipelines for free
        </p>
      </div>

      {/* Google sign-in */}
      <motion.div custom={0} variants={fieldVariants} initial="hidden" animate="visible">
        <Button
          type="button"
          variant="outline"
          onClick={signUpAsDemo}
          className="w-full gap-3 mb-4 h-11 border-[var(--border-glass)] hover:border-indigo-500/40 font-semibold text-xs"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Sign up with Google
        </Button>
      </motion.div>

      <div className="flex items-center gap-3 mb-4">
        <div className="h-px flex-1 bg-[var(--border-glass)]" />
        <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-5)]">or register with email</span>
        <div className="h-px flex-1 bg-[var(--border-glass)]" />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3.5">
        <motion.div custom={1} variants={fieldVariants} initial="hidden" animate="visible">
          <Label htmlFor="name" className="block mb-1 text-xs font-semibold">Full Name</Label>
          <Input id="name" placeholder="Aswin Kumar" icon={<User className="w-4 h-4 text-[var(--text-4)]" />} error={errors.name?.message} {...register('name')} />
        </motion.div>

        <motion.div custom={2} variants={fieldVariants} initial="hidden" animate="visible">
          <Label htmlFor="email" className="block mb-1 text-xs font-semibold">Email address</Label>
          <Input id="email" type="email" placeholder="you@company.com" icon={<Mail className="w-4 h-4 text-[var(--text-4)]" />} error={errors.email?.message} {...register('email')} />
        </motion.div>

        <motion.div custom={3} variants={fieldVariants} initial="hidden" animate="visible">
          <Label htmlFor="password" className="block mb-1 text-xs font-semibold">Password</Label>
          <div className="relative">
            <Input id="password" type={showPass ? 'text' : 'password'} placeholder="Min. 8 characters" icon={<Lock className="w-4 h-4 text-[var(--text-4)]" />} error={errors.password?.message} {...register('password')} />
            <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3.5 top-3 text-[var(--text-5)] hover:text-[var(--text)] transition-colors p-1">
              {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {/* Password strength visualizer */}
          {passValue.length > 0 && (
            <div className="flex items-center gap-3 mt-1.5 text-[10px] font-medium text-[var(--text-4)]">
              <span className={hasMinLen ? 'text-emerald-400 font-bold flex items-center gap-0.5' : ''}>{hasMinLen && <Check className="w-3 h-3" />} 8+ chars</span>
              <span className={hasUpper ? 'text-emerald-400 font-bold flex items-center gap-0.5' : ''}>{hasUpper && <Check className="w-3 h-3" />} 1 uppercase</span>
              <span className={hasNum ? 'text-emerald-400 font-bold flex items-center gap-0.5' : ''}>{hasNum && <Check className="w-3 h-3" />} 1 number</span>
            </div>
          )}
        </motion.div>

        <motion.div custom={4} variants={fieldVariants} initial="hidden" animate="visible">
          <Label htmlFor="confirmPassword" className="block mb-1 text-xs font-semibold">Confirm Password</Label>
          <Input id="confirmPassword" type="password" placeholder="Repeat password" icon={<Lock className="w-4 h-4 text-[var(--text-4)]" />} error={errors.confirmPassword?.message} {...register('confirmPassword')} />
        </motion.div>

        <motion.div custom={5} variants={fieldVariants} initial="hidden" animate="visible" className="pt-2">
          <Button
            type="submit"
            className="w-full h-11 text-xs font-bold bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] hover:shadow-indigo-500/30 text-white shadow-lg"
            loading={isSubmitting}
          >
            {!isSubmitting && <span className="flex items-center justify-center gap-2">Create Free Workspace <ArrowRight className="w-4 h-4" /></span>}
          </Button>
        </motion.div>
      </form>

      <motion.p custom={6} variants={fieldVariants} initial="hidden" animate="visible" className="text-center text-xs text-[var(--text-4)] mt-5 font-medium">
        Already have an account?{' '}
        <Link to="/login" className="text-[#6366F1] hover:text-[#818CF8] font-bold transition-colors">Sign in</Link>
      </motion.p>
    </motion.div>
  );
}
