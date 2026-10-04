import {build} from 'esbuild';
import {mkdir,rm,cp,readFile,writeFile} from 'node:fs/promises';
await rm('dist',{recursive:true,force:true});
await mkdir('dist/client/assets',{recursive:true});
await mkdir('dist/server',{recursive:true});
await mkdir('dist/.openai',{recursive:true});
await build({entryPoints:['frontend/main.jsx'],outfile:'dist/client/assets/app.js',bundle:true,minify:true,format:'esm',platform:'browser',jsx:'automatic',define:{'process.env.NODE_ENV':'"production"'}});
await cp('public','dist/client',{recursive:true});
await cp('frontend/index.html','dist/client/index.html');
for(const [path,title] of [['how-it-works','How it works'],['our-mission','Our mission'],['become-a-cook','Become a cook']]) {await mkdir(`dist/client/${path}`,{recursive:true});const html=(await readFile('frontend/index.html','utf8')).replace(/<title>.*?<\/title>/,`<title>${title} | HomeChef</title>`);await writeFile(`dist/client/${path}/index.html`,html);}
await build({entryPoints:['backend/worker.js'],outfile:'dist/server/index.js',bundle:true,minify:true,format:'esm',platform:'node',target:'es2022',banner:{js:"import { createRequire } from 'node:module'; const require = createRequire('/index.js');"},external:['cloudflare:*','node:*']});
await cp('.openai/hosting.json','dist/.openai/hosting.json');
await writeFile('dist/server/wrangler.json',JSON.stringify({name:'homechef-india',main:'index.js',compatibility_date:'2026-05-01',compatibility_flags:['nodejs_compat','enable_nodejs_http_server_modules'],assets:{directory:'../client',binding:'ASSETS',run_worker_first:['/api/*']}}));
console.log('HomeChef: React frontend and Express API built successfully.');
