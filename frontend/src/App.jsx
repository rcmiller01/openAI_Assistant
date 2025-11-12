import React, { useState } from 'react';

const ChipGroup = ({ options, defaultSelected }) => {
  const [selected, setSelected] = useState(defaultSelected ?? options[0]);

  return (
    <div className="chip-group" role="group">
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className={`chip${selected === option ? ' selected' : ''}`}
          onClick={() => setSelected(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
};

const AccordionSection = ({
  id,
  title,
  description,
  isActive,
  onActivate,
  children,
}) => (
  <article
    className={`accordion-item${isActive ? ' active' : ''}`}
    data-section={id}
  >
    <button
      className="accordion-trigger"
      type="button"
      id={`trigger-${id}`}
      aria-controls={`panel-${id}`}
      aria-expanded={isActive}
      onClick={() => {
        if (!isActive) {
          onActivate(id);
        }
      }}
    >
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <span className="chevron">▾</span>
    </button>
    <div
      className="accordion-panel"
      id={`panel-${id}`}
      role="region"
      aria-labelledby={`trigger-${id}`}
      hidden={!isActive}
    >
      {children}
    </div>
  </article>
);

const Toggle = ({ title, description, defaultChecked = false }) => (
  <label className="toggle">
    <input type="checkbox" defaultChecked={defaultChecked} />
    <span className="toggle-track" />
    <div className="toggle-content">
      <span className="toggle-title">{title}</span>
      <span className="toggle-description">{description}</span>
    </div>
  </label>
);

const CompactToggle = ({ defaultChecked = false }) => (
  <label className="toggle compact">
    <input type="checkbox" defaultChecked={defaultChecked} />
    <span className="toggle-track" />
  </label>
);

export default function App() {
  const [activeSection, setActiveSection] = useState('workspace');

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">AI</div>
          <div className="brand-meta">
            <span className="brand-name">OpenAI Assistant</span>
            <span className="brand-tag">Admin Console</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          <button className="nav-item active" type="button">
            Settings
          </button>
          <button className="nav-item" type="button">
            Monitoring
          </button>
          <button className="nav-item" type="button">
            Usage
          </button>
          <button className="nav-item" type="button">
            Billing
          </button>
          <button className="nav-item" type="button">
            Documentation
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="workspace">
            <span className="workspace-label">Workspace</span>
            <span className="workspace-name">Product Team</span>
          </div>
          <div className="user">
            <div className="avatar">AK</div>
            <div className="user-meta">
              <span className="user-name">Avery Kim</span>
              <span className="user-role">Owner</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="content">
        <header className="content-header">
          <div>
            <h1>Unified Admin Settings</h1>
            <p>
              Configure every workspace and assistant setting in a single,
              focused surface. The layout mirrors the OpenAI desktop experience
              while surfacing the rich integrations available in Open WebUI.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn ghost" type="button">
              Preview Assistant
            </button>
            <button className="btn primary" type="button">
              Save Changes
            </button>
          </div>
        </header>

        <section className="accordion" id="settings-accordion">
          <AccordionSection
            id="workspace"
            title="Workspace Identity"
            description="Branding, locale, and session defaults for the assistant."
            isActive={activeSection === 'workspace'}
            onActivate={setActiveSection}
          >
            <div className="grid two-column">
              <label className="field">
                <span>Workspace Name</span>
                <input type="text" placeholder="Product AI Workspace" />
              </label>
              <label className="field">
                <span>Default Locale</span>
                <select defaultValue="English (US)">
                  <option>English (US)</option>
                  <option>English (UK)</option>
                  <option>Spanish</option>
                  <option>French</option>
                  <option>German</option>
                </select>
              </label>
            </div>
            <div className="grid two-column">
              <label className="field">
                <span>Theme</span>
                <ChipGroup
                  options={['Auto', 'Dark', 'Light']}
                  defaultSelected="Auto"
                />
              </label>
              <label className="field">
                <span>Time Zone</span>
                <select defaultValue="UTC">
                  <option>UTC</option>
                  <option>America/Los_Angeles</option>
                  <option>America/New_York</option>
                  <option>Europe/Berlin</option>
                  <option>Asia/Singapore</option>
                </select>
              </label>
            </div>
            <Toggle
              title="Allow workspace personalization"
              description="Permit members to override theme and locale settings."
              defaultChecked
            />
          </AccordionSection>

          <AccordionSection
            id="conversations"
            title="Conversation Experience"
            description="Default chat behavior, prompt parameters, and conversation controls inspired by Open WebUI."
            isActive={activeSection === 'conversations'}
            onActivate={setActiveSection}
          >
            <div className="grid two-column">
              <label className="field">
                <span>Primary Model</span>
                <select defaultValue="GPT-4o (OpenAI)">
                  <option>GPT-4o (OpenAI)</option>
                  <option>Claude 3 Opus (Anthropic)</option>
                  <option>Gemini 1.5 Pro (Google)</option>
                  <option>Mistral Large (OpenRouter)</option>
                  <option>Mixtral 8x7B (Local - Ollama)</option>
                </select>
              </label>
              <label className="field">
                <span>Fallback Model</span>
                <select defaultValue="GPT-4o mini">
                  <option>GPT-4o mini</option>
                  <option>Claude 3 Sonnet</option>
                  <option>Gemini 1.5 Flash</option>
                  <option>Mistral Medium</option>
                </select>
              </label>
            </div>
            <div className="grid three-column">
              <label className="field">
                <span>Temperature</span>
                <input type="range" min="0" max="1" step="0.1" defaultValue="0.2" />
              </label>
              <label className="field">
                <span>Top P</span>
                <input type="range" min="0" max="1" step="0.05" defaultValue="0.9" />
              </label>
              <label className="field">
                <span>Max Tokens</span>
                <input type="number" defaultValue="4096" />
              </label>
            </div>
            <Toggle
              title="Enable streaming responses"
              description="Stream assistant messages token by token for faster perceived responses."
              defaultChecked
            />
            <Toggle
              title="Auto-summarize long threads"
              description="Summaries are appended after 50 messages using the fallback model."
            />
          </AccordionSection>

          <AccordionSection
            id="interface"
            title="Interface & Personalization"
            description="UI density, prompt composer options, and markdown controls."
            isActive={activeSection === 'interface'}
            onActivate={setActiveSection}
          >
            <div className="grid two-column">
              <label className="field">
                <span>Composer Layout</span>
                <select defaultValue="Adaptive (OpenAI Desktop)">
                  <option>Adaptive (OpenAI Desktop)</option>
                  <option>Classic (Single Column)</option>
                  <option>Minimal (Edge-to-edge)</option>
                </select>
              </label>
              <label className="field">
                <span>UI Density</span>
                <ChipGroup
                  options={['Comfortable', 'Compact', 'Spacious']}
                  defaultSelected="Comfortable"
                />
              </label>
            </div>
            <Toggle
              title="Render markdown & code blocks"
              description="Apply syntax highlighting and GitHub-flavored markdown."
              defaultChecked
            />
            <Toggle
              title="Enable message reactions"
              description="Allow quick emoji feedback to tune future responses."
              defaultChecked
            />
            <Toggle
              title="Display system prompts inline"
              description="Reveal applied instruction prompts to administrators for each conversation."
            />
          </AccordionSection>

          <AccordionSection
            id="audio"
            title="Audio & Multimodal"
            description="Speech-to-text, text-to-speech, and vision model preferences."
            isActive={activeSection === 'audio'}
            onActivate={setActiveSection}
          >
            <div className="grid three-column">
              <label className="field">
                <span>Speech-to-Text Provider</span>
                <select defaultValue="Whisper API">
                  <option>Whisper API</option>
                  <option>Deepgram Nova-2</option>
                  <option>AssemblyAI Realtime</option>
                  <option>Vosk (Local)</option>
                </select>
              </label>
              <label className="field">
                <span>Text-to-Speech Voice</span>
                <select defaultValue="Alloy">
                  <option>Alloy</option>
                  <option>Nova</option>
                  <option>Verse</option>
                  <option>Aria</option>
                </select>
              </label>
              <label className="field">
                <span>Vision Model</span>
                <select defaultValue="GPT-4o Vision">
                  <option>GPT-4o Vision</option>
                  <option>Gemini Vision</option>
                  <option>llava-1.6 (Local)</option>
                  <option>Claude 3 Opus Vision</option>
                </select>
              </label>
            </div>
            <Toggle
              title="Enable real-time voice chats"
              description="Activates low-latency streaming with 100 ms token cadence."
              defaultChecked
            />
            <Toggle
              title="Auto-transcribe uploads"
              description="Generate transcripts for audio and video attachments."
            />
          </AccordionSection>

          <AccordionSection
            id="integrations"
            title="Model & Tool Integrations"
            description="Connect hosted APIs, local runtimes, and automation hooks from Open WebUI's integrations catalog."
            isActive={activeSection === 'integrations'}
            onActivate={setActiveSection}
          >
            <div className="integration-grid">
              <div className="integration-card">
                <header>
                  <h3>OpenAI Platform</h3>
                  <CompactToggle defaultChecked />
                </header>
                <label className="field">
                  <span>API Key</span>
                  <input type="password" placeholder="sk-••••••••" />
                </label>
                <Toggle
                  title="Enable Realtime API"
                  description="Allow streaming audio sessions via WebRTC."
                  defaultChecked
                />
              </div>
              <div className="integration-card">
                <header>
                  <h3>Ollama (Local)</h3>
                  <CompactToggle defaultChecked />
                </header>
                <label className="field">
                  <span>Endpoint</span>
                  <input type="text" placeholder="http://localhost:11434" />
                </label>
                <label className="field">
                  <span>Default Local Model</span>
                  <select defaultValue="llama3">
                    <option>llama3</option>
                    <option>phi3</option>
                    <option>mistral</option>
                  </select>
                </label>
              </div>
              <div className="integration-card">
                <header>
                  <h3>OpenRouter</h3>
                  <CompactToggle />
                </header>
                <label className="field">
                  <span>API Key</span>
                  <input type="password" placeholder="or-••••••••" />
                </label>
                <label className="field">
                  <span>Preferred Provider</span>
                  <select defaultValue="Mistral">
                    <option>Mistral</option>
                    <option>Anthropic</option>
                    <option>Cohere</option>
                    <option>Google</option>
                  </select>
                </label>
              </div>
              <div className="integration-card">
                <header>
                  <h3>Azure OpenAI</h3>
                  <CompactToggle />
                </header>
                <label className="field">
                  <span>Resource Name</span>
                  <input type="text" placeholder="contoso-openai" />
                </label>
                <label className="field">
                  <span>Deployment</span>
                  <input type="text" placeholder="gpt-4o-production" />
                </label>
              </div>
              <div className="integration-card">
                <header>
                  <h3>Anthropic Claude</h3>
                  <CompactToggle />
                </header>
                <label className="field">
                  <span>API Key</span>
                  <input type="password" placeholder="sk-ant-••••" />
                </label>
                <Toggle
                  title="Use for compliance workflows"
                  description="Restrict to verified users for regulated industries."
                />
              </div>
              <div className="integration-card">
                <header>
                  <h3>Workflow Automations</h3>
                  <CompactToggle defaultChecked />
                </header>
                <label className="field">
                  <span>Webhook URL</span>
                  <input type="url" placeholder="https://hooks.zapier.com/..." />
                </label>
                <label className="field">
                  <span>Event Filters</span>
                  <input type="text" placeholder="conversation.created" />
                </label>
              </div>
            </div>
          </AccordionSection>

          <AccordionSection
            id="knowledge"
            title="Knowledge & Retrieval"
            description="Manage document ingestion, embeddings, and retrieval augmentations."
            isActive={activeSection === 'knowledge'}
            onActivate={setActiveSection}
          >
            <div className="grid two-column">
              <label className="field">
                <span>Vector Store</span>
                <select defaultValue="pgvector (Managed)">
                  <option>pgvector (Managed)</option>
                  <option>Pinecone</option>
                  <option>Milvus</option>
                  <option>Weaviate</option>
                </select>
              </label>
              <label className="field">
                <span>Embedding Model</span>
                <select defaultValue="text-embedding-3-large">
                  <option>text-embedding-3-large</option>
                  <option>nomic-embed-text</option>
                  <option>multilingual-e5-large</option>
                </select>
              </label>
            </div>
            <Toggle
              title="Auto-sync cloud drives"
              description="Pull updates from Google Drive, SharePoint, and Dropbox hourly."
              defaultChecked
            />
            <Toggle
              title="Enable on-demand web search"
              description="Augment responses with live web context via Brave Search."
            />
            <Toggle
              title="Enforce citation requirement"
              description="All retrieval-augmented answers must list source references."
            />
          </AccordionSection>

          <AccordionSection
            id="security"
            title="Access, Security & Compliance"
            description="Role management, logging, and privacy guardrails."
            isActive={activeSection === 'security'}
            onActivate={setActiveSection}
          >
            <div className="grid two-column">
              <label className="field">
                <span>Authentication Provider</span>
                <select defaultValue="OpenAI Accounts">
                  <option>OpenAI Accounts</option>
                  <option>Okta SSO</option>
                  <option>Azure AD</option>
                  <option>Google Workspace</option>
                </select>
              </label>
              <label className="field">
                <span>Session Timeout</span>
                <select defaultValue="30 minutes">
                  <option>30 minutes</option>
                  <option>1 hour</option>
                  <option>4 hours</option>
                  <option>24 hours</option>
                </select>
              </label>
            </div>
            <Toggle
              title="Require multifactor authentication"
              description="Applies to owners, admins, and developers by default."
              defaultChecked
            />
            <Toggle
              title="Anonymize analytics data"
              description="Redact user identifiers before storing interaction logs."
            />
            <Toggle
              title="Export audit trail"
              description="Deliver weekly JSON exports to compliance@company.com."
              defaultChecked
            />
          </AccordionSection>

          <AccordionSection
            id="system"
            title="System & Diagnostics"
            description="Environment metadata, rate limits, and feature flags."
            isActive={activeSection === 'system'}
            onActivate={setActiveSection}
          >
            <div className="grid three-column">
              <label className="field">
                <span>Environment</span>
                <select defaultValue="Production">
                  <option>Production</option>
                  <option>Staging</option>
                  <option>Development</option>
                </select>
              </label>
              <label className="field">
                <span>Max Concurrent Sessions</span>
                <input type="number" defaultValue="250" />
              </label>
              <label className="field">
                <span>Latency Budget (ms)</span>
                <input type="number" defaultValue="1200" />
              </label>
            </div>
            <Toggle
              title="Enable beta features"
              description="Provide administrators with upcoming OpenAI desktop UI experiments."
              defaultChecked
            />
            <Toggle
              title="Email error digests"
              description="Send daily failure summaries to platform@company.com."
            />
          </AccordionSection>
        </section>
      </main>
    </div>
  );
}
