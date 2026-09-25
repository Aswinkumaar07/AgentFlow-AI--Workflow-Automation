import { motion } from 'framer-motion';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../ui/accordion';
import { useLandingTheme } from '../../context/LandingThemeContext';

const faqs = [
  { q: 'How does AgentFlow AI generate workflows?',       a: 'AgentFlow uses a multi-agent system: a Planner agent breaks down your natural language request, a RAG-powered Knowledge agent retrieves API documentation, an Executor agent generates the workflow steps, and a Validator agent verifies correctness before execution.' },
  { q: 'Do I need to know how to code?',                  a: 'Not at all. AgentFlow is designed for both technical and non-technical users. Simply describe what you want in plain English and the AI handles everything else.' },
  { q: 'Which APIs and services are supported?',          a: 'AgentFlow ships with 200+ pre-built connectors including GitHub, Slack, Stripe, Notion, Jira, HubSpot, Salesforce, Google Workspace, and many more. You can also add custom API connections.' },
  { q: 'Is my data secure?',                              a: 'Yes. All workflow data is encrypted at rest and in transit. We never store your API credentials in plain text. Enterprise plans include additional compliance features like audit logs and SSO.' },
  { q: 'Can I self-host AgentFlow?',                      a: 'Enterprise plans support self-hosted deployments. Our FastAPI backend is containerized and can be deployed on any cloud provider or on-premises infrastructure.' },
  { q: 'What happens if a workflow execution fails?',     a: 'AgentFlow automatically retries failed steps with exponential backoff. You receive real-time alerts, detailed error logs, and can replay executions from the point of failure.' },
];

export function FAQSection() {
  const { theme } = useLandingTheme();
  const isDark = theme === 'dark';

  const sectionBg  = isDark ? 'rgba(17,24,39,0.2)' : '#FFFFFF';
  const borderCol  = isDark ? '#27272A'             : '#E4E4E7';
  const textPrimary= isDark ? '#F8FAFC'             : '#0F172A';

  return (
    <section id="faq" className="py-24" style={{ backgroundColor: sectionBg, borderTop: `1px solid ${borderCol}` }}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <motion.p initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: '#6366F1' }}>
            FAQ
          </motion.p>
          <motion.h2 initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
            className="text-3xl sm:text-4xl font-bold" style={{ color: textPrimary }}>
            Frequently asked questions
          </motion.h2>
        </div>

        <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}>
          <Accordion type="single" collapsible className="space-y-0">
            {faqs.map((faq, i) => (
              <AccordionItem key={i} value={`faq-${i}`}>
                <AccordionTrigger>{faq.q}</AccordionTrigger>
                <AccordionContent>{faq.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
}
