import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Home, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
      <div className="absolute inset-0 hero-gradient" />
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative text-center px-4"
      >
        <div className="text-[120px] font-bold gradient-text leading-none mb-4">404</div>
        <h1 className="text-2xl font-bold text-[#F8FAFC] mb-2">Page not found</h1>
        <p className="text-[#94A3B8] mb-8 max-w-sm mx-auto">The page you're looking for doesn't exist or has been moved.</p>
        <div className="flex gap-3 justify-center">
          <Link to="/"><Button variant="outline" className="gap-2"><Home className="w-4 h-4" />Go Home</Button></Link>
          <Link to="/dashboard"><Button className="gap-2"><Zap className="w-4 h-4" />Dashboard</Button></Link>
        </div>
      </motion.div>
    </div>
  );
}
