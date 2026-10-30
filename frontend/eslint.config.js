import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: { globals: globals.browser },
    plugins: { 'react-refresh': reactRefresh },
    rules: {
      'react-refresh/only-export-components': [
        'warn',
        {
          allowConstantExport: true,
          // A hook or helper that belongs to the component next to it (context + useAuth, trail + usePageTrail)
          allowExportNames: ['useAuth', 'usePageTrail', 'buttonClassName'],
        },
      ],
    },
  },
  {
    // The site only; the Playwright tests in e2e/ have a fixture argument called `use`, which is not a React hook
    files: ['src/**/*.{ts,tsx}'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      // The same two hook rules as before the upgrade. The plugin's newer "recommended" set adds
      // React Compiler rules that this code base was not written for.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
)
