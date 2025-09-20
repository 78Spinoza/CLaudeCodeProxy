<template>
  <div class="container">
    <!-- Logo Header -->
    <div class="logo-container">
      <div class="logo-svg" v-html="logoSvg"></div>
      <h1 class="installer-title">Smart Installer</h1>
    </div>

    <div v-if="currentStep === 'welcome'" class="welcome-screen">
      <div class="welcome-header">
        <h2>🚀 Welcome to the Smart Installer!</h2>
        <p class="tagline">Get <strong>15x cheaper</strong> Claude Code performance in minutes</p>
      </div>

      <!-- Button moved right below the header -->
      <div class="installation-cta">
        <button @click="startInstallation" :disabled="installing" class="install-button">
          {{ installing ? '⏳ Installing...' : '🚀 Start Smart Installation' }}
        </button>
        <p class="install-subtitle">One click • No manual steps • Professional experience</p>
      </div>

      <!-- Compact features list -->
      <div class="features-list">
        <div class="feature-item-compact">
          🔍 <strong>Smart Detection</strong> - Finds existing Python, Node.js & Git
        </div>
        <div class="feature-item-compact">
          📥 <strong>Download-on-Demand</strong> - Only missing dependencies (~15MB vs 400MB)
        </div>
        <div class="feature-item-compact">
          ⚙️ <strong>Auto-Configuration</strong> - Sets up Claude Code, API keys & shortcuts
        </div>
        <div class="feature-item-compact">
          ⚡ <strong>Ready in Minutes</strong> - From download to running: 5-10 minutes total
        </div>
      </div>
    </div>

    <div v-if="currentStep === 'installing'" class="installation-screen">
      <div class="progress-container">
        <div class="progress-bar" :style="{width: progress + '%'}"></div>
      </div>
      <p><strong>{{ currentMessage }}</strong></p>

      <!-- Real-time log messages -->
      <div class="log-messages" style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 15px 0; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 13px;">
        <div v-for="(log, index) in logMessages" :key="index" :style="{color: log.type === 'error' ? 'red' : log.type === 'success' ? 'green' : 'black'}">
          {{ log.message }}
        </div>
      </div>

      <div class="step-list">
        <div
          v-for="step in installationSteps"
          :key="step.id"
          :class="['step', step.status]"
        >
          <strong>{{ step.name }}</strong>
          <div v-if="step.details">{{ step.details }}</div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div style="margin-top: 30px; text-align: center;">
        <!-- Show "Proceed with Installation" after detection is complete -->
        <div v-if="detectionResults && !installing">
          <button @click="proceedWithInstallation" class="install-button" style="margin-bottom: 15px;">
            🚀 Proceed with Installation
          </button>
          <br>
          <button @click="skipToConfiguration" class="skip-button">
            ⏭️ Skip Installation & Go to API Keys
          </button>
          <p style="font-size: 14px; color: #666; margin-top: 8px;">
            Review the detection results below, then proceed or skip
          </p>
        </div>

        <!-- Show skip button during/before detection -->
        <div v-else>
          <button @click="skipToConfiguration" :disabled="installing" class="skip-button">
            ⏭️ Skip Installation & Go to API Keys
          </button>
          <p style="font-size: 14px; color: #666; margin-top: 8px;">
            If you already have Python, Node.js, Git & Claude Code installed
          </p>
        </div>
      </div>
    </div>

    <div v-if="currentStep === 'configuration'" class="config-screen">
      <h2>🔑 API Configuration - Get 15-20x Cheaper Claude Access!</h2>
      <p style="margin-bottom: 25px; font-size: 16px;">Choose your preferred provider(s) for massive cost savings:</p>

      <!-- Setup Instructions -->
      <div style="margin: 25px 0; padding: 20px; background: #f0f9ff; border: 2px solid #0ea5e9; border-radius: 10px;">
        <h3 style="margin: 0 0 15px 0; color: #0c4a6e;">📋 Quick Setup Guide</h3>
        <ol style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6;">
          <li><strong>Choose at least one provider below</strong> (GroqCloud recommended for tools support)</li>
          <li><strong>Create an account</strong> on the provider's website</li>
          <li><strong>Generate an API key</strong> in their dashboard</li>
          <li><strong>⚠️ CRITICAL: Set spending limits</strong> in the billing section (start with $5-10)</li>
          <li><strong>Enter the API key</strong> in the field below</li>
          <li><strong>Click "Finish Installation"</strong> to save your configuration</li>
        </ol>
        <div style="margin-top: 15px; padding: 12px; background: #fef3c7; border-radius: 6px; border: 1px solid #f59e0b;">
          <strong style="color: #92400e;">💡 Pro Tip:</strong> Start with GroqCloud for full Claude Code tools support, then add xAI for maximum speed and savings!
        </div>
      </div>

      <!-- GroqCloud Setup (MOVED TO FIRST) -->
      <div class="provider-section" style="margin: 25px 0; padding: 20px; border: 2px solid #7c3aed; border-radius: 10px; background: #faf9ff;">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
          <h3 style="margin: 0; color: #7c3aed;">⚡ GroqCloud - 20x Cheaper + Tools</h3>
          <span style="margin-left: 10px; padding: 3px 8px; background: #f59e0b; color: white; border-radius: 12px; font-size: 12px;">$0.15/$0.75 per 1M tokens</span>
        </div>

        <div style="margin: 10px 0; padding: 15px; background: #ffffff; border-radius: 5px; border: 1px solid #e5e7eb;">
          <p style="margin: 0 0 10px 0; font-weight: bold;">📋 Setup Steps:</p>
          <ol style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
            <li>Visit: <a href="#" @click.prevent="openExternal('https://console.groq.com')" style="color: #0066cc; text-decoration: underline;">https://console.groq.com</a></li>
            <li>Create API key in 'API Keys' section</li>
            <li>⚠️ <strong>IMPORTANT:</strong> Set spending limits in 'Billing' section!</li>
          </ol>
          <p style="margin: 10px 0 0 0; font-size: 13px; color: #059669;">
            ✨ <strong>Bonus Features:</strong> Web search, code execution tools included!
          </p>
        </div>

        <div style="margin-top: 15px;">
          <label style="font-weight: bold;">GroqCloud API Key (optional):</label>
          <div v-if="existingKeys.has_groq" style="margin: 8px 0; padding: 10px; background: #f0fdf4; border: 1px solid #22c55e; border-radius: 4px; font-size: 14px;">
            ✅ <strong>Current key found:</strong> {{ existingKeys.groq_key }}
            <div style="margin-top: 5px;">
              <label style="font-size: 13px;">
                <input type="radio" :value="false" v-model="replaceGroqKey" style="margin-right: 5px;" /> Keep current key
              </label>
              <label style="font-size: 13px; margin-left: 15px;">
                <input type="radio" :value="true" v-model="replaceGroqKey" style="margin-right: 5px;" /> Replace with new key
              </label>
            </div>
          </div>
          <input
            v-model="config.groqKey"
            type="password"
            :placeholder="existingKeys.has_groq && !replaceGroqKey ? '(keeping current key)' : 'gsk_abc123def456...'"
            :disabled="existingKeys.has_groq && !replaceGroqKey"
            style="width: 100%; max-width: 400px; margin-top: 8px; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;"
          />
        </div>
      </div>

      <!-- xAI Grok Setup -->
      <div class="provider-section" style="margin: 25px 0; padding: 20px; border: 2px solid #1e40af; border-radius: 10px; background: #f8faff;">
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
          <h3 style="margin: 0; color: #1e40af;">🚀 xAI Grok - 15x Cheaper</h3>
          <span style="margin-left: 10px; padding: 3px 8px; background: #22c55e; color: white; border-radius: 12px; font-size: 12px;">$0.20/$1.50 per 1M tokens</span>
        </div>

        <div style="margin: 10px 0; padding: 15px; background: #ffffff; border-radius: 5px; border: 1px solid #e5e7eb;">
          <p style="margin: 0 0 10px 0; font-weight: bold;">📋 Setup Steps:</p>
          <ol style="margin: 5px 0; padding-left: 20px; font-size: 14px;">
            <li>Visit: <a href="#" @click.prevent="openExternal('https://console.x.ai')" style="color: #0066cc; text-decoration: underline;">https://console.x.ai</a></li>
            <li>Create API key in 'API Keys' section</li>
            <li>⚠️ <strong>IMPORTANT:</strong> Set spending limits in 'Billing' section!</li>
          </ol>
          <p style="margin: 10px 0 0 0; font-size: 13px; color: #059669;">
            ✨ <strong>Bonus Features:</strong> Web search, code execution tools included!
          </p>
        </div>

        <div style="margin-top: 15px;">
          <label style="font-weight: bold;">GroqCloud API Key (optional):</label>
          <div v-if="existingKeys.has_groq" style="margin: 8px 0; padding: 10px; background: #f0fdf4; border: 1px solid #22c55e; border-radius: 4px; font-size: 14px;">
            ✅ <strong>Current key found:</strong> {{ existingKeys.groq_key }}
            <div style="margin-top: 5px;">
              <label style="font-size: 13px;">
                <input type="radio" :value="false" v-model="replaceGroqKey" style="margin-right: 5px;" /> Keep current key
              </label>
              <label style="font-size: 13px; margin-left: 15px;">
                <input type="radio" :value="true" v-model="replaceGroqKey" style="margin-right: 5px;" /> Replace with new key
              </label>
            </div>
          </div>
          <input
            v-model="config.groqKey"
            type="password"
            :placeholder="existingKeys.has_groq && !replaceGroqKey ? '(keeping current key)' : 'gsk_abc123def456...'"
            :disabled="existingKeys.has_groq && !replaceGroqKey"
            style="width: 100%; max-width: 400px; margin-top: 8px; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;"
          />
        </div>
      </div>

      <!-- Cost Comparison & Tips -->
      <div style="margin: 25px 0; padding: 15px; background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border-radius: 8px; border: 1px solid #10b981;">
        <h4 style="margin: 0 0 10px 0; color: #065f46;">💰 Cost Comparison (vs Claude Sonnet Direct)</h4>
        <div style="display: flex; justify-content: space-around; text-align: center;">
          <div>
            <div style="font-size: 20px; font-weight: bold; color: #dc2626;">Anthropic Direct</div>
            <div style="font-size: 14px;">$3.00/$15.00 per 1M tokens</div>
          </div>
          <div style="font-size: 24px; color: #059669;">→</div>
          <div>
            <div style="font-size: 20px; font-weight: bold; color: #059669;">With Proxy</div>
            <div style="font-size: 14px;">$0.15-$0.20 per 1M tokens</div>
          </div>
        </div>
      </div>

      <!-- Important Notes -->
      <div style="margin: 20px 0; padding: 15px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px;">
        <p style="margin: 0 0 10px 0; font-weight: bold; color: #92400e;">⚠️ Important Security Notes:</p>
        <ul style="margin: 5px 0; padding-left: 20px; font-size: 14px; color: #92400e;">
          <li><strong>Set spending limits</strong> in both provider dashboards before use</li>
          <li><strong>Both keys are optional</strong> - you can configure them later</li>
          <li><strong>Keys are stored securely</strong> in your user environment variables</li>
          <li><strong>Start with small limits</strong> to test before scaling up</li>
        </ul>
      </div>

      <button @click="finishInstallation" :disabled="saving">
        {{ saving ? 'Saving...' : 'Finish Installation' }}
      </button>
    </div>

    <div v-if="currentStep === 'completed'" class="completed-screen">
      <h2>🎉 Claude Code Proxy Successfully Installed!</h2>
      <p style="font-size: 18px; margin-bottom: 25px;">Ready to enjoy 15-20x cheaper Claude Code access!</p>

      <!-- Quick Start -->
      <div style="margin: 25px 0; padding: 20px; background: #f0fdf4; border: 2px solid #10b981; border-radius: 10px;">
        <h3 style="margin: 0 0 15px 0; color: #065f46;">🚀 Quick Start (2 steps):</h3>

        <div style="margin: 15px 0;">
          <strong style="color: #065f46;">Step 1:</strong> Start a proxy server
          <div style="margin: 8px 0; padding: 10px; background: white; border-radius: 5px; font-family: monospace; border: 1px solid #d1d5db;">
            <button @click="launchProxy" style="margin-right: 10px; padding: 8px 12px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;">Launch Claude Proxy</button>
            <span style="font-size: 14px; color: #666;">or manually: Open cmd and run <code>claudeproxy</code> from your project folder</span>
          </div>
        </div>

        <div style="margin: 15px 0;">
          <strong style="color: #065f46;">Step 2:</strong> Use Claude Code with proxy
          <div style="margin: 8px 0; padding: 10px; background: white; border-radius: 5px; font-family: monospace; font-size: 11px; border: 1px solid #d1d5db; overflow-x: auto;">
            # Basic usage
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5000", "ANTHROPIC_API_KEY": "dummy_key"}}' -p "Your prompt here"

            # With all tools (plan mode)
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5000", "ANTHROPIC_API_KEY": "dummy_key"}}' --permission-mode plan
          </div>
        </div>
      </div>

      <!-- Provider Options -->
      <div style="margin: 25px 0; padding: 20px; background: #faf5ff; border: 2px solid #7c3aed; border-radius: 10px;">
        <h3 style="margin: 0 0 15px 0; color: #581c87;">🔀 Provider Options:</h3>

        <div style="display: flex; gap: 20px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 200px;">
            <strong style="color: #1e40af;">xAI Grok (Port 5000)</strong>
            <div style="font-size: 13px; margin: 5px 0;">15x cheaper • Fast responses</div>
            <code style="font-size: 11px; background: white; padding: 2px 4px; border-radius: 3px;">ANTHROPIC_BASE_URL: http://localhost:5000</code>
          </div>

          <div style="flex: 1; min-width: 200px;">
            <strong style="color: #7c3aed;">GroqCloud (Port 5001)</strong>
            <div style="font-size: 13px; margin: 5px 0;">20x cheaper • Web search • Code tools</div>
            <code style="font-size: 11px; background: white; padding: 2px 4px; border-radius: 3px;">ANTHROPIC_BASE_URL: http://localhost:5001</code>
          </div>
        </div>
      </div>

      <!-- Detailed Usage Guide -->
      <div style="margin: 25px 0; padding: 20px; background: #f8fafc; border: 2px solid #334155; border-radius: 10px;">
        <h3 style="margin: 0 0 15px 0; color: #334155;">📖 Complete Usage Guide</h3>

        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; color: #475569;">🎯 Quick Commands:</h4>
          <div style="background: white; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 10px; border: 1px solid #d1d5db; overflow-x: auto;">
            # xAI Grok (Fast & Cheap)
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5000", "ANTHROPIC_API_KEY": "dummy_key"}}' -p "Hello"

            # GroqCloud (Tools & Web Search)
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5001", "ANTHROPIC_API_KEY": "dummy_key"}}' --permission-mode plan

            # Enhanced GroqCloud (All Tools Working)
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5003", "ANTHROPIC_API_KEY": "dummy_key"}}' --permission-mode plan
          </div>
        </div>

        <div style="margin-bottom: 20px;">
          <h4 style="margin: 0 0 8px 0; color: #475569;">🛠️ Development Workflow:</h4>
          <div style="background: white; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 10px; border: 1px solid #d1d5db; overflow-x: auto;">
            # Step 1: Open cmd, go to your project folder and start proxy
            cd C:\MyProject
            claudeproxy

            # Step 2: Use Claude Code in another terminal (full tools)
            claude --settings '{"env": {"ANTHROPIC_BASE_URL": "http://localhost:5003", "ANTHROPIC_API_KEY": "dummy_key"}}' --permission-mode plan

            # Step 3: Enjoy 20x cheaper Claude Code with all features!
          </div>
        </div>

        <div>
          <h4 style="margin: 0 0 8px 0; color: #475569;">⚠️ Important Notes:</h4>
          <ul style="margin: 5px 0; padding-left: 20px; font-size: 13px; color: #475569;">
            <li><strong>Port 5003</strong> = GroqCloud Enhanced (ALL Claude Code tools working)</li>
            <li><strong>Port 5001</strong> = GroqCloud Basic (limited tools)</li>
            <li><strong>Port 5000</strong> = xAI Grok (fastest, cheapest)</li>
            <li><strong>Always run proxy first</strong>, then use Claude Code commands</li>
            <li><strong>Check provider dashboards</strong> for usage and costs</li>
          </ul>
        </div>
      </div>

      <!-- Cost Savings -->
      <div style="margin: 25px 0; padding: 15px; background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%); border-radius: 8px; border: 1px solid #22c55e;">
        <h4 style="margin: 0 0 10px 0; color: #065f46;">💰 Your Savings:</h4>
        <div style="text-align: center;">
          <div style="font-size: 18px; color: #dc2626;">Before: <strike>$3.00-$15.00</strike> per 1M tokens</div>
          <div style="font-size: 20px; font-weight: bold; color: #059669; margin: 8px 0;">Now: $0.15-$0.20 per 1M tokens</div>
          <div style="font-size: 16px; color: #065f46;">💸 <strong>Savings: 15-20x less cost!</strong></div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div style="margin: 25px 0;">
        <button @click="launchProxy" style="padding: 12px 20px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 0 10px;">🚀 Launch Claude Proxy</button>
        <button @click="openInstallFolder" style="padding: 12px 20px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin: 0 10px;">📁 Open Install Folder</button>
      </div>

      <!-- Advanced Users Note -->
      <div style="margin: 20px 0; padding: 10px; background: #f3f4f6; border-radius: 5px; font-size: 13px; color: #374151;">
        <strong>For Advanced Users:</strong> Use <code>python claudeproxysetup.py</code> for command-line configuration, or modify proxy scripts directly in the install folder.
      </div>
    </div>

    <div v-if="error" class="error-message" style="color: red; margin-top: 20px;">
      <strong>Error:</strong> {{ error }}
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import logoSvgContent from './logo.svg?raw'

export default {
  name: 'App',
  setup() {
    const currentStep = ref('welcome')
    const installing = ref(false)
    const saving = ref(false)
    const progress = ref(0)
    const currentMessage = ref('')
    const error = ref('')
    const installPath = ref('')
    const detectionResults = ref(null)
    const autoProceeding = ref(false)

    const config = ref({
      xaiKey: '',
      groqKey: ''
    })

    const existingKeys = ref({
      xai_key: '',
      groq_key: '',
      has_xai: false,
      has_groq: false
    })

    const replaceXaiKey = ref(false)
    const replaceGroqKey = ref(false)
    const logMessages = ref([])

    const installationSteps = ref([
      { id: 'detect', name: 'Detecting System Dependencies', status: 'pending', details: '' },
      { id: 'python', name: 'Python 3.8+', status: 'pending', details: '' },
      { id: 'nodejs', name: 'Node.js', status: 'pending', details: '' },
      { id: 'git', name: 'Git', status: 'pending', details: '' },
      { id: 'claude', name: 'Claude Code CLI', status: 'pending', details: '' },
      { id: 'proxy', name: 'Proxy Scripts', status: 'pending', details: '' },
      { id: 'shortcuts', name: 'Desktop Shortcuts', status: 'pending', details: '' }
    ])

    const addLogMessage = (message, type = 'info') => {
      const timestamp = new Date().toLocaleTimeString()
      logMessages.value.push({
        message: `[${timestamp}] ${message}`,
        type: type
      })
      // Keep only last 50 messages to prevent memory issues
      if (logMessages.value.length > 50) {
        logMessages.value.shift()
      }
    }

    const updateStep = (stepId, status, details = '') => {
      const step = installationSteps.value.find(s => s.id === stepId)
      if (step) {
        step.status = status
        step.details = details
        console.log(`Updated step ${stepId}: ${status} - ${details}`)

        // Add visible log message
        const statusEmoji = status === 'completed' ? '✓' : status === 'active' ? '⏳' : '○'
        addLogMessage(`${statusEmoji} ${step.name}: ${details || status}`, status === 'completed' ? 'success' : 'info')

        // Force Vue reactivity
        installationSteps.value = [...installationSteps.value]
      } else {
        console.log(`Step not found: ${stepId}`)
        addLogMessage(`⚠ Unknown step: ${stepId}`, 'error')
      }
    }

    const skipToConfiguration = async () => {
      // Skip installation and go directly to API key configuration
      currentStep.value = 'configuration'
      installing.value = false

      // Set a default install path for the proxy scripts
      installPath.value = 'C:\\Users\\' + (process.env.USERNAME || 'User') + '\\claude-proxy'

      // Check for existing API keys
      await checkExistingKeys()
    }

    const startInstallation = async () => {
      installing.value = true
      currentStep.value = 'installing'
      error.value = ''

      try {
        // PHASE 1: Detection only
        currentMessage.value = 'Starting dependency detection...'

        // Listen for progress updates
        const unlisten = await listen('installation-progress', (event) => {
          const { step, status, details, progress: prog } = event.payload
          updateStep(step, status, details)
          progress.value = prog
          currentMessage.value = details || `${status} ${step}`
        })

        // Listen for errors
        const errorUnlisten = await listen('installation-error', (event) => {
          error.value = event.payload.message
          installing.value = false
        })

        // Detect dependencies
        detectionResults.value = await invoke('detect_dependencies')

        // Automatically proceed to installation
        addLogMessage('🔄 Detection complete - proceeding to installation...', 'info')
        currentMessage.value = 'Detection complete - starting installation...'

        // Continue directly to installation phase
        await proceedWithInstallation()

      } catch (err) {
        error.value = `Detection failed: ${err}`
        installing.value = false
      }
    }

    const proceedWithInstallation = async () => {
      console.log('=== ENTERING proceedWithInstallation ===')
      addLogMessage('🔧 Starting installation phase...', 'info')

      if (!detectionResults.value) {
        console.log('ERROR: No detection results available')
        addLogMessage('❌ ERROR: No detection results available', 'error')
        error.value = 'No detection results available'
        return
      }

      console.log('Detection results available:', detectionResults.value)
      addLogMessage('✓ Detection results validated', 'success')

      installing.value = true
      error.value = ''
      addLogMessage('🚀 Installation phase activated', 'info')

      try {
        // PHASE 2: Installation with detection results
        currentMessage.value = 'Starting installation process...'

        // Listen for progress updates
        const unlisten = await listen('installation-progress', (event) => {
          const { step, status, details, progress: prog } = event.payload

          console.log('=== PROGRESS EVENT RECEIVED ===')
          console.log(`Step: ${step}`)
          console.log(`Status: ${status}`)
          console.log(`Details: ${details}`)
          console.log(`Progress: ${prog}%`)
          console.log('================================')

          updateStep(step, status, details)
          progress.value = prog
          currentMessage.value = details || `${status} ${step}`

          // User-visible debug info
          if (step === 'proxy') {
            currentMessage.value = `[PROXY] ${status}: ${details || 'Installing proxy scripts...'}`
          } else if (step === 'shortcuts') {
            currentMessage.value = `[SHORTCUTS] ${status}: ${details || 'Creating desktop shortcuts...'}`
          }

          console.log(`UI Updated - Current Message: ${currentMessage.value}`)

          if (status === 'completed' && step === 'shortcuts') {
            console.log('=== INSTALLATION COMPLETE - MOVING TO CONFIGURATION ===')
            addLogMessage('🎉 Installation complete! Moving to configuration...', 'success')

            // Installation complete
            currentStep.value = 'configuration'
            installing.value = false
            progress.value = 100

            console.log('UI state updated - currentStep:', currentStep.value, 'installing:', installing.value)
            addLogMessage('✅ Moved to API key configuration screen', 'success')
          }
        })

        // Listen for errors
        const errorUnlisten = await listen('installation-error', (event) => {
          console.log('=== INSTALLATION ERROR ===')
          console.log(`Error: ${event.payload.message}`)
          console.log('==========================')

          error.value = `[ERROR] ${event.payload.message}`
          currentMessage.value = `Installation failed: ${event.payload.message}`
          installing.value = false
        })

        console.log('=== STARTING INSTALLATION ===')
        console.log('Detection Results:', detectionResults.value)
        console.log('==============================')

        // Add initial log messages
        addLogMessage('🚀 Starting installation process...', 'info')
        addLogMessage('📋 Using detection results from previous scan', 'info')
        addLogMessage('📡 Invoking start_installation command...', 'info')

        console.log('About to call start_installation with:', { detectionResults: detectionResults.value })

        // Start installation with detection results
        await invoke('start_installation', { detectionResults: detectionResults.value })

        console.log('start_installation completed successfully')
        addLogMessage('✅ Installation command completed', 'success')

      } catch (err) {
        console.log('=== INSTALLATION EXCEPTION ===')
        console.log(`Exception: ${err}`)
        console.log('===============================')

        addLogMessage(`💥 EXCEPTION: ${err}`, 'error')
        error.value = `[EXCEPTION] Installation failed: ${err}`
        currentMessage.value = `Critical error: ${err}`
        installing.value = false
      }
    }

    const checkExistingKeys = async () => {
      try {
        const result = await invoke('check_existing_keys')
        existingKeys.value = result

        // Set default radio button values
        replaceXaiKey.value = !result.has_xai
        replaceGroqKey.value = !result.has_groq
      } catch (err) {
        console.error('Failed to check existing keys:', err)
        // Set defaults if check fails
        existingKeys.value = { xai_key: '', groq_key: '', has_xai: false, has_groq: false }
        replaceXaiKey.value = true
        replaceGroqKey.value = true
      }
    }

    const finishInstallation = async () => {
      saving.value = true

      try {
        // Determine which keys to save
        const finalXaiKey = existingKeys.value.has_xai && !replaceXaiKey.value ? 'KEEP_EXISTING' : config.value.xaiKey
        const finalGroqKey = existingKeys.value.has_groq && !replaceGroqKey.value ? 'KEEP_EXISTING' : config.value.groqKey

        const result = await invoke('save_configuration', {
          xaiKey: finalXaiKey,
          groqKey: finalGroqKey
        })

        installPath.value = result.installPath
        currentStep.value = 'completed'
      } catch (err) {
        error.value = `Configuration failed: ${err}`
      }

      saving.value = false
    }

    const launchProxy = async () => {
      try {
        await invoke('launch_proxy')
      } catch (err) {
        error.value = `Failed to launch proxy: ${err}`
      }
    }

    const openInstallFolder = async () => {
      try {
        await invoke('open_install_folder')
      } catch (err) {
        error.value = `Failed to open folder: ${err}`
      }
    }

    const openExternal = async (url) => {
      try {
        await invoke('open_url', { url })
      } catch (err) {
        console.error('Failed to open URL:', err)
        // Fallback: copy URL to show to user
        navigator.clipboard.writeText(url).then(() => {
          alert(`URL copied to clipboard: ${url}`)
        })
      }
    }

    return {
      currentStep,
      installing,
      saving,
      progress,
      currentMessage,
      error,
      installPath,
      detectionResults,
      config,
      existingKeys,
      replaceXaiKey,
      replaceGroqKey,
      installationSteps,
      logMessages,
      logoSvg: logoSvgContent,
      startInstallation,
      proceedWithInstallation,
      skipToConfiguration,
      checkExistingKeys,
      finishInstallation,
      launchProxy,
      openInstallFolder,
      openExternal
    }
  }
}
</script>