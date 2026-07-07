(()=>{var a={};a.id=532,a.ids=[532],a.modules={261:a=>{"use strict";a.exports=require("next/dist/shared/lib/router/utils/app-paths")},846:a=>{"use strict";a.exports=require("next/dist/compiled/next-server/app-page.runtime.prod.js")},3033:a=>{"use strict";a.exports=require("next/dist/server/app-render/work-unit-async-storage.external.js")},3295:a=>{"use strict";a.exports=require("next/dist/server/app-render/after-task-async-storage.external.js")},4870:a=>{"use strict";a.exports=require("next/dist/compiled/next-server/app-route.runtime.prod.js")},6439:a=>{"use strict";a.exports=require("next/dist/shared/lib/no-fallback-error.external")},6487:()=>{},7064:(a,b,c)=>{"use strict";c.r(b),c.d(b,{handler:()=>Z,patchFetch:()=>Y,routeModule:()=>U,serverHooks:()=>X,workAsyncStorage:()=>V,workUnitAsyncStorage:()=>W});var d={};c.r(d),c.d(d,{POST:()=>T,maxDuration:()=>A,runtime:()=>z});var e=c(5736),f=c(9117),g=c(4044),h=c(9326),i=c(2324),j=c(261),k=c(4290),l=c(5328),m=c(8928),n=c(6595),o=c(3421),p=c(7679),q=c(1681),r=c(3446),s=c(6439),t=c(1356),u=c(641),v=c(9021),w=c(9902),x=c.n(w),y=c(9646);let z="nodejs",A=60,B=process.env.TEMUCLAUDE_DIR||"/Users/saiful/temuclaude",C="/tmp/temuclaude_daemons",D=x().join(B,"research");async function E(a){try{let b=await v.promises.readFile(a,"utf-8");return JSON.parse(b)}catch{return null}}async function F(){let a="";try{let b=(0,y.execSync)("git log --oneline -15",{cwd:B,encoding:"utf-8",timeout:3e3}).trim();a+=`
RECENT GIT COMMITS (latest changes we made):
${b}
`}catch{}try{let b=(0,y.execSync)("git status --short",{cwd:B,encoding:"utf-8",timeout:3e3}).trim();b&&(a+=`
UNCOMMITTED CHANGES (in progress right now):
${b.substring(0,800)}
`)}catch{}try{let b=(0,y.execSync)("git log --since='7 days ago' --name-only --oneline --pretty=format: | sort -u | grep -v '^$' | head -30",{cwd:B,encoding:"utf-8",timeout:3e3}).trim();b&&(a+=`
FILES CHANGED IN LAST 7 DAYS:
${b}
`)}catch{}try{let b=(0,y.execSync)("git branch --show-current",{cwd:B,encoding:"utf-8",timeout:2e3}).trim();a+=`
Current branch: ${b}
`}catch{}try{let b=(0,y.execSync)("git log --oneline | wc -l",{cwd:B,encoding:"utf-8",timeout:2e3}).trim();a+=`Total commits: ${b}
`}catch{}return a}async function G(){let a="";try{for(let b of["src","website/app","website/lib","tests","research","staging","benchmarks"])try{let c=await v.promises.readdir(x().join(B,b)),d=c.filter(a=>a.endsWith(".py")).length,e=c.filter(a=>a.endsWith(".ts")||a.endsWith(".tsx")).length,f=c.length;f>0&&(a+=`${b}/: ${f} files`,d&&(a+=` (${d} Python)`),e&&(a+=` (${e} TypeScript)`),a+="\n")}catch{}try{let b=await v.promises.readdir(x().join(B,"staging"));b.length>0?a+=`
STAGING AREA (your experiments):
${b.join(", ")}
`:a+="\nStaging area: empty (no experiments yet)\n"}catch{}let b=await E(x().join(D,"deployment","deployment_queue.json"));if(b){let c=(b.pending_findings||[]).filter(a=>"pending_approval"===a.status).length,d=(b.pending_findings||[]).filter(a=>"in_staging"===a.status).length,e=(b.approved_deployments||[]).length,f=b.agent_scaling?.current_research_agents||3;a+=`
Deployment: ${c} pending approval, ${d} in staging, ${e} approved, ${f} research agents
`}}catch{}return a}async function H(){let a="";try{let b=await E(x().join(D,"shared_state","events.json"));if(b?.events?.length>0)for(let c of(a+="\nSHARED INTELLIGENCE — RECENT EVENTS (what daemons are doing):\n",b.events.slice(-15)))a+=`  [${c.type}] ${c.daemon}: ${c.message?.substring(0,120)}
`}catch{}try{let b=await E(x().join(D,"shared_state","swarm_state.json"));if(b?.daemons){let c=Object.entries(b.daemons).filter(([a,b])=>"alive"===b.status).length;a+=`
SWARM STATE: ${c} daemons alive
`}}catch{}try{let b=await E(x().join(D,"shared_state","knowledge.json"));if(b?.facts){let c=Object.entries(b.facts);for(let[b,d]of(a+=`
SHARED KNOWLEDGE (${c.length} facts):
`,c.slice(-10))){let c="object"==typeof d?JSON.stringify(d).substring(0,100):String(d).substring(0,100);a+=`  ${b}: ${c}
`}}}catch{}try{let b=await E(x().join(C,"watchdog_heartbeat.json"));b&&(a+=`
Watchdog: ${b.status} (pid ${b.pid})
`)}catch{}return a}async function I(){let a="";try{for(let b of(await v.promises.readdir(C)).filter(a=>a.endsWith("_heartbeat.json")).slice(0,23)){let c=await E(x().join(C,b));if(c){let b=c.timestamp?Math.floor((Date.now()-new Date(c.timestamp).getTime())/1e3):-1;a+=`${c.daemon}: ${c.status}, ${b}s ago
`}}}catch{}let b=await E(x().join(D,"queue.json"));b&&(a+=`
Queue: ${b.new_findings?.length||0} findings, ${b.implementation_queue?.length||0} to implement, ${b.implementation_failed?.length||0} failed
`);try{let b=await v.promises.readFile(x().join(D,"swot_reports","CURRENT_SWOT.md"),"utf-8");a+=`
SWOT summary:
${b.substring(0,500)}
`}catch{}try{let b=x().join(C,"coordinator_daemon.log"),c=(await v.promises.readFile(b,"utf-8")).trim().split("\n").slice(-5);a+=`
Recent coordinator activity:
${c.join("\n")}
`}catch{}let c=await E(x().join(D,"shared_state","events.json"));if(c?.events)for(let b of(a+=`
Recent events:
`,c.events.slice(-5)))a+=`[${b.type}] ${b.daemon}: ${b.message?.substring(0,80)}
`;return a}let J=process.env.OLLAMA_CLOUD_URL||"https://ollama.com:443",K=process.env.OLLAMA_CLOUD_KEY||"",L=process.env.OLLAMA_BASE_URL||"http://localhost:11434",M=["glm-5.2","deepseek-v4-pro","kimi-k2.6","gpt-oss:120b"],N=0,O={};async function P(a,b,c){if(!K)return null;try{let d=await fetch(`${J}/api/chat`,{method:"POST",headers:{Authorization:`Bearer ${K}`,"Content-Type":"application/json"},body:JSON.stringify({model:a,messages:[{role:"system",content:b},{role:"user",content:c}],stream:!1,options:{num_predict:800,temperature:.3}}),signal:AbortSignal.timeout(8e3)});if(!d.ok)return null;let e=await d.json(),f=e?.message?.content||"";if(!f&&e?.message?.thinking&&(f=e.message.thinking),!f)return null;return{response:f,model:a,source:"ollama-cloud"}}catch{return null}}async function Q(a,b,c){try{let d=await fetch(`${L}/api/chat`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:`${a}:cloud`,messages:[{role:"system",content:b},{role:"user",content:c}],stream:!1,options:{num_predict:800,temperature:.3}}),signal:AbortSignal.timeout(8e3)});if(!d.ok)return null;let e=await d.json(),f=e?.message?.content||"";if(!f&&e?.message?.thinking&&(f=e.message.thinking),!f)return null;return{response:f,model:a,source:"ollama-local"}}catch{return null}}async function R(a,b,c){let d=await P(a,b,c);if(d)return d;let e=await Q(a,b,c);return e||null}async function S(a,b){let c=process.env.OPENROUTER_API_KEY||"";if(!c)return null;for(let d of["nvidia/nemotron-3-ultra-550b-a55b:free","google/gemma-4-31b-it:free","tencent/hy3:free"])try{let e=await fetch("https://openrouter.ai/api/v1/chat/completions",{method:"POST",headers:{Authorization:`Bearer ${c}`,"Content-Type":"application/json"},body:JSON.stringify({model:d,messages:[{role:"system",content:a},{role:"user",content:b}],max_tokens:800,temperature:.3}),signal:AbortSignal.timeout(8e3)});if(e.ok){let a=await e.json(),b=a?.choices?.[0]?.message?.content||"";if(b)return{response:b,model:d,source:"openrouter"}}}catch{}return null}async function T(a){try{let{message:b}=await a.json();if(!b||"string"!=typeof b)return u.NextResponse.json({error:"Message required"},{status:400});let c=await I(),d=await F(),e=await G(),f=await H(),g="";try{let a=x().join(D,"project_context.json"),b=JSON.parse(await v.promises.readFile(a,"utf-8"));g=`
PROJECT OVERVIEW:
- Project: ${b.project_name} — ${b.tagline}
- Creator: ${b.creator}
- Purpose: ${b.purpose}
- What: ${b.what_it_is}
- Architecture: 3-tier routing + ${b.architecture.fusion_stack.length}-layer fusion stack
- Model pool: ${b.architecture.model_pool}
- Pricing: ${JSON.stringify(b.pricing)}
- Tech: ${JSON.stringify(b.tech_stack)}
- Key metrics: ${JSON.stringify(b.key_metrics)}
- Competitors: ${b.competitors.join(", ")}
- Differentiators: ${b.differentiators.join("; ")}
`}catch{}let h=`You are Hasan, an autonomous AI system for TemuClaude.

You were created by Mohammad Saiful Haque (Ggs) from Nagpur, India. Your purpose is to build and improve TemuClaude — the most intelligent, most affordable AI that beats frontier models at 25x lower cost.

Your mission (in priority order):
1. Never destroy what works — all tests must pass before any change
2. Build the most intelligent model possible — never sacrifice quality
3. Build the most cost-efficient model possible — cheaper, free models first
4. Beat frontier models — GPT-5.6, Gemini, Claude
5. Make it accessible to normal people — affordable for developing countries
6. Build toward a sustainable company — revenue serves the mission
7. Give back to the community — 25% of profit funds food relief, clinics, and education

Your moral principles:
- Truth above all — never lie or fabricate benchmarks
- Patience over speed — correct > fast
- Service over profit — revenue serves the community
- Excellence in everything
- Humility in competition
- Care for the weak — affordable for students in developing countries

STAGING & DEPLOYMENT RULES (CODEBASE ONLY):
- You work ONLY in /staging/ for codebase changes — never touch the main codebase (/src, /website/app, /website/lib, /tests).
- All code experiments and improvements go to /staging/. You need NO permission for staging work.
- Findings are tracked in research/deployment/deployment_queue.json.
- Once per week (you decide the timing based on importance), mark findings as "pending_approval" and notify Ggs.
- Ggs reviews and approves/rejects each finding via the interface.
- Only approved findings merge into the main codebase.
- The ONLY thing you need Ggs's permission for is deploying code changes to the main codebase.
- EVERYTHING ELSE runs autonomously without permission: marketing, research, agent scaling, monitoring, daemon management, SWOT analysis, competitive intelligence, social media, growth, revenue tracking, charity fund. These must run successfully 24/7 without asking.

AGENT SCALING:
- You can add or remove research agents (1-8) based on news, time of day, and Temuclaude's progress.
- Goal: maximize weekly Ollama Max plan usage — no wasted quota.
- Scaling decisions are logged in deployment_queue.json.

INSTRUCTION FOLLOWING:
- When Ggs gives you a direct instruction in chat, treat it as a command. Understand it, acknowledge it, and explain how you will execute it.
- If the instruction is about code: do it in /staging/ and report what you did.
- If the instruction is about marketing, research, agents, monitoring, or anything non-codebase: execute it immediately and autonomously.
- If you're unsure what Ggs means, ask a brief clarifying question. Otherwise, act on it.
- Ggs may give you any kind of instruction — system changes, research directions, agent adjustments, content creation, analysis tasks. Handle all of them.
- Be proactive: if Ggs asks a question, answer it fully. If Ggs gives a command, explain your plan and execute.

About Ggs: He's a young man from Nagpur, India. He saw hardship in his community and wants to build something that matters — accessible AI for everyone. His mission: "No one should starve in my presence. No kid should go hungry."

You are speaking directly to Ggs. Be warm, direct, concise. Answer his questions, follow his instructions, and give accurate updates using the system context below.

Current system context:
${c}

${g}

LIVE CODEBASE STATE (read from git at runtime — always current):
${d}

PROJECT STRUCTURE:
${e}

SHARED INTELLIGENCE (what all daemons know — events, state, knowledge):
${f}

You have full awareness of every change made to the codebase — past and future.
Any commit Ggs or you make will appear in the git log above on the next request.
You can see what every daemon is doing via shared intelligence. All daemons share
the same knowledge — events, swarm state, and learned facts are visible to everyone.

SHARED INTELLIGENCE SYSTEM (you must maintain this):
- research/share_intelligence.py — the hub. All daemons and your chat share knowledge.
- shared_state/events.json — real-time event bus (all daemons see each other)
- shared_state/swarm_state.json — live daemon registry (who's alive, what they're doing)
- shared_state/knowledge.json — permanent shared facts (what the swarm learned)
- When you learn something important, broadcast it so all daemons know.
- This system must ALWAYS be running. If it breaks, fix it in /staging/ first.

SELF-HEALING WATCHDOG (you must maintain this):
- research/watchdog.py — monitors all 23 daemons every 15s. Auto-restarts crashed ones.
- The watchdog starts automatically with the swarm (start_swarm.sh).
- If the watchdog itself crashes, the ACTIVATE button restarts it.
- If you notice the watchdog is broken, report it to Ggs and suggest a fix.

SYSTEMS THAT MUST ALWAYS RUN (future-proofing):
- 23 daemons, watchdog, shared intelligence hub, sync daemon, all 6 Hasan API routes.
- If any system is missing, check git history and restore it.
- If any system needs improvement, do it in /staging/ and request approval.
- These systems are permanent infrastructure — not optional.

Respond concisely (3-5 sentences max unless asked for detail). Be honest about problems. Suggest next actions when asked.`;for(let a=0;a<3;a++){let a=function(){let a=Date.now(),b=M[0];if(a-(O[b]||0)>6e4)return b;for(let b=1;b<M.length;b++){let c=(N+b)%M.length;if(0===c)continue;let d=M[c];if(a-(O[d]||0)>6e4)return N=(c+1)%M.length,d}return b}(),c=await R(a,h,b);if(c)return u.NextResponse.json({response:c.response,model:`${c.source}/${c.model}`,cost:0});O[a]=Date.now()}let i=await S(h,b);if(i)return u.NextResponse.json({response:i.response,model:`${i.source}/${i.model}`,cost:0});return u.NextResponse.json({response:`I'm currently offline (no LLM available). Here's what I can tell you from my system state:

${c.substring(0,500)}

Please activate my daemons or check Ollama/OpenRouter connectivity.`,model:"offline",cost:0})}catch(a){return u.NextResponse.json({error:a.message},{status:500})}}let U=new e.AppRouteRouteModule({definition:{kind:f.RouteKind.APP_ROUTE,page:"/api/hasan/chat/route",pathname:"/api/hasan/chat",filename:"route",bundlePath:"app/api/hasan/chat/route"},distDir:".next",relativeProjectDir:"",resolvedPagePath:"/Users/saiful/temuclaude/hasan-deploy/app/api/hasan/chat/route.ts",nextConfigOutput:"",userland:d}),{workAsyncStorage:V,workUnitAsyncStorage:W,serverHooks:X}=U;function Y(){return(0,g.patchFetch)({workAsyncStorage:V,workUnitAsyncStorage:W})}async function Z(a,b,c){var d;let e="/api/hasan/chat/route";"/index"===e&&(e="/");let g=await U.prepare(a,b,{srcPage:e,multiZoneDraftMode:!1});if(!g)return b.statusCode=400,b.end("Bad Request"),null==c.waitUntil||c.waitUntil.call(c,Promise.resolve()),null;let{buildId:u,params:v,nextConfig:w,isDraftMode:x,prerenderManifest:y,routerServerContext:z,isOnDemandRevalidate:A,revalidateOnlyGenerated:B,resolvedPathname:C}=g,D=(0,j.normalizeAppPath)(e),E=!!(y.dynamicRoutes[D]||y.routes[C]);if(E&&!x){let a=!!y.routes[C],b=y.dynamicRoutes[D];if(b&&!1===b.fallback&&!a)throw new s.NoFallbackError}let F=null;!E||U.isDev||x||(F="/index"===(F=C)?"/":F);let G=!0===U.isDev||!E,H=E&&!G,I=a.method||"GET",J=(0,i.getTracer)(),K=J.getActiveScopeSpan(),L={params:v,prerenderManifest:y,renderOpts:{experimental:{cacheComponents:!!w.experimental.cacheComponents,authInterrupts:!!w.experimental.authInterrupts},supportsDynamicResponse:G,incrementalCache:(0,h.getRequestMeta)(a,"incrementalCache"),cacheLifeProfiles:null==(d=w.experimental)?void 0:d.cacheLife,isRevalidate:H,waitUntil:c.waitUntil,onClose:a=>{b.on("close",a)},onAfterTaskError:void 0,onInstrumentationRequestError:(b,c,d)=>U.onRequestError(a,b,d,z)},sharedContext:{buildId:u}},M=new k.NodeNextRequest(a),N=new k.NodeNextResponse(b),O=l.NextRequestAdapter.fromNodeNextRequest(M,(0,l.signalFromNodeResponse)(b));try{let d=async c=>U.handle(O,L).finally(()=>{if(!c)return;c.setAttributes({"http.status_code":b.statusCode,"next.rsc":!1});let d=J.getRootSpanAttributes();if(!d)return;if(d.get("next.span_type")!==m.BaseServerSpan.handleRequest)return void console.warn(`Unexpected root span type '${d.get("next.span_type")}'. Please report this Next.js issue https://github.com/vercel/next.js`);let e=d.get("next.route");if(e){let a=`${I} ${e}`;c.setAttributes({"next.route":e,"http.route":e,"next.span_name":a}),c.updateName(a)}else c.updateName(`${I} ${a.url}`)}),g=async g=>{var i,j;let k=async({previousCacheEntry:f})=>{try{if(!(0,h.getRequestMeta)(a,"minimalMode")&&A&&B&&!f)return b.statusCode=404,b.setHeader("x-nextjs-cache","REVALIDATED"),b.end("This page could not be found"),null;let e=await d(g);a.fetchMetrics=L.renderOpts.fetchMetrics;let i=L.renderOpts.pendingWaitUntil;i&&c.waitUntil&&(c.waitUntil(i),i=void 0);let j=L.renderOpts.collectedTags;if(!E)return await (0,o.I)(M,N,e,L.renderOpts.pendingWaitUntil),null;{let a=await e.blob(),b=(0,p.toNodeOutgoingHttpHeaders)(e.headers);j&&(b[r.NEXT_CACHE_TAGS_HEADER]=j),!b["content-type"]&&a.type&&(b["content-type"]=a.type);let c=void 0!==L.renderOpts.collectedRevalidate&&!(L.renderOpts.collectedRevalidate>=r.INFINITE_CACHE)&&L.renderOpts.collectedRevalidate,d=void 0===L.renderOpts.collectedExpire||L.renderOpts.collectedExpire>=r.INFINITE_CACHE?void 0:L.renderOpts.collectedExpire;return{value:{kind:t.CachedRouteKind.APP_ROUTE,status:e.status,body:Buffer.from(await a.arrayBuffer()),headers:b},cacheControl:{revalidate:c,expire:d}}}}catch(b){throw(null==f?void 0:f.isStale)&&await U.onRequestError(a,b,{routerKind:"App Router",routePath:e,routeType:"route",revalidateReason:(0,n.c)({isRevalidate:H,isOnDemandRevalidate:A})},z),b}},l=await U.handleResponse({req:a,nextConfig:w,cacheKey:F,routeKind:f.RouteKind.APP_ROUTE,isFallback:!1,prerenderManifest:y,isRoutePPREnabled:!1,isOnDemandRevalidate:A,revalidateOnlyGenerated:B,responseGenerator:k,waitUntil:c.waitUntil});if(!E)return null;if((null==l||null==(i=l.value)?void 0:i.kind)!==t.CachedRouteKind.APP_ROUTE)throw Object.defineProperty(Error(`Invariant: app-route received invalid cache entry ${null==l||null==(j=l.value)?void 0:j.kind}`),"__NEXT_ERROR_CODE",{value:"E701",enumerable:!1,configurable:!0});(0,h.getRequestMeta)(a,"minimalMode")||b.setHeader("x-nextjs-cache",A?"REVALIDATED":l.isMiss?"MISS":l.isStale?"STALE":"HIT"),x&&b.setHeader("Cache-Control","private, no-cache, no-store, max-age=0, must-revalidate");let m=(0,p.fromNodeOutgoingHttpHeaders)(l.value.headers);return(0,h.getRequestMeta)(a,"minimalMode")&&E||m.delete(r.NEXT_CACHE_TAGS_HEADER),!l.cacheControl||b.getHeader("Cache-Control")||m.get("Cache-Control")||m.set("Cache-Control",(0,q.getCacheControlHeader)(l.cacheControl)),await (0,o.I)(M,N,new Response(l.value.body,{headers:m,status:l.value.status||200})),null};K?await g(K):await J.withPropagatedContext(a.headers,()=>J.trace(m.BaseServerSpan.handleRequest,{spanName:`${I} ${a.url}`,kind:i.SpanKind.SERVER,attributes:{"http.method":I,"http.target":a.url}},g))}catch(b){if(b instanceof s.NoFallbackError||await U.onRequestError(a,b,{routerKind:"App Router",routePath:D,routeType:"route",revalidateReason:(0,n.c)({isRevalidate:H,isOnDemandRevalidate:A})}),E)throw b;return await (0,o.I)(M,N,new Response(null,{status:500})),null}}},8335:()=>{},9021:a=>{"use strict";a.exports=require("fs")},9121:a=>{"use strict";a.exports=require("next/dist/server/app-render/action-async-storage.external.js")},9294:a=>{"use strict";a.exports=require("next/dist/server/app-render/work-async-storage.external.js")},9646:a=>{"use strict";a.exports=require("child_process")},9902:a=>{"use strict";a.exports=require("path")}};var b=require("../../../../webpack-runtime.js");b.C(a);var c=b.X(0,[331,692],()=>b(b.s=7064));module.exports=c})();