import Navbar from '@/components/layout/Navbar';
import Hero from '@/components/layout/Hero';
import AgentsSection from '@/components/layout/AgentsSection';
import Footer from '@/components/layout/Footer';

export default function Home() {
  return (
    <main className="min-h-screen selection:bg-cyan-500/30">
      <Navbar />
      <Hero />
      <AgentsSection />
      <Footer />
    </main>
  );
}
