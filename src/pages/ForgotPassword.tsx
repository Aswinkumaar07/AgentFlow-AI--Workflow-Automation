import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Zap, CheckCircle } from 'lucide-react';
import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

const schema = z.object({
  email: z.string().email('Invalid email address'),
});
type FormData = z.infer<typeof schema>;

export default function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (_data: FormData) => {
    await new Promise(r => setTimeout(r, 800));
    setSent(true);
  };

  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="w-full">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#6366F1] to-[#8B5CF6] flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-[#F8FAFC] font-bold">AgentFlow AI</span>
        </div>
        <h1 className="text-2xl font-bold text-[#F8FAFC] mb-1">Reset your password</h1>
        <p className="text-sm text-[#94A3B8]">We'll send a reset link to your email address</p>
      </div>

      {sent ? (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
          <div className="w-16 h-16 rounded-2xl bg-[#22C55E]/10 border border-[#22C55E]/30 flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-[#22C55E]" />
          </div>
          <h3 className="text-lg font-semibold text-[#F8FAFC] mb-2">Check your email</h3>
          <p className="text-sm text-[#94A3B8] mb-6">We've sent a password reset link to your inbox. The link expires in 1 hour.</p>
          <Link to="/login"><Button variant="outline" className="gap-2"><ArrowLeft className="w-4 h-4" />Back to Sign in</Button></Link>
        </motion.div>
      ) : (
        <>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mb-4">
            <div>
              <Label htmlFor="email" className="block mb-1.5">Email address</Label>
              <Input id="email" type="email" placeholder="you@example.com" icon={<Mail className="w-4 h-4" />} error={errors.email?.message} {...register('email')} />
            </div>
            <Button type="submit" className="w-full h-11" loading={isSubmitting}>
              {!isSubmitting && 'Send reset link'}
            </Button>
          </form>
          <Link to="/login" className="flex items-center justify-center gap-1.5 text-sm text-[#64748B] hover:text-[#94A3B8] transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign in
          </Link>
        </>
      )}
    </motion.div>
  );
}
