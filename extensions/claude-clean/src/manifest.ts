import { defineManifest } from '@crxjs/vite-plugin'

export default defineManifest({
  manifest_version: 3,
  name: 'Claude Clean',
  version: '0.1.0',
  description:
    'Clean up Claude-generated text by varying vocabulary and restructuring sentences to change statistical properties.',
  icons: {
    16: 'public/icon16.svg',
    48: 'public/icon48.svg',
    128: 'public/icon128.svg',
  },
  action: {
    default_popup: 'src/popup/index.html',
    default_title: 'Claude Clean',
    default_icon: {
      16: 'public/icon16.svg',
      48: 'public/icon48.svg',
      128: 'public/icon128.svg',
    },
  },
  background: {
    service_worker: 'src/background/service-worker.ts',
    type: 'module',
  },
  content_scripts: [
    {
      matches: ['https://claude.ai/*'],
      js: ['src/content/claude-content.ts'],
      run_at: 'document_end',
    },
  ],
  permissions: ['contextMenus', 'storage', 'activeTab'],
  host_permissions: ['https://claude.ai/*'],
})