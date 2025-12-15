import React from 'react';
import { Shield, Brain, Clock, Network, Database, Code, Gavel, CheckCircle2, Server, Zap, Lock } from 'lucide-react';
import workflowIllustration from '../assets/workflow-illustration.png';

export function AboutSection() {
  const workflowSteps = [
    {
      number: '1',
      title: 'Sequential Chaos Injection',
      description: 'The Simulator doesn\'t just break things; it creates realistic, time-delayed failure narratives. A root cause event is fired at T+0s, followed by cascading symptomatic faults at T+2s, T+5s, etc.',
      icon: <Zap className="w-5 h-5 text-white" />,
      checklist: [
        'Define Root Cause Trigger (T+0s)',
        'Inject Downstream Symptoms with Delays',
        'Simulate Realistic Propagation Time',
        'Standardized Payload Delivery'
      ]
    },
    {
      number: '2',
      title: 'Blind Specialist Analysis',
      description: 'Logs are routed to isolated AI agents. The Database Agent sees *only* DB metrics; the Network Agent sees *only* transport logs. This total isolation prevents "alert panic" and groupthink bias.',
      icon: <Shield className="w-5 h-5 text-white" />,
      checklist: [
        'DBA Agent analyzes Locks & State',
        'Network Agent analyzes Latency & 504s',
        'Application Agent analyzes Logic & Config',
        'Strict Data Isolation Enforcement'
      ]
    },
    {
      number: '3',
      title: 'Judge Synthesis & Temporal Forensics',
      description: 'The Principal Judge Agent receives the independent reports. Its primary mechanism is analyzing the "T+" timestamps to mathematically identify the "First Mover" event, separating the trigger from the noise.',
      icon: <Gavel className="w-5 h-5 text-white" />,
      checklist: [
        'Analyze T+ Timeline Offsets',
        'Apply Causal Precedence Logic',
        'Rule Out Downstream Symptoms',
        'Determine Definitive Root Cause'
      ]
    },
    {
      number: '4',
      title: 'Actionable Remediation',
      description: 'Instead of generic advice like "check the database," the system outputs specific, technical fixes based on the exact mechanism identified (e.g., "Wrap the JSON parser in `src/api.py` with a try/finally block").',
      icon: <CheckCircle2 className="w-5 h-5 text-white" />,
      checklist: [
        'Pinpoint Root Cause Component',
        'Suggest Specific Code/Config Fixes',
        'Verify against SRE Best Practices',
        'Generate Executive Summary'
      ]
    }
  ];

  const coreConcepts = [
    {
      title: 'The "Blind Specialist" Model',
      description: 'In a real War Room, human biases lead to the "blame game." If the network engineer panics, everyone panics. By forcing agents to work in total isolation, we guarantee unbiased, purely evidence-based reporting from each domain.',
      icon: <Brain className="w-6 h-6 text-black" />
    },
    {
      title: 'Causal Precedence Hierarchy',
      description: 'Infrastructure rarely breaks on its own. Sentinel uses a strict decision tree: Application Logic drives Database State, which drives Network Transport. This prevents blaming AWS latency when a bad application query is the actual culprit.',
      icon: <Server className="w-6 h-6 text-black" />
    },
    {
      title: 'Temporal Forensics (T+0s)',
      description: 'Root cause is a function of time. The Sentinel engine timestamps every signal. The event that occurs at T+0s is mathematically identified as the trigger that started the cascade.',
      icon: <Clock className="w-6 h-6 text-black" />
    }
  ];

  const stack = [
    { label: 'Backend', value: 'Python 3.10+ / FastAPI (Async)' },
    { label: 'AI Engine', value: 'Google Gemini 1.5 Pro' },
    { label: 'Data Store', value: 'SQLite (Embedded, Low-Latency)' },
    { label: 'Validation', value: 'Pydantic Strict Schemas' },
    { label: 'Concurrency', value: 'ThreadPoolExecutor' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-16 pb-12">
      {/* Hero Section */}
      <div className="text-center space-y-6">
        <h2 className="text-4xl font-bold tracking-tight">
          Autonomous Root Cause Analysis.
          <br />
          <span className="text-black/60">Separating Signal from Noise.</span>
        </h2>
        <p className="text-lg text-black/70 leading-relaxed max-w-3xl mx-auto">
          Sentinel is an incident response platform designed to solve "Alert Fatigue" in distributed systems. It uses a novel <strong>Multi-Agent "Blind Specialist" Architecture</strong> to deconstruct complex, cascading failures and identify the single true root cause within seconds.
        </p>
      </div>

      {/* The Problem / Solution Contrast */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-red-50/50 border border-red-100 rounded-2xl p-8 space-y-4 flex flex-col">
          <div>
              <h3 className="text-xl font-semibold flex items-center gap-2 text-red-900">
                <Lock className="w-5 h-5" /> The Current Reality
              </h3>
              <p className="text-black/70 leading-relaxed mt-4">
                One bad database query can lock up an entire table. Seconds later, your site slows down, and error messages start piling up. Your monitoring tools start shouting about network and database problems at the same time. Everyone panics in the "War Room," and it takes hours of digging through logs to find the one query that started it all.
              </p>
          </div>
        </div>
        <div className="bg-emerald-50/50 border border-emerald-100 rounded-2xl p-8 space-y-4">
          <h3 className="text-xl font-semibold flex items-center gap-2 text-emerald-900">
            <Shield className="w-5 h-5" /> The Sentinel Approach
          </h3>
          <p className="text-black/70 leading-relaxed">
            Sentinel ingests the entire failure stream. It assigns specialized AI agents to analyze the Network, Database, and Application layers in isolation. A "Judge" agent then reconstructs the timeline using forensic timestamps to deliver a final verdict: <em>"The network didn't fail; an application logic error caused a deadlock at T+0s."</em>
          </p>
        </div>
      </div>

      {/* Workflow Illustration */}
      <div className="flex justify-center my-12">
        <img 
          src={workflowIllustration}
          alt="Developer troubleshooting complex system issues with multiple monitors showing code, architecture diagrams, and incident alerts"
          className="max-w-4xl w-full h-auto rounded-2xl shadow-lg"
        />
      </div>

      {/* Workflow Steps */}
      <div className="space-y-8">
        <div className="text-center">
          <h3 className="text-2xl font-bold">The Incident Analysis Workflow</h3>
          <p className="text-black/60 mt-2">From controlled chaos to definitive verdict</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {workflowSteps.map((step) => (
            <div key={step.number} className="bg-white border border-black/10 rounded-2xl p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center flex-shrink-0 shadow-sm">
                  {step.icon}
                </div>
                <div className="space-y-3 flex-1">
                  <div>
                    <h4 className="text-lg font-semibold flex items-center gap-2">
                      <span className="text-black/40 font-mono">0{step.number}.</span> {step.title}
                    </h4>
                  </div>
                  <p className="text-black/70 text-sm leading-relaxed">
                    {step.description}
                  </p>
                  <div className="pt-2 space-y-2">
                    {step.checklist.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs font-medium text-black/60">
                        <CheckCircle2 className="w-3.5 h-3.5 text-black/40" />
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Core Concepts - The "Secret Sauce" */}
      <div className="space-y-8 bg-[#f5f4f0] p-8 rounded-3xl border border-black/5">
        <div className="text-center">
          <h3 className="text-2xl font-bold">Core Architectural Concepts</h3>
          <p className="text-black/60 mt-2">Designed to eliminate bias and hallucinations in AI reasoning</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {coreConcepts.map((concept, idx) => (
            <div key={idx} className="space-y-4 text-center md:text-left">
              <div className="bg-white w-12 h-12 rounded-2xl border border-black/10 flex items-center justify-center mx-auto md:mx-0 shadow-sm">
                {concept.icon}
              </div>
              <h4 className="text-lg font-semibold">{concept.title}</h4>
              <p className="text-black/70 text-sm leading-relaxed">
                {concept.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Technical Stack Footer */}
      <div className="border-t border-black/10 pt-12">
        <h3 className="text-sm font-bold text-black/40 uppercase tracking-wider mb-6 text-center">Engine Technical Stack</h3>
        <div className="flex flex-wrap justify-center gap-x-12 gap-y-4">
          {stack.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 text-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-black/40" />
              <span className="text-black/60">{item.label}:</span>
              <span className="font-medium text-black/80">{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}