import FeatureCards from "../components/landing/FeatureCards";
import Footer from "../components/landing/Footer";
import Hero from "../components/landing/Hero";
import HowItWorks from "../components/landing/HowItWorks";
import Navbar from "../components/landing/Navbar";

export default function Landing() {
  return (
    <div className="app-bg min-h-screen">
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <FeatureCards />
      </main>
      <Footer />
    </div>
  );
}
