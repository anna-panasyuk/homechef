import { httpServerHandler } from 'cloudflare:node';
import {app} from './app.js';
app.listen(3000);
const api = httpServerHandler({port:3000});
export default {fetch(request,env,ctx) {return new URL(request.url).pathname.startsWith('/api/') ? api.fetch(request,env,ctx) : env.ASSETS.fetch(request);}};
