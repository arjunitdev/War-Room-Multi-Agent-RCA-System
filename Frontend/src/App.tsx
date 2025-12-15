import { useState } from "react";
import { ChaosSimulator } from "./components/ChaosSimulator";
import { WarRoom } from "./components/WarRoom";
import { AboutSection } from "./components/AboutSection";

export default function App() {
  const [activeTab, setActiveTab] = useState<
    "about" | "chaos" | "war"
  >("about");

  return (
    <div className="min-h-screen bg-[#f5f4f0]">
      {/* Header */}
      <header className="border-b border-black/10 bg-white">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="font-['Courier_Prime',monospace] text-xl tracking-tight">
              sentinel
            </h1>

            {/* CHANGED: Replaced Request Demo with LinkedIn Link */}
            <a
              href="https://www.linkedin.com/in/arjun-selvam/"
              target="_blank"
              rel="noopener noreferrer"
              className="px-6 py-2 bg-black text-white rounded-full hover:bg-black/90 transition-colors text-sm font-medium"
            >
              by Arjun Selvam →
            </a>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-black/10 bg-white/80">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex gap-0">
            {[
              { id: "about" as const, label: "About" },
              {
                id: "chaos" as const,
                label: "Chaos Simulator",
              },
              { id: "war" as const, label: "War Room" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-8 py-4 border-b-2 transition-all text-sm
                  ${
                    activeTab === tab.id
                      ? "border-black text-black"
                      : "border-transparent text-black/50 hover:text-black/70"
                  }
                `}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-8 py-12">
        {activeTab === "about" && <AboutSection />}
        {activeTab === "chaos" && <ChaosSimulator />}
        {activeTab === "war" && <WarRoom />}
      </main>
    </div>
  );
}