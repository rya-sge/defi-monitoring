import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist', 'node_modules'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommendedTypeChecked,
      reactHooks.configs['recommended-latest'],
      reactRefresh.configs.vite,
      prettier,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
      parserOptions: {
        project: ['./tsconfig.app.json', './tsconfig.node.json'],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
  {
    // Vendored shadcn/ui primitives. They are generated, not authored here, and
    // they export variant objects next to their component, which the Fast
    // Refresh rule forbids in our own files for good reason. Narrow override
    // rather than weakening the rule everywhere.
    files: ['src/components/ui/**/*.tsx'],
    // Stock shadcn: SidebarMenuSkeleton picks a random width once, in a useMemo, which the
    // React Compiler purity rule flags. Vendored code, left as shipped.
    rules: { 'react-refresh/only-export-components': 'off', 'react-hooks/purity': 'off' },
  },
);
