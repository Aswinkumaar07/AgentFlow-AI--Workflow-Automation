import { LandingThemeProvider } from '../context/LandingThemeContext';
import { LandingNavbar } from '../components/landing/LandingNavbar';
import { HeroSection } from '../components/landing/HeroSection';
import { TrustBadges } from '../components/landing/TrustBadges';
import { FeaturesSection } from '../components/landing/FeaturesSection';
import { HowItWorks } from '../components/landing/HowItWorks';
import { Testimonials } from '../components/landing/Testimonials';
import { PricingSection } from '../components/landing/PricingSection';
import { FAQSection } from '../components/landing/FAQSection';
import { CTASection } from '../components/landing/CTASection';
import { Footer } from '../components/landing/Footer';

export default function Landing() {
  return (
    <LandingThemeProvider>
      <div
        className="min-h-screen transition-colors duration-300"
        style={{ backgroundColor: 'var(--bg)', color: 'var(--text)' }}
      >
        <LandingNavbar />
        <HeroSection />
        <TrustBadges />
        <FeaturesSection />
        <HowItWorks />
        <Testimonials />
        <PricingSection />
        <FAQSection />
        <CTASection />
        <Footer />
      </div>
    </LandingThemeProvider>
  );
}
