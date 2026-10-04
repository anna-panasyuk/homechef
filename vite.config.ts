import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
// Plain Vite build for Lovable. The empty postcss config skips the unused Tailwind starter config.
export default defineConfig({server:{host:'::',port:8080},css:{postcss:{}},plugins:[react()]});
