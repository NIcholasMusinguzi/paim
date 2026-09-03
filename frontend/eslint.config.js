import js from "@eslint/js";
import importX from "eslint-plugin-import-x";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

const FEATURES = ["farmer", "agent", "officer", "national", "buyer", "auth"];

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended, reactHooks.configs["recommended-latest"]],
    languageOptions: { ecmaVersion: 2022, globals: globals.browser },
    plugins: { "import-x": importX },
    settings: { "import-x/resolver": { typescript: true } },
    rules: {
      // features/* may import design/, api/, realtime/ — never another feature.
      // Cross-feature sharing goes into design/ or api/ (section 3). Zones
      // match resolved paths, so this also catches relative imports.
      "import-x/no-restricted-paths": [
        "error",
        {
          zones: FEATURES.map((feature) => ({
            target: `./src/features/${feature}`,
            from: "./src/features",
            except: [`./${feature}`],
            message: "A feature may not import from another feature. Share via design/, api/, or realtime/ instead.",
          })),
        },
      ],
    },
  },
);
