module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
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
}
